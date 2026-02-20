#!/usr/bin/env python3
"""
Metric Extractor for Java Code Analysis

Extracts software metrics from Java source files for ML-based code smell detection.
Based on CK Metrics Suite (Chidamber & Kemerer, 1994).

Author: Research Implementation
Version: 1.0
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

import pandas as pd


@dataclass
class JavaMetrics:
    """Data class for Java metrics."""
    file_path: str
    class_name: str
    package_name: str
    
    # Size Metrics
    loc: int
    sloc: int
    blank_lines: int
    comment_lines: int
    
    # Complexity Metrics
    wmc: int
    cyclomatic: int
    cognitive: int
    
    # Coupling Metrics
    cbo: int
    fan_in: int
    fan_out: int
    rfc: int
    
    # Cohesion Metrics
    lcom: float
    lcom2: float
    lcom3: float
    tcc: float
    
    # Structure Metrics
    nom: int
    noa: int
    nop: int
    nopm: int
    dit: int
    noc: int
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_feature_vector(self) -> List[float]:
        """Convert to feature vector for ML."""
        return [
            self.loc, self.sloc, self.wmc, self.cyclomatic,
            self.cbo, self.lcom, self.nom, self.noa,
            self.fan_out, self.rfc, self.tcc, self.dit
        ]
    
    @staticmethod
    def feature_names() -> List[str]:
        return ['loc', 'sloc', 'wmc', 'cyclomatic', 'cbo', 'lcom', 
                'nom', 'noa', 'fan_out', 'rfc', 'tcc', 'dit']


class MetricExtractor:
    """Extract software metrics from Java files."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
    
    def extract_metrics_from_file(self, file_path: str) -> Optional[JavaMetrics]:
        """Extract metrics from a single Java file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return self._extract_metrics(content, file_path)
        except Exception as e:
            self.logger.error(f"Error extracting metrics from {file_path}: {e}")
            return None
    
    def _extract_metrics(self, content: str, file_path: str) -> JavaMetrics:
        """Extract all metrics from Java content."""
        # Remove string literals
        content_clean = re.sub(r'"(?:[^"\\]|\\.)*"', '""', content)
        
        # Basic info
        class_name = self._extract_class_name(content_clean, file_path)
        package_name = self._extract_package(content_clean)
        
        # Size metrics
        loc, sloc, blank_lines, comment_lines = self._calc_size_metrics(content)
        
        # Methods
        methods = self._extract_methods(content_clean)
        fields = self._extract_fields(content_clean)
        
        # Complexity
        wmc = sum(self._calc_method_complexity(m) for m in methods)
        cyclomatic = self._calc_cyclomatic(content_clean)
        cognitive = self._calc_cognitive(content_clean)
        
        # Coupling
        cbo, fan_out = self._calc_coupling(content_clean)
        fan_in = 0
        rfc = len(methods) + self._count_method_calls(content_clean)
        
        # Cohesion
        lcom, lcom2, lcom3 = self._calc_lcom(methods, fields, content_clean)
        tcc = self._calc_tcc(methods, fields, content_clean)
        
        # Structure
        nom = len(methods)
        noa = len(fields)
        nop = len(re.findall(r'\bpublic\s+[\w<>\[\],\s]+\s+\w+\s*\(', content_clean))
        nopm = len(re.findall(r'\bprivate\s+[\w<>\[\],\s]+\s+\w+\s*\(', content_clean))
        dit = len(re.findall(r'\bextends\s+\w+', content_clean))
        noc = len(re.findall(r'\bimplements\s+[\w,\s]+', content_clean))
        
        return JavaMetrics(
            file_path=file_path, class_name=class_name, package_name=package_name,
            loc=loc, sloc=sloc, blank_lines=blank_lines, comment_lines=comment_lines,
            wmc=wmc, cyclomatic=cyclomatic, cognitive=cognitive,
            cbo=cbo, fan_in=fan_in, fan_out=fan_out, rfc=rfc,
            lcom=lcom, lcom2=lcom2, lcom3=lcom3, tcc=tcc,
            nom=nom, noa=noa, nop=nop, nopm=nopm, dit=dit, noc=noc
        )
    
    def _extract_class_name(self, content: str, file_path: str) -> str:
        match = re.search(r'\b(class|interface|enum)\s+(\w+)', content)
        return match.group(2) if match else Path(file_path).stem
    
    def _extract_package(self, content: str) -> str:
        match = re.search(r'^package\s+([\w.]+);', content, re.MULTILINE)
        return match.group(1) if match else ""
    
    def _calc_size_metrics(self, content: str) -> Tuple[int, int, int, int]:
        lines = content.split('\n')
        loc = len(lines)
        blank = sum(1 for l in lines if not l.strip())
        
        comments = 0
        in_block = False
        for line in lines:
            s = line.strip()
            if in_block:
                comments += 1
                if '*/' in s: in_block = False
            elif s.startswith('//'):
                comments += 1
            elif s.startswith('/*'):
                comments += 1
                if '*/' not in s: in_block = True
        
        return loc, loc - blank - comments, blank, comments
    
    def _extract_methods(self, content: str) -> List[str]:
        methods = []
        pattern = re.compile(
            r'(?:public|private|protected|static|final|abstract|synchronized|\s)*'
            r'[\w<>\[\],\s]+\s+(\w+)\s*\([^)]*\)\s*(?:throws[\w,\s]+)?\s*\{'
        )
        for match in pattern.finditer(content):
            start = match.end() - 1
            body = self._extract_block(content, start)
            if body: methods.append(body)
        return methods
    
    def _extract_block(self, content: str, start: int) -> Optional[str]:
        if start >= len(content) or content[start] != '{':
            return None
        depth, end = 0, start
        for i in range(start, len(content)):
            if content[i] == '{': depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    return content[start:i+1]
        return None
    
    def _extract_fields(self, content: str) -> List[str]:
        pattern = re.compile(r'(?:private|protected|public)\s+(?:static\s+)?(?:final\s+)?[\w<>\[\],\s]+\s+(\w+)\s*[;=]')
        return pattern.findall(content)
    
    def _calc_method_complexity(self, method: str) -> int:
        c = 1
        c += len(re.findall(r'\bif\b', method))
        c += len(re.findall(r'\bfor\b', method))
        c += len(re.findall(r'\bwhile\b', method))
        c += len(re.findall(r'\bcase\b', method))
        c += len(re.findall(r'\bcatch\b', method))
        c += len(re.findall(r'\?', method))
        c += len(re.findall(r'&&', method))
        c += len(re.findall(r'\|\|', method))
        return c
    
    def _calc_cyclomatic(self, content: str) -> int:
        c = 1
        for pattern in [r'\bif\b', r'\bfor\b', r'\bwhile\b', r'\bcase\b', 
                       r'\bcatch\b', r'\?', r'&&', r'\|\|']:
            c += len(re.findall(pattern, content))
        return c
    
    def _calc_cognitive(self, content: str) -> int:
        cog, nest = 0, 0
        for line in content.split('\n'):
            s = line.strip()
            if re.search(r'\b(if|for|while|switch|try)\b.*\{', s):
                cog += 1 + nest
                nest += 1
            elif s == '}':
                nest = max(0, nest - 1)
            if '&&' in s or '||' in s: cog += 1
        return cog
    
    def _calc_coupling(self, content: str) -> Tuple[int, int]:
        types = set(re.findall(r'\b([A-Z][a-zA-Z0-9]*)\b', content))
        java_types = {'String', 'Integer', 'Long', 'Double', 'Float', 'Boolean',
                     'Object', 'Class', 'System', 'Exception', 'List', 'Map',
                     'Set', 'ArrayList', 'HashMap', 'HashSet', 'Override'}
        external = types - java_types
        return len(external), len(external)
    
    def _count_method_calls(self, content: str) -> int:
        keywords = {'if', 'for', 'while', 'switch', 'catch', 'return', 'new'}
        calls = re.findall(r'\b(\w+)\s*\(', content)
        return len(set(c for c in calls if c not in keywords))
    
    def _calc_lcom(self, methods: List[str], fields: List[str], content: str) -> Tuple[float, float, float]:
        if not methods or not fields:
            return 0.0, 0.0, 0.0
        
        m, a = len(methods), len(fields)
        access = []
        for method in methods:
            acc = set()
            for f in fields:
                if re.search(r'\b' + re.escape(f) + r'\b', method):
                    acc.add(f)
            access.append(acc)
        
        p, q = 0, 0
        for i in range(m):
            for j in range(i+1, m):
                if access[i] & access[j]: q += 1
                else: p += 1
        
        lcom1 = max(0, p - q) / max(1, p + q) if (p + q) > 0 else 0.0
        sum_ma = sum(sum(1 for acc in access if f in acc) for f in fields)
        lcom2 = 1 - (sum_ma / (m * a)) if (m * a) > 0 else 0.0
        avg_ma = sum_ma / a if a > 0 else 0
        lcom3 = (m - avg_ma) / (m - 1) if m > 1 else 0.0
        
        return round(lcom1, 4), round(lcom2, 4), round(max(0, min(1, lcom3)), 4)
    
    def _calc_tcc(self, methods: List[str], fields: List[str], content: str) -> float:
        m = len(methods)
        if m < 2: return 1.0
        
        access = []
        for method in methods:
            acc = set()
            for f in fields:
                if re.search(r'\b' + re.escape(f) + r'\b', method):
                    acc.add(f)
            access.append(acc)
        
        np = m * (m - 1) // 2
        ndp = sum(1 for i in range(m) for j in range(i+1, m) if access[i] & access[j])
        
        return round(ndp / np, 4) if np > 0 else 1.0
    
    def extract_all_metrics(self, directory: str = None) -> pd.DataFrame:
        """Extract metrics from all Java files."""
        if directory is None:
            directory = self.config.get('data', {}).get('sample_dir', 'data/sample')
        
        directory = Path(directory)
        if not directory.exists():
            self.logger.error(f"Directory not found: {directory}")
            return pd.DataFrame()
        
        metrics_list = []
        for java_file in directory.glob('**/*.java'):
            self.logger.debug(f"Processing: {java_file}")
            metrics = self.extract_metrics_from_file(str(java_file))
            if metrics:
                metrics_list.append(metrics.to_dict())
        
        if not metrics_list:
            return pd.DataFrame()
        
        df = pd.DataFrame(metrics_list)
        self.logger.info(f"Extracted metrics for {len(df)} classes")
        return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    extractor = MetricExtractor()
    df = extractor.extract_all_metrics("data/sample")
    if not df.empty:
        print(df[['class_name', 'loc', 'nom', 'wmc', 'cbo', 'lcom']].to_string())
