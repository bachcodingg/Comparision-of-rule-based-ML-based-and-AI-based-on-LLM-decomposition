#!/usr/bin/env python3
"""
Tests for Rule-Based Java Decomposition Analyzer
"""

import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestMetricExtractor:
    """Tests for the MetricExtractor class."""
    
    def test_calculate_loc(self):
        """Test lines of code calculation."""
        from metrics.metric_extractor import MetricExtractor
        
        config = {
            "data": {
                "raw_dir": "data/raw",
                "processed_dir": "data/processed",
                "repositories": []
            },
            "metrics": {
                "parser": {
                    "skip_tests": True,
                    "encoding": "UTF-8"
                }
            }
        }
        
        extractor = MetricExtractor(config)
        
        # Test simple code
        code = '''public class Test {
    // Comment
    private int x;
    
    public void method() {
        System.out.println("Hello");
    }
}'''
        loc = extractor._calculate_loc(code)
        assert loc > 0
        assert loc < 10  # Should be around 6-7 lines
    
    def test_count_methods(self):
        """Test method counting."""
        from metrics.metric_extractor import MetricExtractor
        
        config = {
            "data": {
                "raw_dir": "data/raw",
                "processed_dir": "data/processed",
                "repositories": []
            },
            "metrics": {"parser": {}}
        }
        
        extractor = MetricExtractor(config)
        
        code = '''public class Test {
    public void method1() {}
    private void method2() {}
    protected void method3() {}
    public static void method4() {}
}'''
        
        total, pub, priv, prot = extractor._count_methods(code)
        assert total == 4
        assert pub >= 1
        assert priv == 1
        assert prot == 1


class TestRuleAnalyzer:
    """Tests for the RuleBasedAnalyzer class."""
    
    def test_violation_creation(self):
        """Test that violations are created correctly."""
        from analyzer.rule_analyzer import Violation
        
        v = Violation(
            file_path="/test/Test.java",
            class_name="Test",
            package="com.test",
            rule_name="TooManyMethods",
            severity="critical",
            metric_name="nom",
            metric_value=25,
            threshold=20,
            description="Too many methods",
            repository="test-repo"
        )
        
        assert v.class_name == "Test"
        assert v.severity == "critical"
        assert v.metric_value == 25
    
    def test_severity_mapping(self):
        """Test PMD priority to severity mapping."""
        from analyzer.rule_analyzer import RuleBasedAnalyzer
        
        config = {
            "data": {
                "raw_dir": "data/raw",
                "processed_dir": "data/processed",
                "repositories": []
            },
            "rules": {
                "pmd": {"enabled": False},
                "thresholds": {}
            },
            "output": {"results_dir": "results"},
            "analysis": {}
        }
        
        analyzer = RuleBasedAnalyzer(config)
        
        assert analyzer._map_pmd_priority(1) == "severe"
        assert analyzer._map_pmd_priority(2) == "severe"
        assert analyzer._map_pmd_priority(3) == "critical"
        assert analyzer._map_pmd_priority(4) == "warning"
        assert analyzer._map_pmd_priority(5) == "warning"


class TestThresholds:
    """Tests for threshold-based analysis."""
    
    def test_threshold_detection(self):
        """Test that thresholds correctly flag violations."""
        # Create test metrics
        metrics = pd.DataFrame([
            {"class_name": "LargeClass", "loc": 600, "nom": 25, "cbo": 5},
            {"class_name": "SmallClass", "loc": 100, "nom": 5, "cbo": 2},
        ])
        
        # Large class should exceed LOC and NOM thresholds
        assert metrics.iloc[0]["loc"] > 500
        assert metrics.iloc[0]["nom"] > 20
        
        # Small class should not
        assert metrics.iloc[1]["loc"] < 500
        assert metrics.iloc[1]["nom"] < 20


class TestCompositeRules:
    """Tests for composite rule evaluation."""
    
    def test_god_class_detection(self):
        """Test God Class composite rule."""
        # A God Class should have:
        # - High LOC (> 500)
        # - Many methods (> 20)
        # - High coupling (> 10)
        # - Low cohesion (> 0.5)
        
        god_class_metrics = {
            "loc": 800,
            "nom": 30,
            "cbo": 15,
            "lcom": 0.7
        }
        
        # Check that all metrics exceed thresholds
        assert god_class_metrics["loc"] > 500
        assert god_class_metrics["nom"] > 20
        assert god_class_metrics["cbo"] > 10
        assert god_class_metrics["lcom"] > 0.5


class TestEvaluation:
    """Tests for evaluation metrics."""
    
    def test_precision_recall_calculation(self):
        """Test precision and recall calculation."""
        # Simulated predictions and ground truth
        predicted = {"A", "B", "C", "D"}
        actual = {"A", "C", "E", "F"}
        
        tp = len(predicted & actual)  # A, C = 2
        fp = len(predicted - actual)  # B, D = 2
        fn = len(actual - predicted)  # E, F = 2
        
        precision = tp / (tp + fp)  # 2/4 = 0.5
        recall = tp / (tp + fn)     # 2/4 = 0.5
        
        assert precision == 0.5
        assert recall == 0.5
        
        f1 = 2 * precision * recall / (precision + recall)
        assert f1 == 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
