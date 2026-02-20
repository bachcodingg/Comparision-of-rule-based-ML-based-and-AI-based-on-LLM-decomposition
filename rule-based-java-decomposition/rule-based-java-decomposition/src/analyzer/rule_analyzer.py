#!/usr/bin/env python3
"""
Rule-Based Analyzer Module - Updated for Research-Based Thresholds

Implements rule-based detection of large Java classes using:
1. PMD static analysis rules
2. Custom threshold-based rules (4-level severity)
3. Composite rules combining multiple metrics

Based on recent research (2022-2023):
- Dewangan et al. (2023): 4-level severity classification
- Verma et al. (2023): Multi-metric detection reduces false positives
- Rao et al. (2023): Empirical threshold validation

Updated: January 2026
Version: 2.0
"""

import os
import csv
import json
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Violation:
    """Represents a rule violation detected in a Java class."""
    file_path: str
    class_name: str
    package: str
    rule_name: str
    severity: str  # low, medium, high, critical (4-level system)
    metric_name: str
    metric_value: float
    threshold: float
    description: str
    line_number: int = 1
    priority_score: float = 0.0
    repository: str = ""


@dataclass
class AnalysisResult:
    """Complete analysis result for a Java class."""
    file_path: str
    class_name: str
    package: str
    repository: str
    violations: List[Violation] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    total_score: float = 0.0
    decomposition_recommended: bool = False
    priority_rank: int = 0
    recommendations: List[str] = field(default_factory=list)


class RuleBasedAnalyzer:
    """
    Rule-Based Analyzer for detecting large Java classes.
    
    Uses 4-level severity system (Low, Medium, High, Critical) based on
    empirical research from Dewangan et al. (2023), Rao et al. (2023),
    and Gupta & Chauhan (2022).
    
    Attributes:
        config: Configuration dictionary from config.yaml
        thresholds: Metric thresholds for detection (4 levels per metric)
        results_dir: Directory for saving results
    """
    
    def __init__(self, config: dict):
        """
        Initialize the analyzer with configuration.
        
        Args:
            config: Configuration dictionary containing rule settings
        """
        self.config = config
        self.rules_config = config.get("rules", {})
        self.thresholds = self.rules_config.get("thresholds", {})
        self.composite_rules = self.rules_config.get("composite_rules", [])
        
        # Directories
        self.raw_dir = Path(config["data"]["raw_dir"])
        self.processed_dir = Path(config["data"]["processed_dir"])
        self.results_dir = Path(config["output"]["results_dir"])
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # PMD settings
        self.pmd_config = self.rules_config.get("pmd", {})
        self.pmd_executable = self.pmd_config.get("executable", "pmd")
        self.pmd_ruleset = self.pmd_config.get("ruleset", "src/rules/pmd_rules.xml")
        
        # Analysis settings with 4-level severity weights
        # Based on Rao et al. (2023)
        self.analysis_config = config.get("analysis", {})
        self.severity_weights = self.analysis_config.get("severity_weights", {
            "low": 1,
            "medium": 2,
            "high": 3,
            "critical": 4
        })
        
        # Repository list
        self.repositories = config["data"]["repositories"]
        
        logger.info("Initialized RuleBasedAnalyzer with 4-level severity system")
    
    def get_severity_for_metric(self, metric_name: str, value: float) -> str:
        """
        Determine severity level for a metric value.
        
        Uses 4-level thresholds from research:
        - Low: Below medium threshold
        - Medium: Between medium and high
        - High: Between high and critical
        - Critical: Above critical threshold
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            
        Returns:
            Severity level string: 'low', 'medium', 'high', or 'critical'
        """
        thresholds = self.thresholds.get(metric_name, {})
        
        # Get threshold values (with defaults)
        low = thresholds.get("low", 0)
        medium = thresholds.get("medium", 100)
        high = thresholds.get("high", 200)
        critical = thresholds.get("critical", 300)
        
        if value >= critical:
            return "critical"
        elif value >= high:
            return "high"
        elif value >= medium:
            return "medium"
        else:
            return "low"
    
    def create_pmd_ruleset(self) -> Path:
        """
        Create PMD ruleset XML file with configured rules.
        
        Returns:
            Path to the created ruleset file
        """
        pmd_rules = self.pmd_config.get("rules", [])
        
        # Build rule references
        rule_refs = []
        for rule in pmd_rules:
            if not rule.get("enabled", True):
                continue
                
            rule_name = rule["name"]
            threshold = rule.get("threshold")
            
            if threshold:
                rule_refs.append(f'''
    <rule ref="category/java/design.xml/{rule_name}">
        <properties>
            <property name="minimum" value="{threshold}"/>
        </properties>
    </rule>''')
            else:
                rule_refs.append(f'''
    <rule ref="category/java/design.xml/{rule_name}"/>''')
        
        ruleset_content = f'''<?xml version="1.0"?>
<ruleset name="LargeClassDetection"
         xmlns="http://pmd.sourceforge.net/ruleset/2.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://pmd.sourceforge.net/ruleset/2.0.0 
                             https://pmd.sourceforge.io/ruleset_2_0_0.xsd">
    
    <description>Rules for detecting large Java classes that may need decomposition</description>
    {"".join(rule_refs)}
</ruleset>'''
        
        ruleset_path = Path(self.pmd_ruleset)
        ruleset_path.parent.mkdir(parents=True, exist_ok=True)
        ruleset_path.write_text(ruleset_content)
        
        logger.info(f"Created PMD ruleset: {ruleset_path}")
        return ruleset_path
    
    def run_pmd_analysis(self) -> pd.DataFrame:
        """
        Run PMD static analysis on all repositories.
        
        Returns:
            DataFrame with PMD violations
        """
        if not self.pmd_config.get("enabled", True):
            logger.info("PMD analysis disabled in config")
            return pd.DataFrame()
        
        self.create_pmd_ruleset()
        all_violations = []
        
        for repo in self.repositories:
            repo_name = repo["name"]
            repo_path = self.raw_dir / repo_name
            
            if not repo_path.exists():
                logger.warning(f"Repository not found: {repo_path}")
                continue
            
            logger.info(f"Running PMD on {repo_name}...")
            violations = self._run_pmd_on_repo(repo_path, repo_name)
            all_violations.extend(violations)
            logger.info(f"Found {len(violations)} PMD violations in {repo_name}")
        
        df = self._violations_to_dataframe(all_violations)
        
        # Save PMD results
        output_path = self.results_dir / "pmd_violations.csv"
        df.to_csv(output_path, index=False)
        logger.info(f"Saved PMD results to {output_path}")
        
        return df
    
    def _run_pmd_on_repo(self, repo_path: Path, repo_name: str) -> List[Violation]:
        """Run PMD on a single repository."""
        violations = []
        output_file = self.results_dir / f"pmd_{repo_name}_raw.csv"
        
        try:
            cmd = [
                self.pmd_executable, "check",
                "-d", str(repo_path),
                "-R", self.pmd_ruleset,
                "-f", "csv",
                "-r", str(output_file)
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=600
            )
            
            if output_file.exists():
                violations = self._parse_pmd_csv(output_file, repo_name)
                
        except FileNotFoundError:
            logger.warning("PMD not installed. Using fallback analysis.")
            violations = self._fallback_pmd_analysis(repo_path, repo_name)
        except subprocess.TimeoutExpired:
            logger.error(f"PMD timed out on {repo_name}")
        except Exception as e:
            logger.error(f"PMD error: {e}")
            violations = self._fallback_pmd_analysis(repo_path, repo_name)
        
        return violations
    
    def _parse_pmd_csv(self, csv_file: Path, repo_name: str) -> List[Violation]:
        """Parse PMD CSV output into Violation objects."""
        violations = []
        
        try:
            with open(csv_file, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    violation = Violation(
                        file_path=row.get("File", ""),
                        class_name=Path(row.get("File", "")).stem,
                        package=self._extract_package(row.get("File", "")),
                        rule_name=row.get("Rule", ""),
                        severity=self._map_pmd_priority(int(row.get("Priority", 3))),
                        metric_name=row.get("Rule", ""),
                        metric_value=0,
                        threshold=0,
                        description=row.get("Description", ""),
                        line_number=int(row.get("Line", 1)),
                        repository=repo_name
                    )
                    violations.append(violation)
        except Exception as e:
            logger.error(f"Error parsing PMD CSV: {e}")
        
        return violations
    
    def _map_pmd_priority(self, priority: int) -> str:
        """
        Map PMD priority (1-5) to our 4-level severity system.
        
        PMD uses 1=High, 2=Medium-High, 3=Medium, 4=Low, 5=Info
        We map to: critical, high, medium, low
        """
        if priority == 1:
            return "critical"
        elif priority == 2:
            return "high"
        elif priority == 3:
            return "medium"
        else:
            return "low"
    
    def _extract_package(self, file_path: str) -> str:
        """Extract package name from file path."""
        parts = Path(file_path).parts
        if "src" in parts:
            idx = parts.index("src")
            pkg_parts = [p for p in parts[idx+1:-1] if p not in ["main", "java", "test"]]
            return ".".join(pkg_parts)
        return ""
    
    def _fallback_pmd_analysis(self, repo_path: Path, repo_name: str) -> List[Violation]:
        """
        Fallback analysis when PMD is not available.
        Uses simple heuristics based on file size.
        """
        violations = []
        
        for java_file in repo_path.rglob("*.java"):
            try:
                content = java_file.read_text(encoding='utf-8', errors='ignore')
                loc = len([l for l in content.split("\n") if l.strip() and not l.strip().startswith("//")])
                
                # Use config thresholds
                loc_threshold = self.thresholds.get("lines_of_code", {}).get("high", 1000)
                method_threshold = self.thresholds.get("number_of_methods", {}).get("high", 40)
                
                # Simple LOC check
                if loc > loc_threshold:
                    severity = self.get_severity_for_metric("lines_of_code", loc)
                    violation = Violation(
                        file_path=str(java_file),
                        class_name=java_file.stem,
                        package=self._extract_package(str(java_file)),
                        rule_name="ExcessiveClassLength",
                        severity=severity,
                        metric_name="lines_of_code",
                        metric_value=loc,
                        threshold=loc_threshold,
                        description=f"Class has {loc} lines",
                        repository=repo_name
                    )
                    violations.append(violation)
                
                # Simple method count check
                method_count = content.count("public ") + content.count("private ") + content.count("protected ")
                if method_count > method_threshold:
                    severity = self.get_severity_for_metric("number_of_methods", method_count)
                    violation = Violation(
                        file_path=str(java_file),
                        class_name=java_file.stem,
                        package=self._extract_package(str(java_file)),
                        rule_name="TooManyMethods",
                        severity=severity,
                        metric_name="number_of_methods",
                        metric_value=method_count,
                        threshold=method_threshold,
                        description=f"Class has ~{method_count} methods",
                        repository=repo_name
                    )
                    violations.append(violation)
                    
            except Exception as e:
                logger.error(f"Error analyzing {java_file}: {e}")
        
        return violations
    
    def run_threshold_analysis(self) -> pd.DataFrame:
        """
        Run threshold-based analysis on extracted metrics.
        
        Checks each metric against 4-level thresholds:
        low < medium < high < critical
        
        Returns:
            DataFrame with threshold violations
        """
        metrics_file = self.processed_dir / "code_metrics.csv"
        
        if not metrics_file.exists():
            logger.warning(f"Metrics file not found: {metrics_file}")
            return pd.DataFrame()
        
        metrics_df = pd.read_csv(metrics_file)
        violations = []
        
        for _, row in metrics_df.iterrows():
            class_name = row.get("class_name", "Unknown")
            file_path = row.get("file_path", "")
            package = row.get("package", "")
            repo = row.get("repository", "")
            
            # Check each metric against thresholds
            for metric_name, metric_thresholds in self.thresholds.items():
                metric_value = row.get(metric_name, 0)
                
                # Determine severity level
                severity = self.get_severity_for_metric(metric_name, metric_value)
                
                # Only create violation if medium or above
                if severity in ["medium", "high", "critical"]:
                    # Get the threshold that was exceeded
                    if severity == "critical":
                        exceeded_threshold = metric_thresholds.get("critical", 0)
                    elif severity == "high":
                        exceeded_threshold = metric_thresholds.get("high", 0)
                    else:  # medium
                        exceeded_threshold = metric_thresholds.get("medium", 0)
                    
                    violation = Violation(
                        file_path=file_path,
                        class_name=class_name,
                        package=package,
                        rule_name=f"{metric_name}_threshold",
                        severity=severity,
                        metric_name=metric_name,
                        metric_value=metric_value,
                        threshold=exceeded_threshold,
                        description=f"{metric_name}={metric_value:.2f} exceeds {severity} threshold ({exceeded_threshold})",
                        repository=repo
                    )
                    violations.append(violation)
        
        df = self._violations_to_dataframe(violations)
        
        # Save threshold violations
        output_path = self.results_dir / "threshold_violations.csv"
        df.to_csv(output_path, index=False)
        logger.info(f"Found {len(violations)} threshold violations")
        logger.info(f"Saved threshold results to {output_path}")
        
        return df
    
    def run_composite_analysis(self) -> pd.DataFrame:
        """
        Run composite rule analysis.
        
        Composite rules require multiple metrics to exceed thresholds.
        Example: God Class Candidate = 2+ metrics at HIGH or CRITICAL
        
        Based on Dewangan et al. (2023) and Verma et al. (2023):
        Multi-metric detection reduces false positives.
        
        Returns:
            DataFrame with composite rule violations
        """
        metrics_file = self.processed_dir / "code_metrics.csv"
        
        if not metrics_file.exists():
            logger.warning(f"Metrics file not found: {metrics_file}")
            return pd.DataFrame()
        
        metrics_df = pd.read_csv(metrics_file)
        violations = []
        
        for _, row in metrics_df.iterrows():
            class_name = row.get("class_name", "Unknown")
            
            for rule in self.composite_rules:
                rule_name = rule.get("name", "")
                conditions = rule.get("conditions", {})
                min_violations = conditions.get("min_violations", 2)
                required_severity = conditions.get("severity_level", "high")
                
                # Count how many metrics meet the criteria
                violation_count = 0
                violated_metrics = []
                
                for condition_str in conditions.get("metrics", []):
                    if self._evaluate_condition(row, condition_str, required_severity):
                        violation_count += 1
                        metric_name = condition_str.split(">=")[0].strip()
                        violated_metrics.append(metric_name)
                
                # If enough violations, create composite violation
                if violation_count >= min_violations:
                    violation = Violation(
                        file_path=row.get("file_path", ""),
                        class_name=class_name,
                        package=row.get("package", ""),
                        rule_name=rule_name,
                        severity="high" if required_severity == "high" else "critical",
                        metric_name="composite",
                        metric_value=violation_count,
                        threshold=min_violations,
                        description=f"{rule_name}: {violation_count} metrics at {required_severity.upper()} or above ({', '.join(violated_metrics)})",
                        repository=row.get("repository", "")
                    )
                    violations.append(violation)
        
        df = self._violations_to_dataframe(violations)
        
        # Save composite violations
        output_path = self.results_dir / "composite_violations.csv"
        df.to_csv(output_path, index=False)
        logger.info(f"Found {len(violations)} composite rule violations")
        logger.info(f"Saved composite results to {output_path}")
        
        return df
    
    def _evaluate_condition(self, row: pd.Series, condition_str: str, required_severity: str) -> bool:
        """
        Evaluate a single condition string like 'lines_of_code >= high'.
        
        Args:
            row: DataFrame row with metric values
            condition_str: Condition string to evaluate
            required_severity: Required severity level
            
        Returns:
            True if condition is met
        """
        try:
            parts = condition_str.split(">=")
            if len(parts) != 2:
                return False
            
            metric_name = parts[0].strip()
            threshold_level = parts[1].strip()
            
            metric_value = row.get(metric_name, 0)
            
            # Get actual severity for this metric value
            actual_severity = self.get_severity_for_metric(metric_name, metric_value)
            
            # Check if actual severity meets or exceeds required severity
            severity_order = ["low", "medium", "high", "critical"]
            actual_idx = severity_order.index(actual_severity)
            required_idx = severity_order.index(required_severity)
            
            return actual_idx >= required_idx
            
        except Exception as e:
            logger.error(f"Error evaluating condition '{condition_str}': {e}")
            return False
    
    def run_full_analysis(self) -> pd.DataFrame:
        """
        Run complete analysis: PMD + Threshold + Composite rules.
        
        Returns:
            Combined DataFrame with all violations
        """
        logger.info("Starting full rule-based analysis...")
        
        # Run all three analysis types
        pmd_df = self.run_pmd_analysis()
        threshold_df = self.run_threshold_analysis()
        composite_df = self.run_composite_analysis()
        
        # Combine results
        all_dfs = [df for df in [pmd_df, threshold_df, composite_df] if not df.empty]
        
        if all_dfs:
            combined_df = pd.concat(all_dfs, ignore_index=True)
        else:
            combined_df = pd.DataFrame()
        
        # Save combined results
        output_path = self.results_dir / "all_violations.csv"
        combined_df.to_csv(output_path, index=False)
        logger.info(f"Saved combined results to {output_path}")
        
        # Generate summary by class
        summary_df = self._generate_class_summary(combined_df)
        summary_path = self.results_dir / "analysis_results.csv"
        summary_df.to_csv(summary_path, index=False)
        logger.info(f"Saved analysis summary to {summary_path}")
        
        logger.info("Analysis complete!")
        return summary_df
    
    def _generate_class_summary(self, violations_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate summary by class from violations.
        
        Returns:
            DataFrame with one row per class showing aggregated violations
        """
        if violations_df.empty:
            return pd.DataFrame()
        
        # Group by class
        summary_rows = []
        
        for class_name in violations_df["class_name"].unique():
            class_violations = violations_df[violations_df["class_name"] == class_name]
            
            # Count violations by severity
            severity_counts = class_violations["severity"].value_counts().to_dict()
            
            # Calculate total score (using severity weights)
            total_score = sum(
                self.severity_weights.get(row["severity"], 1) 
                for _, row in class_violations.iterrows()
            )
            
            # Check if it's a God Class candidate (2+ at high/critical)
            high_critical_count = (
                severity_counts.get("high", 0) + 
                severity_counts.get("critical", 0)
            )
            is_god_class = high_critical_count >= 2
            
            summary_rows.append({
                "class_name": class_name,
                "file_path": class_violations.iloc[0]["file_path"],
                "package": class_violations.iloc[0]["package"],
                "repository": class_violations.iloc[0]["repository"],
                "total_violations": len(class_violations),
                "low_violations": severity_counts.get("low", 0),
                "medium_violations": severity_counts.get("medium", 0),
                "high_violations": severity_counts.get("high", 0),
                "critical_violations": severity_counts.get("critical", 0),
                "total_score": total_score,
                "is_god_class_candidate": is_god_class,
                "violated_rules": ", ".join(class_violations["rule_name"].unique())
            })
        
        summary_df = pd.DataFrame(summary_rows)
        summary_df = summary_df.sort_values("total_score", ascending=False)
        
        return summary_df
    
    def _violations_to_dataframe(self, violations: List[Violation]) -> pd.DataFrame:
        """Convert list of Violation objects to DataFrame."""
        if not violations:
            return pd.DataFrame()
        
        return pd.DataFrame([{
            "file_path": v.file_path,
            "class_name": v.class_name,
            "package": v.package,
            "rule_name": v.rule_name,
            "severity": v.severity,
            "metric_name": v.metric_name,
            "metric_value": v.metric_value,
            "threshold": v.threshold,
            "description": v.description,
            "line_number": v.line_number,
            "repository": v.repository
        } for v in violations])


if __name__ == "__main__":
    # Example usage
    import yaml
    
    with open("config.yaml") as f:
        config = yaml.safe_load(f)
    
    analyzer = RuleBasedAnalyzer(config)
    results = analyzer.run_full_analysis()
    
    print(f"\nAnalysis complete!")
    print(f"Total classes analyzed: {len(results)}")
    print(f"God Class candidates: {results['is_god_class_candidate'].sum()}")