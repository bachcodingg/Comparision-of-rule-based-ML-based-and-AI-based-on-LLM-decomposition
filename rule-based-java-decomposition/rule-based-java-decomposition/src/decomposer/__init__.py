"""
Decomposer Module

This module provides functionality for decomposing large Java classes
into smaller, more cohesive classes using the Extract Class refactoring pattern.

Main Components:
- JavaParser: Parses Java source files
- CohesionAnalyzer: Identifies cohesive method groups
- JavaClassDecomposer: Performs the actual decomposition
"""

from .decomposer import (
    JavaParser,
    CohesionAnalyzer,
    JavaClassDecomposer,
    decompose_java_file,
    JavaClass,
    JavaMethod,
    JavaField,
    ExtractedClass,
    DecompositionResult
)

__all__ = [
    'JavaParser',
    'CohesionAnalyzer', 
    'JavaClassDecomposer',
    'decompose_java_file',
    'JavaClass',
    'JavaMethod',
    'JavaField',
    'ExtractedClass',
    'DecompositionResult'
]
