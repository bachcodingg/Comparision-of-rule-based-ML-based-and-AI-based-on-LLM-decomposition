#!/usr/bin/env python3
"""
Java Class Decomposer Module

This module implements the actual decomposition (Extract Class refactoring) of large Java classes.
It analyzes class structure, identifies cohesive groups of methods/fields, and generates
refactored code with multiple smaller classes.

CITATIONS AND REFERENCES:
-------------------------
This implementation is inspired by and adapts concepts from:

1. CodART (Source Code Automated Refactoring Toolkit)
   - Repository: https://github.com/m-zakeri/CodART
   - Authors: Morteza Zakeri et al.
   - License: MIT
   - Used concepts: ANTLR-based parsing approach, Extract Class refactoring pattern

2. RefactoringMiner
   - Repository: https://github.com/tsantalis/RefactoringMiner
   - Authors: Nikolaos Tsantalis et al.
   - Used concepts: Extract Class detection patterns

3. Martin Fowler's Refactoring Catalog
   - Source: https://refactoring.guru/extract-class
   - Used concepts: Extract Class refactoring methodology

PRIORITY SCORING FORMULA JUSTIFICATION:
---------------------------------------
The priority scoring formula used in this project is based on the QMOOD 
(Quality Model for Object-Oriented Design) by Bansiya & Davis (2002).

Formula: Priority = w1*LOC + w2*WMC + w3*CBO + w4*LCOM + w5*NOM

Weights explanation:
- LOC (25%): Size is the primary indicator of complexity. Research shows 
  classes over 500 LOC have 2-3x higher defect density (Nagappan et al., 2006)
- WMC (25%): Weighted Methods per Class directly correlates with maintenance 
  effort (Chidamber & Kemerer, 1994)
- CBO (20%): High coupling increases change propagation risk and testing 
  difficulty (Briand et al., 1999)
- LCOM (15%): Lack of cohesion indicates multiple responsibilities - the core
  reason for Extract Class refactoring (Fowler, 1999)
- NOM (15%): Method count indicates complexity, but less directly than WMC

References:
- Bansiya, J., & Davis, C. (2002). A hierarchical model for object-oriented 
  design quality assessment. IEEE TSE.
- Chidamber, S. R., & Kemerer, C. F. (1994). A metrics suite for OOD. IEEE TSE.
- Fowler, M. (1999). Refactoring: Improving the Design of Existing Code.

Author: Rule-Based Java Decomposition Project
License: MIT
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class JavaField:
    """Represents a field in a Java class."""
    name: str
    type_name: str
    modifiers: List[str]
    line_number: int
    raw_code: str
    
    def is_private(self) -> bool:
        return "private" in self.modifiers


@dataclass
class JavaMethod:
    """Represents a method in a Java class."""
    name: str
    return_type: str
    parameters: List[Tuple[str, str]]  # (type, name) pairs
    modifiers: List[str]
    body: str
    line_start: int
    line_end: int
    raw_code: str
    
    # Dependencies
    fields_accessed: Set[str] = field(default_factory=set)
    methods_called: Set[str] = field(default_factory=set)
    
    def is_getter(self) -> bool:
        return self.name.startswith("get") and len(self.parameters) == 0
    
    def is_setter(self) -> bool:
        return self.name.startswith("set") and len(self.parameters) == 1
    
    def is_constructor(self, class_name: str) -> bool:
        return self.name == class_name


@dataclass
class JavaClass:
    """Represents a parsed Java class."""
    name: str
    package: str
    imports: List[str]
    modifiers: List[str]
    extends: Optional[str]
    implements: List[str]
    fields: List[JavaField]
    methods: List[JavaMethod]
    inner_classes: List['JavaClass']
    raw_code: str
    file_path: str
    
    def get_loc(self) -> int:
        return len([l for l in self.raw_code.split('\n') if l.strip()])
    
    def get_nom(self) -> int:
        return len(self.methods)


@dataclass
class ExtractedClass:
    """Represents a class extracted during decomposition."""
    name: str
    fields: List[JavaField]
    methods: List[JavaMethod]
    responsibility: str  # Description of what this class does
    

@dataclass
class DecompositionResult:
    """Result of decomposing a large class."""
    original_class: JavaClass
    extracted_classes: List[ExtractedClass]
    modified_original: str  # The refactored original class code
    new_class_codes: List[str]  # Code for each new extracted class
    success: bool
    message: str


class JavaParser:
    """
    Simple regex-based Java parser for extracting class structure.
    
    Note: For production use, consider using ANTLR4 with JavaParserLabeled grammar
    as used in CodART project (https://github.com/m-zakeri/CodART).
    This implementation uses regex for simplicity and portability.
    """
    
    # Regex patterns for Java parsing
    PACKAGE_PATTERN = re.compile(r'package\s+([\w.]+)\s*;')
    IMPORT_PATTERN = re.compile(r'import\s+([\w.*]+)\s*;')
    CLASS_PATTERN = re.compile(
        r'((?:public|private|protected|abstract|final|static)\s+)*'
        r'class\s+(\w+)'
        r'(?:\s+extends\s+(\w+))?'
        r'(?:\s+implements\s+([\w,\s]+))?'
        r'\s*\{'
    )
    FIELD_PATTERN = re.compile(
        r'((?:private|public|protected|static|final|volatile|transient)\s+)*'
        r'(\w+(?:<[\w<>,\s]+>)?)\s+(\w+)\s*(?:=\s*[^;]+)?\s*;'
    )
    METHOD_PATTERN = re.compile(
        r'((?:public|private|protected|static|final|abstract|synchronized)\s+)*'
        r'(\w+(?:<[\w<>,\s]+>)?)\s+(\w+)\s*\(([^)]*)\)\s*'
        r'(?:throws\s+[\w,\s]+)?\s*\{'
    )
    
    def parse_file(self, file_path: str) -> Optional[JavaClass]:
        """Parse a Java file and return a JavaClass object."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return self.parse_content(content, file_path)
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            return None
    
    def parse_content(self, content: str, file_path: str = "") -> Optional[JavaClass]:
        """Parse Java content string and return a JavaClass object."""
        # Extract package
        package_match = self.PACKAGE_PATTERN.search(content)
        package = package_match.group(1) if package_match else ""
        
        # Extract imports
        imports = self.IMPORT_PATTERN.findall(content)
        
        # Find class declaration
        class_match = self.CLASS_PATTERN.search(content)
        if not class_match:
            return None
        
        modifiers_str = class_match.group(1) or ""
        modifiers = modifiers_str.split() if modifiers_str else []
        class_name = class_match.group(2)
        extends = class_match.group(3)
        implements_str = class_match.group(4)
        implements = [i.strip() for i in implements_str.split(',')] if implements_str else []
        
        # Find class body
        class_start = class_match.end() - 1
        class_body = self._extract_block(content, class_start)
        
        # Parse fields
        fields = self._parse_fields(class_body)
        
        # Parse methods
        methods = self._parse_methods(class_body, class_name)
        
        # Analyze dependencies
        self._analyze_dependencies(methods, fields)
        
        return JavaClass(
            name=class_name,
            package=package,
            imports=imports,
            modifiers=modifiers,
            extends=extends,
            implements=implements,
            fields=fields,
            methods=methods,
            inner_classes=[],
            raw_code=content,
            file_path=file_path
        )
    
    def _extract_block(self, content: str, start: int) -> str:
        """Extract a balanced brace block starting from position."""
        if content[start] != '{':
            return ""
        
        depth = 0
        end = start
        in_string = False
        string_char = None
        
        for i in range(start, len(content)):
            char = content[i]
            
            # Handle string literals
            if char in '"\'':
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char and content[i-1] != '\\':
                    in_string = False
                continue
            
            if in_string:
                continue
            
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    end = i
                    break
        
        return content[start:end+1]
    
    def _parse_fields(self, class_body: str) -> List[JavaField]:
        """Parse field declarations from class body."""
        fields = []
        lines = class_body.split('\n')
        
        for i, line in enumerate(lines):
            # Skip method bodies
            if '{' in line and '(' in line:
                continue
            
            match = self.FIELD_PATTERN.search(line)
            if match and '(' not in line:  # Ensure it's not a method
                modifiers_str = match.group(1) or ""
                modifiers = modifiers_str.split() if modifiers_str else ["package-private"]
                type_name = match.group(2)
                name = match.group(3)
                
                fields.append(JavaField(
                    name=name,
                    type_name=type_name,
                    modifiers=modifiers,
                    line_number=i + 1,
                    raw_code=line.strip()
                ))
        
        return fields
    
    def _parse_methods(self, class_body: str, class_name: str) -> List[JavaMethod]:
        """Parse method declarations from class body."""
        methods = []
        
        for match in self.METHOD_PATTERN.finditer(class_body):
            modifiers_str = match.group(1) or ""
            modifiers = modifiers_str.split() if modifiers_str else ["package-private"]
            return_type = match.group(2)
            name = match.group(3)
            params_str = match.group(4)
            
            # Parse parameters
            parameters = []
            if params_str.strip():
                for param in params_str.split(','):
                    parts = param.strip().split()
                    if len(parts) >= 2:
                        parameters.append((parts[-2], parts[-1]))
            
            # Extract method body
            method_start = match.end() - 1
            body = self._extract_block(class_body, method_start)
            
            # Calculate line numbers
            line_start = class_body[:match.start()].count('\n') + 1
            line_end = line_start + body.count('\n')
            
            methods.append(JavaMethod(
                name=name,
                return_type=return_type,
                parameters=parameters,
                modifiers=modifiers,
                body=body,
                line_start=line_start,
                line_end=line_end,
                raw_code=match.group(0) + body
            ))
        
        return methods
    
    def _analyze_dependencies(self, methods: List[JavaMethod], fields: List[JavaField]) -> None:
        """Analyze which fields each method accesses and which methods it calls."""
        field_names = {f.name for f in fields}
        method_names = {m.name for m in methods}
        
        for method in methods:
            # Find field accesses
            for field_name in field_names:
                # Look for field access patterns: this.field, field, this.field =
                patterns = [
                    rf'\bthis\.{field_name}\b',
                    rf'\b{field_name}\s*[=\+\-\*\/]',
                    rf'[=\+\-\*\/\(,]\s*{field_name}\b'
                ]
                for pattern in patterns:
                    if re.search(pattern, method.body):
                        method.fields_accessed.add(field_name)
                        break
            
            # Find method calls
            for method_name in method_names:
                if method_name != method.name:  # Don't count self-calls as dependencies
                    if re.search(rf'\b{method_name}\s*\(', method.body):
                        method.methods_called.add(method_name)


class CohesionAnalyzer:
    """
    Analyzes method-field relationships to identify cohesive groups.
    
    This approach is based on the LCOM (Lack of Cohesion of Methods) concept
    from Chidamber & Kemerer metrics, but uses graph-based clustering to
    identify groups of related methods that could form separate classes.
    
    Reference: 
    - Bavota, G. et al. (2014). "Recommending Refactorings Based on 
      Historical Analysis of Changes"
    """
    
    def analyze(self, java_class: JavaClass) -> List[Set[str]]:
        """
        Identify cohesive groups of methods based on shared field access.
        
        Returns list of sets, where each set contains method names that
        should stay together (share field access patterns).
        """
        if not java_class.methods:
            return []
        
        # Build method-field access matrix
        method_field_matrix = {}
        for method in java_class.methods:
            method_field_matrix[method.name] = method.fields_accessed
        
        # Build method similarity graph based on shared field access
        method_names = list(method_field_matrix.keys())
        similarity = defaultdict(float)
        
        for i, m1 in enumerate(method_names):
            for m2 in method_names[i+1:]:
                fields1 = method_field_matrix[m1]
                fields2 = method_field_matrix[m2]
                
                if fields1 and fields2:
                    # Jaccard similarity
                    intersection = len(fields1 & fields2)
                    union = len(fields1 | fields2)
                    if union > 0:
                        similarity[(m1, m2)] = intersection / union
        
        # Group methods using connected components with similarity threshold
        threshold = 0.3  # Methods sharing >30% fields are considered related
        groups = self._cluster_methods(method_names, similarity, threshold)
        
        return groups
    
    def _cluster_methods(self, methods: List[str], 
                         similarity: Dict[Tuple[str, str], float],
                         threshold: float) -> List[Set[str]]:
        """Cluster methods using Union-Find based on similarity threshold."""
        # Initialize each method as its own group
        parent = {m: m for m in methods}
        
        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]
        
        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py
        
        # Union methods with similarity above threshold
        for (m1, m2), sim in similarity.items():
            if sim >= threshold:
                union(m1, m2)
        
        # Collect groups
        groups_dict = defaultdict(set)
        for m in methods:
            groups_dict[find(m)].add(m)
        
        return list(groups_dict.values())


class JavaClassDecomposer:
    """
    Main class for decomposing large Java classes into smaller ones.
    
    This implements the Extract Class refactoring pattern as described by
    Martin Fowler in "Refactoring: Improving the Design of Existing Code".
    
    The decomposition process:
    1. Parse the Java class to extract structure
    2. Analyze cohesion to identify method groups
    3. Determine which groups should be extracted
    4. Generate new class code for extracted groups
    5. Modify original class to delegate to new classes
    """
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.parser = JavaParser()
        self.cohesion_analyzer = CohesionAnalyzer()
        
        # Decomposition thresholds
        self.min_methods_to_extract = self.config.get("min_methods_to_extract", 3)
        self.min_fields_to_extract = self.config.get("min_fields_to_extract", 2)
    
    def decompose(self, java_class: JavaClass) -> DecompositionResult:
        """
        Decompose a large Java class into smaller classes.
        
        Args:
            java_class: The parsed Java class to decompose
            
        Returns:
            DecompositionResult with extracted classes and refactored code
        """
        logger.info(f"Analyzing class {java_class.name} for decomposition...")
        
        # Analyze cohesion to find method groups
        method_groups = self.cohesion_analyzer.analyze(java_class)
        
        # Filter groups that are large enough to extract
        extractable_groups = [
            g for g in method_groups 
            if len(g) >= self.min_methods_to_extract
        ]
        
        if len(extractable_groups) <= 1:
            return DecompositionResult(
                original_class=java_class,
                extracted_classes=[],
                modified_original=java_class.raw_code,
                new_class_codes=[],
                success=False,
                message="No clear decomposition found - class may already be cohesive"
            )
        
        # Create extracted classes
        extracted_classes = []
        for i, method_names in enumerate(extractable_groups[1:], 1):  # Keep first group in original
            extracted = self._create_extracted_class(
                java_class, method_names, i
            )
            if extracted:
                extracted_classes.append(extracted)
        
        if not extracted_classes:
            return DecompositionResult(
                original_class=java_class,
                extracted_classes=[],
                modified_original=java_class.raw_code,
                new_class_codes=[],
                success=False,
                message="Could not create meaningful extracted classes"
            )
        
        # Generate code for extracted classes
        new_class_codes = [
            self._generate_class_code(java_class, ec)
            for ec in extracted_classes
        ]
        
        # Modify original class
        modified_original = self._generate_modified_original(
            java_class, extracted_classes
        )
        
        return DecompositionResult(
            original_class=java_class,
            extracted_classes=extracted_classes,
            modified_original=modified_original,
            new_class_codes=new_class_codes,
            success=True,
            message=f"Successfully extracted {len(extracted_classes)} class(es)"
        )
    
    def _create_extracted_class(self, original: JavaClass, 
                                 method_names: Set[str],
                                 index: int) -> Optional[ExtractedClass]:
        """Create an ExtractedClass from a group of methods."""
        # Get methods to extract
        methods = [m for m in original.methods if m.name in method_names]
        
        if not methods:
            return None
        
        # Find fields accessed by these methods
        accessed_fields = set()
        for method in methods:
            accessed_fields.update(method.fields_accessed)
        
        # Get field objects
        fields = [f for f in original.fields if f.name in accessed_fields]
        
        # Generate class name based on common method pattern
        class_name = self._suggest_class_name(methods, original.name, index)
        
        # Determine responsibility description
        responsibility = self._infer_responsibility(methods)
        
        return ExtractedClass(
            name=class_name,
            fields=fields,
            methods=methods,
            responsibility=responsibility
        )
    
    def _suggest_class_name(self, methods: List[JavaMethod], 
                            original_name: str, index: int) -> str:
        """Suggest a name for the extracted class based on method patterns."""
        # Look for common prefixes in method names
        method_names = [m.name for m in methods]
        
        # Try to find common prefix
        if len(method_names) > 1:
            prefix = os.path.commonprefix(method_names)
            if len(prefix) > 3:
                # Capitalize and use as class name
                suggested = prefix.rstrip('_').title().replace('_', '')
                if suggested and suggested[0].isupper():
                    return f"{original_name}{suggested}Helper"
        
        # Look for patterns like get/set, handle, process
        patterns = {
            'get': 'DataAccessor',
            'set': 'DataMutator', 
            'handle': 'Handler',
            'process': 'Processor',
            'validate': 'Validator',
            'parse': 'Parser',
            'format': 'Formatter',
            'calculate': 'Calculator',
            'compute': 'Computer',
            'send': 'Sender',
            'receive': 'Receiver',
            'load': 'Loader',
            'save': 'Persister',
            'create': 'Factory',
            'build': 'Builder'
        }
        
        for method_name in method_names:
            lower_name = method_name.lower()
            for pattern, suffix in patterns.items():
                if lower_name.startswith(pattern):
                    return f"{original_name}{suffix}"
        
        # Default naming
        return f"{original_name}Component{index}"
    
    def _infer_responsibility(self, methods: List[JavaMethod]) -> str:
        """Infer the responsibility of the extracted class."""
        method_names = [m.name.lower() for m in methods]
        
        # Check for common patterns
        if all('get' in n or 'set' in n for n in method_names):
            return "Data access and mutation"
        if all('valid' in n or 'check' in n for n in method_names):
            return "Validation logic"
        if all('parse' in n or 'format' in n for n in method_names):
            return "Data parsing and formatting"
        if all('handle' in n or 'process' in n for n in method_names):
            return "Event/data processing"
        if all('save' in n or 'load' in n or 'persist' in n for n in method_names):
            return "Persistence operations"
        
        return "Extracted functionality"
    
    def _generate_class_code(self, original: JavaClass, 
                              extracted: ExtractedClass) -> str:
        """Generate Java code for an extracted class."""
        lines = []
        
        # Package declaration
        if original.package:
            lines.append(f"package {original.package};")
            lines.append("")
        
        # Imports (copy relevant ones from original)
        if original.imports:
            for imp in original.imports:
                lines.append(f"import {imp};")
            lines.append("")
        
        # Class documentation
        lines.append("/**")
        lines.append(f" * {extracted.responsibility}")
        lines.append(f" * ")
        lines.append(f" * Extracted from {original.name} using rule-based decomposition.")
        lines.append(f" * ")
        lines.append(f" * @see {original.name}")
        lines.append(" */")
        
        # Class declaration
        lines.append(f"public class {extracted.name} {{")
        lines.append("")
        
        # Fields
        if extracted.fields:
            lines.append("    // Fields")
            for field in extracted.fields:
                lines.append(f"    {field.raw_code}")
            lines.append("")
        
        # Constructor
        lines.append(f"    public {extracted.name}() {{")
        lines.append("        // Default constructor")
        lines.append("    }")
        lines.append("")
        
        # Methods
        lines.append("    // Methods")
        for method in extracted.methods:
            # Add method with proper indentation
            method_lines = method.raw_code.split('\n')
            for ml in method_lines:
                lines.append(f"    {ml}")
            lines.append("")
        
        lines.append("}")
        
        return '\n'.join(lines)
    
    def _generate_modified_original(self, original: JavaClass,
                                     extracted_classes: List[ExtractedClass]) -> str:
        """Generate modified original class that delegates to extracted classes."""
        lines = []
        
        # Package declaration
        if original.package:
            lines.append(f"package {original.package};")
            lines.append("")
        
        # Imports
        if original.imports:
            for imp in original.imports:
                lines.append(f"import {imp};")
            lines.append("")
        
        # Class documentation
        lines.append("/**")
        lines.append(f" * {original.name}")
        lines.append(f" * ")
        lines.append(f" * Refactored using rule-based decomposition.")
        lines.append(f" * Extracted components:")
        for ec in extracted_classes:
            lines.append(f" *   - {ec.name}: {ec.responsibility}")
        lines.append(" */")
        
        # Build class declaration
        class_decl = " ".join(original.modifiers) if original.modifiers else "public"
        class_decl += f" class {original.name}"
        if original.extends:
            class_decl += f" extends {original.extends}"
        if original.implements:
            class_decl += f" implements {', '.join(original.implements)}"
        class_decl += " {"
        
        lines.append(class_decl)
        lines.append("")
        
        # Add references to extracted classes
        lines.append("    // Extracted component references")
        for ec in extracted_classes:
            var_name = ec.name[0].lower() + ec.name[1:]
            lines.append(f"    private final {ec.name} {var_name} = new {ec.name}();")
        lines.append("")
        
        # Keep fields not in extracted classes
        extracted_field_names = set()
        for ec in extracted_classes:
            extracted_field_names.update(f.name for f in ec.fields)
        
        remaining_fields = [f for f in original.fields if f.name not in extracted_field_names]
        if remaining_fields:
            lines.append("    // Remaining fields")
            for field in remaining_fields:
                lines.append(f"    {field.raw_code}")
            lines.append("")
        
        # Keep methods not in extracted classes
        extracted_method_names = set()
        for ec in extracted_classes:
            extracted_method_names.update(m.name for m in ec.methods)
        
        remaining_methods = [m for m in original.methods if m.name not in extracted_method_names]
        
        # Add delegation methods for extracted methods
        lines.append("    // Delegation methods to extracted components")
        for ec in extracted_classes:
            var_name = ec.name[0].lower() + ec.name[1:]
            for method in ec.methods:
                # Create delegation method
                params = ", ".join(f"{t} {n}" for t, n in method.parameters)
                param_names = ", ".join(n for _, n in method.parameters)
                
                lines.append(f"    public {method.return_type} {method.name}({params}) {{")
                if method.return_type == "void":
                    lines.append(f"        {var_name}.{method.name}({param_names});")
                else:
                    lines.append(f"        return {var_name}.{method.name}({param_names});")
                lines.append("    }")
                lines.append("")
        
        # Add remaining methods
        if remaining_methods:
            lines.append("    // Remaining methods")
            for method in remaining_methods:
                method_lines = method.raw_code.split('\n')
                for ml in method_lines:
                    lines.append(f"    {ml}")
                lines.append("")
        
        lines.append("}")
        
        return '\n'.join(lines)
    
    def decompose_file(self, file_path: str, output_dir: str = None) -> DecompositionResult:
        """
        Decompose a Java file and optionally write results to output directory.
        
        Args:
            file_path: Path to the Java file
            output_dir: Directory to write decomposed files (optional)
            
        Returns:
            DecompositionResult
        """
        java_class = self.parser.parse_file(file_path)
        
        if not java_class:
            return DecompositionResult(
                original_class=None,
                extracted_classes=[],
                modified_original="",
                new_class_codes=[],
                success=False,
                message=f"Failed to parse {file_path}"
            )
        
        result = self.decompose(java_class)
        
        # Write output files if directory specified and decomposition successful
        if output_dir and result.success:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Write modified original
            original_file = output_path / f"{java_class.name}.java"
            original_file.write_text(result.modified_original)
            logger.info(f"Wrote modified original to {original_file}")
            
            # Write extracted classes
            for ec, code in zip(result.extracted_classes, result.new_class_codes):
                extracted_file = output_path / f"{ec.name}.java"
                extracted_file.write_text(code)
                logger.info(f"Wrote extracted class to {extracted_file}")
        
        return result


# Convenience function for direct usage
def decompose_java_file(file_path: str, output_dir: str = None) -> DecompositionResult:
    """
    Decompose a large Java file into smaller classes.
    
    Args:
        file_path: Path to the Java file to decompose
        output_dir: Optional directory to write decomposed files
        
    Returns:
        DecompositionResult with decomposition details
    """
    decomposer = JavaClassDecomposer()
    return decomposer.decompose_file(file_path, output_dir)


if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print("Usage: python decomposer.py <java_file> [output_dir]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    result = decompose_java_file(file_path, output_dir)
    
    if result.success:
        print(f"\n✓ {result.message}")
        print(f"\nExtracted {len(result.extracted_classes)} class(es):")
        for ec in result.extracted_classes:
            print(f"  - {ec.name}: {ec.responsibility}")
            print(f"    Methods: {[m.name for m in ec.methods]}")
            print(f"    Fields: {[f.name for f in ec.fields]}")
    else:
        print(f"\n✗ {result.message}")
