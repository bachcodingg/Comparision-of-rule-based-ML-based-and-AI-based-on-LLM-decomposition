#!/usr/bin/env python3
"""
Metric Extractor - Extract code metrics from Java files.
Based on CK Metrics Suite (Chidamber & Kemerer, 1994).
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

import pandas as pd


@dataclass
class JavaMetrics:
    """Extracted Java metrics."""
    file_path: str
    class_name: str
    loc: int
    sloc: int
    blank_lines: int
    comment_lines: int
    wmc: int
    cyclomatic: int
    cognitive: int
    cbo: int
    fan_out: int
    imports: int
    lcom: float
    lcom2: float
    tcc: float
    nom: int
    noa: int
    nop: int
    nopm: int
    dit: int
    
    def to_dict(self) -> Dict:
        return asdict(self)


class MetricExtractor:
    """Extract software metrics from Java files."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
    
    def extract_metrics_from_file(self, file_path: str) -> Optional[JavaMetrics]:
        """Extract all metrics from a Java file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return self._extract(content, file_path)
        except Exception as e:
            self.logger.error(f"Error: {file_path}: {e}")
            return None
    
    def _extract(self, content: str, file_path: str) -> JavaMetrics:
        """Extract metrics from content."""
        lines = content.split('\n')
        loc = len(lines)
        blank_lines = sum(1 for l in lines if not l.strip())
        
        # Comment lines
        comment_lines = len(re.findall(r'//.*$', content, re.MULTILINE))
        comment_lines += len(re.findall(r'/\*.*?\*/', content, re.DOTALL))
        
        sloc = loc - blank_lines - comment_lines
        
        # Class name - look for public class first, then any class declaration
        match = re.search(r'\bpublic\s+(?:abstract\s+)?(?:class|interface)\s+(\w+)', content)
        if not match:
            match = re.search(r'\b(?:class|interface)\s+(\w+)', content)
        class_name = match.group(1) if match else Path(file_path).stem
        
        # Methods
        methods = re.findall(r'(?:public|private|protected|static|\s)*\s+\w+\s+(\w+)\s*\([^)]*\)\s*(?:throws[^{]*)?\{', content)
        nom = len(methods)
        
        # Fields
        fields = re.findall(r'(?:private|protected|public)\s+(?:static\s+)?(?:final\s+)?\w+\s+(\w+)\s*[;=]', content)
        noa = len(fields)
        
        # Complexity - calculate per-method cyclomatic complexity
        # Find method signatures to split into individual methods
        method_sig_pattern = re.compile(
            r'(?:public|private|protected)\s+(?:static\s+)?(?:final\s+)?(?:synchronized\s+)?'
            r'(?:abstract\s+)?[\w<>\[\],\s]+\s+\w+\s*\([^)]*\)\s*(?:throws[\w,\s]+)?\s*\{'
        )
        
        wmc = 0
        method_count = 0
        for match in method_sig_pattern.finditer(content):
            start = match.end()
            depth = 1
            pos = start
            while pos < len(content) and depth > 0:
                if content[pos] == '{':
                    depth += 1
                elif content[pos] == '}':
                    depth -= 1
                pos += 1
            if depth == 0:
                method_body = content[start:pos-1]
                # Count decision points within this method
                method_cc = 1  # Base complexity
                method_cc += len(re.findall(r'\bif\b', method_body))
                method_cc += len(re.findall(r'\bfor\b', method_body))
                method_cc += len(re.findall(r'\bwhile\b', method_body))
                method_cc += len(re.findall(r'\bcase\b', method_body))
                method_cc += len(re.findall(r'\bcatch\b', method_body))
                method_cc += len(re.findall(r'&&|\|\|', method_body))
                wmc += method_cc
                method_count += 1
        
        # Total cyclomatic complexity (file-level) as fallback
        cyclomatic = wmc if wmc > 0 else 1
        cognitive = cyclomatic  # Simplified
        
        # Coupling - count actual type dependencies only
        imports = len(re.findall(r'^import\s+', content, re.MULTILINE))
        
        # Common Java built-in types to EXCLUDE from coupling
        java_builtin_types = {
            'String', 'Integer', 'Long', 'Double', 'Float', 'Boolean', 'Byte',
            'Short', 'Character', 'Object', 'Class', 'Void', 'Number',
            'int', 'long', 'double', 'float', 'boolean', 'byte', 'short', 'char', 'void',
            'List', 'ArrayList', 'LinkedList', 'Map', 'HashMap', 'TreeMap', 'LinkedHashMap',
            'Set', 'HashSet', 'TreeSet', 'LinkedHashSet', 'Collection', 'Collections',
            'Iterator', 'Iterable', 'Optional', 'Stream', 'Collectors',
            'Arrays', 'Math', 'System', 'Runtime',
            'Exception', 'RuntimeException', 'Error', 'Throwable',
            'IllegalArgumentException', 'NullPointerException', 'IOException',
            'IndexOutOfBoundsException', 'UnsupportedOperationException',
            'StringBuilder', 'StringBuffer', 'Comparable', 'Serializable', 'Cloneable',
            'Override', 'Deprecated', 'SuppressWarnings', 'FunctionalInterface',
            'Test', 'Before', 'After', 'Autowired', 'Component', 'Service', 'Repository',
            'Date', 'Calendar', 'LocalDate', 'LocalDateTime', 'Instant',
            'Pattern', 'Matcher', 'Scanner', 'Random',
            'File', 'Path', 'Paths', 'Files',
            'PrintStream', 'InputStream', 'OutputStream', 'Reader', 'Writer',
            'T', 'E', 'K', 'V', 'R', 'U',  # Generic type parameters
        }
        
        coupled_types = set()
        
        # 1. Types from import statements (strongest signal)
        import_types = re.findall(r'^import\s+[\w.]+\.([A-Z]\w*)\s*;', content, re.MULTILINE)
        coupled_types.update(import_types)
        
        # 2. Types in field declarations
        field_types = re.findall(r'(?:private|protected|public)\s+(?:static\s+)?(?:final\s+)?([A-Z]\w*)', content)
        coupled_types.update(field_types)
        
        # 3. Types in method parameters and return types
        param_types = re.findall(r'(?:public|private|protected)\s+(?:static\s+)?([A-Z]\w*)\s+\w+\s*\(', content)
        coupled_types.update(param_types)
        
        # 4. Types in new expressions
        new_types = re.findall(r'new\s+([A-Z]\w*)\s*[\(<]', content)
        coupled_types.update(new_types)
        
        # 5. Types in instanceof checks
        instanceof_types = re.findall(r'instanceof\s+([A-Z]\w*)', content)
        coupled_types.update(instanceof_types)
        
        # Remove built-in types and the class itself
        coupled_types -= java_builtin_types
        coupled_types.discard(class_name)
        
        cbo = len(coupled_types)
        fan_out = cbo
        
        # Cohesion (LCOM) - proper method body extraction using brace depth tracking
        if nom > 1 and noa > 0:
            # Extract method bodies by finding method signatures and tracking braces
            method_signature_pattern = re.compile(
                r'(?:public|private|protected)\s+(?:static\s+)?(?:final\s+)?(?:synchronized\s+)?'
                r'(?:abstract\s+)?[\w<>\[\],\s]+\s+\w+\s*\([^)]*\)\s*(?:throws[\w,\s]+)?\s*\{'
            )
            
            method_bodies = []
            for match in method_signature_pattern.finditer(content):
                start = match.end()  # Position right after the opening {
                depth = 1
                pos = start
                while pos < len(content) and depth > 0:
                    if content[pos] == '{':
                        depth += 1
                    elif content[pos] == '}':
                        depth -= 1
                    pos += 1
                if depth == 0:
                    method_bodies.append(content[start:pos-1])
            
            # Count method pairs sharing fields
            shared = 0
            not_shared = 0
            for i in range(len(method_bodies)):
                for j in range(i+1, len(method_bodies)):
                    common = False
                    for f in fields:
                        if re.search(rf'\b{re.escape(f)}\b', method_bodies[i]) and \
                           re.search(rf'\b{re.escape(f)}\b', method_bodies[j]):
                            common = True
                            break
                    if common:
                        shared += 1
                    else:
                        not_shared += 1
            total = shared + not_shared
            lcom = not_shared / total if total > 0 else 0
        else:
            lcom = 0
        
        lcom2 = lcom
        tcc = 1 - lcom
        
        # Public/private methods
        nop = len(re.findall(r'\bpublic\s+\w+\s+\w+\s*\(', content))
        nopm = len(re.findall(r'\bprivate\s+\w+\s+\w+\s*\(', content))
        
        # Inheritance
        dit = 1 if 'extends' in content else 0
        
        return JavaMetrics(
            file_path=file_path, class_name=class_name,
            loc=loc, sloc=sloc, blank_lines=blank_lines, comment_lines=comment_lines,
            wmc=wmc, cyclomatic=cyclomatic, cognitive=cognitive,
            cbo=cbo, fan_out=fan_out, imports=imports,
            lcom=round(lcom, 4), lcom2=round(lcom2, 4), tcc=round(tcc, 4),
            nom=nom, noa=noa, nop=nop, nopm=nopm, dit=dit
        )
    
    def extract_all_metrics(self, directory: str = None) -> pd.DataFrame:
        """Extract metrics from all Java files in directory."""
        if directory is None:
            directory = self.config.get('data', {}).get('sample_dir', 'data/sample')
        
        directory = Path(directory)
        if not directory.exists():
            self.logger.error(f"Directory not found: {directory}")
            return pd.DataFrame()
        
        metrics_list = []
        for java_file in directory.glob('**/*.java'):
            metrics = self.extract_metrics_from_file(str(java_file))
            if metrics:
                metrics_list.append(metrics.to_dict())
        
        return pd.DataFrame(metrics_list) if metrics_list else pd.DataFrame()
