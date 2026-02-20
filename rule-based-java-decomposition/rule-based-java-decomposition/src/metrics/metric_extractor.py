#!/usr/bin/env python3
"""
Metric Extractor Module

Extracts software metrics from Java source files for rule-based analysis.

Metrics extracted:
- LOC (Lines of Code)
- NOM (Number of Methods)
- NOF (Number of Fields)
- CC (Cyclomatic Complexity)
- WMC (Weighted Methods per Class)
- CBO (Coupling Between Objects)
- LCOM (Lack of Cohesion of Methods)
- DIT (Depth of Inheritance Tree)
- RFC (Response for a Class)
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class ClassMetrics:
    """Metrics for a single Java class."""
    file_path: str
    class_name: str
    package: str
    repository: str
    
    # Size metrics
    loc: int = 0                 # Lines of Code
    nom: int = 0                 # Number of Methods
    nof: int = 0                 # Number of Fields
    noa: int = 0                 # Number of Attributes
    
    # Complexity metrics
    cc: float = 0.0              # Cyclomatic Complexity (average per method)
    wmc: int = 0                 # Weighted Methods per Class
    
    # Coupling metrics
    cbo: int = 0                 # Coupling Between Objects
    fanin: int = 0               # Fan-in (incoming dependencies)
    fanout: int = 0              # Fan-out (outgoing dependencies)
    
    # Cohesion metrics
    lcom: float = 0.0            # Lack of Cohesion of Methods (0-1)
    
    # Inheritance metrics
    dit: int = 0                 # Depth of Inheritance Tree
    noc: int = 0                 # Number of Children
    
    # Other metrics
    rfc: int = 0                 # Response for a Class
    public_methods: int = 0
    private_methods: int = 0
    protected_methods: int = 0


class MetricExtractor:
    """
    Extracts code metrics from Java source files.
    
    This extractor uses regex-based parsing for simplicity and portability.
    For more accurate metrics, consider using JavaParser or similar AST tools.
    """
    
    # Common Java types to exclude from coupling calculation
    JAVA_BUILTIN_TYPES = {
        'String', 'Integer', 'Long', 'Double', 'Float', 'Boolean', 'Byte',
        'Short', 'Character', 'Object', 'Class', 'Void', 'int', 'long',
        'double', 'float', 'boolean', 'byte', 'short', 'char', 'void',
        'List', 'ArrayList', 'LinkedList', 'Map', 'HashMap', 'TreeMap',
        'Set', 'HashSet', 'TreeSet', 'Collection', 'Iterator', 'Optional',
        'Stream', 'Collectors', 'Arrays', 'Collections', 'Math', 'System',
        'Exception', 'RuntimeException', 'Error', 'Throwable'
    }
    
    def __init__(self, config: dict):
        """
        Initialize the metric extractor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.raw_dir = Path(config["data"]["raw_dir"])
        self.processed_dir = Path(config["data"]["processed_dir"])
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        self.repositories = config["data"]["repositories"]
        
        # Metric settings
        metrics_config = config.get("metrics", {})
        parser_config = metrics_config.get("parser", {})
        
        self.skip_tests = parser_config.get("skip_tests", True)
        self.skip_generated = parser_config.get("skip_generated", True)
        self.encoding = parser_config.get("encoding", "UTF-8")
        
        # Regex patterns
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for parsing Java code."""
        # Class/interface declaration
        self.class_pattern = re.compile(
            r'(?:public\s+)?(?:abstract\s+)?(?:final\s+)?'
            r'(?:class|interface|enum)\s+(\w+)'
            r'(?:\s+extends\s+(\w+))?'
            r'(?:\s+implements\s+([\w,\s]+))?'
        )
        
        # Method declaration
        self.method_pattern = re.compile(
            r'(?:public|private|protected)\s+'
            r'(?:static\s+)?(?:final\s+)?(?:synchronized\s+)?'
            r'(?:abstract\s+)?'
            r'[\w<>\[\],\s]+\s+(\w+)\s*\('
        )
        
        # Field declaration
        self.field_pattern = re.compile(
            r'(?:public|private|protected)\s+'
            r'(?:static\s+)?(?:final\s+)?'
            r'([\w<>\[\]]+)\s+(\w+)\s*[;=]'
        )
        
        # Import statement
        self.import_pattern = re.compile(r'import\s+([\w.]+);')
        
        # Package declaration
        self.package_pattern = re.compile(r'package\s+([\w.]+);')
        
        # Branching statements (for cyclomatic complexity)
        self.branch_pattern = re.compile(
            r'\b(if|else\s+if|for|while|case|catch|&&|\|\||\?)\b'
        )
        
        # Type usage pattern
        self.type_pattern = re.compile(r'\b([A-Z][a-zA-Z0-9]*)\b')
    
    def extract_all_metrics(self) -> pd.DataFrame:
        """
        Extract metrics from all repositories.
        
        Returns:
            DataFrame with metrics for all classes
        """
        all_metrics = []
        
        for repo in self.repositories:
            repo_name = repo["name"]
            repo_path = self.raw_dir / repo_name
            
            if not repo_path.exists():
                logger.warning(f"Repository not found: {repo_path}")
                continue
            
            logger.info(f"Extracting metrics from {repo_name}...")
            repo_metrics = self._extract_from_repository(repo_path, repo_name)
            all_metrics.extend(repo_metrics)
            logger.info(f"Extracted metrics for {len(repo_metrics)} classes")
        
        df = self._metrics_to_dataframe(all_metrics)
        
        # Save to CSV
        output_path = self.processed_dir / "code_metrics.csv"
        df.to_csv(output_path, index=False)
        logger.info(f"Saved metrics to {output_path}")
        
        return df
    
    def _extract_from_repository(self, repo_path: Path, repo_name: str) -> List[ClassMetrics]:
        """Extract metrics from a single repository."""
        metrics_list = []
        
        for java_file in repo_path.rglob("*.java"):
            # Skip test files
            if self.skip_tests and "test" in str(java_file).lower():
                continue
            
            # Skip generated files
            if self.skip_generated:
                if "generated" in str(java_file).lower():
                    continue
                if "target" in java_file.parts:
                    continue
            
            try:
                metrics = self._extract_from_file(java_file, repo_name)
                if metrics:
                    metrics_list.append(metrics)
            except Exception as e:
                logger.debug(f"Error extracting from {java_file}: {e}")
        
        return metrics_list
    
    def extract_metrics_from_file(self, file_path) -> Dict:
        """
        Extract metrics from a single Java file (public API).
        
        Args:
            file_path: Path to Java file (str or Path object)
            
        Returns:
            Dictionary with metric values for use in priority scoring
        """
        file_path = Path(file_path)
        
        try:
            content = file_path.read_text(encoding=self.encoding, errors="ignore")
        except Exception as e:
            logger.error(f"Cannot read {file_path}: {e}")
            return {}
        
        # Extract basic info
        class_match = self.class_pattern.search(content)
        if not class_match:
            logger.warning(f"No class found in {file_path}")
            return {}
        
        class_name = class_match.group(1)
        parent_class = class_match.group(2)
        
        # Extract package
        package_match = self.package_pattern.search(content)
        package = package_match.group(1) if package_match else ""
        
        # Calculate metrics
        loc = self._calculate_loc(content)
        nom, public_methods, private_methods, protected_methods = self._count_methods(content)
        nof, noa = self._count_fields(content)
        cc, wmc = self._calculate_complexity(content)
        cbo, fanout = self._calculate_coupling(content)
        lcom = self._calculate_lcom(content)
        dit = self._calculate_dit(parent_class)
        rfc = self._calculate_rfc(content, nom)
        
        return {
            'file_path': str(file_path),
            'class_name': class_name,
            'package': package,
            'loc': loc,
            'nom': nom,
            'nof': nof,
            'noa': noa,
            'cc': cc,
            'wmc': wmc,
            'cbo': cbo,
            'fanout': fanout,
            'lcom': lcom,
            'dit': dit,
            'rfc': rfc,
            'public_methods': public_methods,
            'private_methods': private_methods,
            'protected_methods': protected_methods
        }

    def _extract_from_file(self, file_path: Path, repo_name: str) -> Optional[ClassMetrics]:
        """Extract metrics from a single Java file."""
        try:
            content = file_path.read_text(encoding=self.encoding, errors="ignore")
        except Exception as e:
            logger.debug(f"Cannot read {file_path}: {e}")
            return None
        
        # Extract basic info
        class_match = self.class_pattern.search(content)
        if not class_match:
            return None
        
        class_name = class_match.group(1)
        parent_class = class_match.group(2)
        
        # Extract package
        package_match = self.package_pattern.search(content)
        package = package_match.group(1) if package_match else ""
        
        metrics = ClassMetrics(
            file_path=str(file_path),
            class_name=class_name,
            package=package,
            repository=repo_name
        )
        
        # Calculate metrics
        metrics.loc = self._calculate_loc(content)
        metrics.nom, metrics.public_methods, metrics.private_methods, metrics.protected_methods = self._count_methods(content)
        metrics.nof, metrics.noa = self._count_fields(content)
        metrics.cc, metrics.wmc = self._calculate_complexity(content)
        metrics.cbo, metrics.fanout = self._calculate_coupling(content)
        metrics.lcom = self._calculate_lcom(content)
        metrics.dit = self._calculate_dit(parent_class)
        metrics.rfc = self._calculate_rfc(content, metrics.nom)
        
        return metrics
    
    def _calculate_loc(self, content: str) -> int:
        """Calculate lines of code (excluding blanks and comments)."""
        lines = content.split("\n")
        loc = 0
        in_block_comment = False
        
        for line in lines:
            line = line.strip()
            
            # Handle block comments
            if "/*" in line:
                in_block_comment = True
            if "*/" in line:
                in_block_comment = False
                continue
            
            if in_block_comment:
                continue
            
            # Skip blank lines and single-line comments
            if not line or line.startswith("//"):
                continue
            
            loc += 1
        
        return loc
    
    def _count_methods(self, content: str) -> Tuple[int, int, int, int]:
        """Count methods by visibility."""
        public_count = len(re.findall(r'\bpublic\s+(?:static\s+)?(?:final\s+)?[\w<>\[\],\s]+\s+\w+\s*\(', content))
        private_count = len(re.findall(r'\bprivate\s+(?:static\s+)?(?:final\s+)?[\w<>\[\],\s]+\s+\w+\s*\(', content))
        protected_count = len(re.findall(r'\bprotected\s+(?:static\s+)?(?:final\s+)?[\w<>\[\],\s]+\s+\w+\s*\(', content))
        
        # Exclude constructors from public count
        class_match = self.class_pattern.search(content)
        if class_match:
            class_name = class_match.group(1)
            constructor_count = len(re.findall(rf'\bpublic\s+{class_name}\s*\(', content))
            public_count -= constructor_count
        
        total = public_count + private_count + protected_count
        return total, public_count, private_count, protected_count
    
    def _count_fields(self, content: str) -> Tuple[int, int]:
        """Count fields and attributes."""
        fields = self.field_pattern.findall(content)
        nof = len(fields)
        
        # Count only non-static fields as attributes
        static_fields = len(re.findall(r'(?:public|private|protected)\s+static\s+', content))
        noa = nof - static_fields
        
        return nof, noa
    
    def _calculate_complexity(self, content: str) -> Tuple[float, int]:
        """
        Calculate cyclomatic complexity.
        
        Returns:
            Tuple of (average CC per method, WMC)
        """
        # Split content into methods (simplified approach)
        method_bodies = re.split(r'(?:public|private|protected)\s+', content)
        
        total_cc = 0
        method_count = 0
        
        for body in method_bodies[1:]:  # Skip first split (before first method)
            if '(' in body and '{' in body:
                # Count branching statements
                branches = len(self.branch_pattern.findall(body))
                method_cc = branches + 1  # Base complexity is 1
                total_cc += method_cc
                method_count += 1
        
        wmc = total_cc
        avg_cc = total_cc / method_count if method_count > 0 else 0
        
        return round(avg_cc, 2), wmc
    
    def _calculate_coupling(self, content: str) -> Tuple[int, int]:
        """
        Calculate coupling between objects (CBO) and fan-out.
        
        CBO = number of unique classes this class depends on
        """
        # Find all type references
        types_used = set(self.type_pattern.findall(content))
        
        # Remove built-in types
        external_types = types_used - self.JAVA_BUILTIN_TYPES
        
        # Remove the class itself
        class_match = self.class_pattern.search(content)
        if class_match:
            external_types.discard(class_match.group(1))
        
        cbo = len(external_types)
        fanout = cbo  # Simplified: fanout equals CBO in this implementation
        
        return cbo, fanout
    
    def _calculate_lcom(self, content: str) -> float:
        """
        Calculate Lack of Cohesion of Methods (LCOM).
        
        Uses simplified LCOM4: methods that share fields are cohesive.
        Returns value between 0 (cohesive) and 1 (not cohesive).
        """
        # Extract field names
        fields = set()
        for match in self.field_pattern.finditer(content):
            fields.add(match.group(2))
        
        if not fields:
            return 0.0
        
        # Extract methods and the fields they use
        method_fields = []
        
        # Simple approach: split by method signatures
        methods = re.split(r'(?:public|private|protected)\s+[\w<>\[\],\s]+\s+\w+\s*\([^)]*\)\s*(?:throws[\w,\s]+)?\s*\{', content)
        
        for method in methods[1:]:  # Skip content before first method
            # Find field references in this method
            used_fields = set()
            for field in fields:
                if re.search(rf'\b{field}\b', method):
                    used_fields.add(field)
            if used_fields:
                method_fields.append(used_fields)
        
        if len(method_fields) < 2:
            return 0.0
        
        # Calculate LCOM: pairs of methods that don't share fields
        pairs_without_shared = 0
        pairs_with_shared = 0
        
        for i in range(len(method_fields)):
            for j in range(i + 1, len(method_fields)):
                if method_fields[i] & method_fields[j]:  # Shared fields
                    pairs_with_shared += 1
                else:
                    pairs_without_shared += 1
        
        total_pairs = pairs_with_shared + pairs_without_shared
        if total_pairs == 0:
            return 0.0
        
        lcom = pairs_without_shared / total_pairs
        return round(lcom, 3)
    
    def _calculate_dit(self, parent_class: Optional[str]) -> int:
        """
        Calculate Depth of Inheritance Tree.
        
        Note: This is simplified - would need full class hierarchy for accuracy.
        """
        if not parent_class:
            return 0
        if parent_class in ('Object', 'Exception', 'RuntimeException'):
            return 1
        return 2  # Assume DIT of 2 for other parent classes
    
    def _calculate_rfc(self, content: str, nom: int) -> int:
        """
        Calculate Response for a Class.
        
        RFC = number of methods + number of distinct methods called
        """
        # Count method calls (simplified)
        method_calls = set(re.findall(r'\.(\w+)\s*\(', content))
        
        # Exclude common methods
        common_methods = {'toString', 'equals', 'hashCode', 'get', 'set', 'add', 'remove'}
        external_calls = len(method_calls - common_methods)
        
        rfc = nom + external_calls
        return rfc
    
    def _metrics_to_dataframe(self, metrics_list: List[ClassMetrics]) -> pd.DataFrame:
        """Convert list of ClassMetrics to DataFrame."""
        return pd.DataFrame([{
            "file_path": m.file_path,
            "class_name": m.class_name,
            "package": m.package,
            "repository": m.repository,
            "loc": m.loc,
            "nom": m.nom,
            "nof": m.nof,
            "noa": m.noa,
            "cc": m.cc,
            "wmc": m.wmc,
            "cbo": m.cbo,
            "fanin": m.fanin,
            "fanout": m.fanout,
            "lcom": m.lcom,
            "dit": m.dit,
            "noc": m.noc,
            "rfc": m.rfc,
            "public_methods": m.public_methods,
            "private_methods": m.private_methods,
            "protected_methods": m.protected_methods
        } for m in metrics_list])


if __name__ == "__main__":
    import yaml
    
    logging.basicConfig(level=logging.INFO)
    
    with open("config.yaml") as f:
        config = yaml.safe_load(f)
    
    extractor = MetricExtractor(config)
    metrics_df = extractor.extract_all_metrics()
    
    print(f"\nExtracted metrics for {len(metrics_df)} classes")
    print("\nSample metrics:")
    print(metrics_df.head(10))
    
    print("\nMetric statistics:")
    print(metrics_df[["loc", "nom", "cbo", "wmc", "lcom"]].describe())
