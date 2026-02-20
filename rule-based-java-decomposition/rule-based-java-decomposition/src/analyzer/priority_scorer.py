#!/usr/bin/env python3
"""
Priority Scoring Module for Java Class Decomposition
Updated: January 2026

This module calculates priority scores for Java classes using a severity-based
approach validated by recent empirical research (2022-2023).

SEVERITY-BASED PRIORITY SCORING
================================

Instead of normalizing metrics, this approach assigns severity levels (1-4) to
each metric based on empirically validated thresholds, then calculates a weighted
priority score.

Formula:
    Priority = Sum (Severity_Level x Metric_Weight)

Where:
    Severity_Level in {1=Low, 2=Medium, 3=High, 4=Critical}
    
    Metric_Weights:
        LOC:  0.25  (size is fundamental indicator)
        WMC:  0.25  (complexity drives maintenance cost)
        CBO:  0.20  (coupling affects change propagation)
        LCOM: 0.15  (cohesion indicates separation quality)
        NOM:  0.15  (method count reflects behavioral complexity)

Priority Score Range: 0.0 - 4.0
    0.0-1.0: LOW      - No immediate action needed
    1.0-2.0: MEDIUM   - Monitor for growth
    2.0-3.0: HIGH     - Refactor when time permits
    3.0-4.0: CRITICAL - Urgent refactoring required

RESEARCH FOUNDATION
===================

This approach is based on recent empirical studies:

1. Dewangan, S., et al. (2023). "Severity Classification of Code Smells Using 
   Machine-Learning Methods." SN Computer Science, 4, 564.
   - Introduced 4-level severity classification (Low/Medium/High/Critical)
   - Validated on God Class, Data Class, Feature Envy, Long Method
   - Provides LOC, NOM, CBO thresholds

2. Verma, V., et al. (2023). "Code smell prioritization in object‐oriented 
   software systems: A systematic literature review." Journal of Software: 
   Evolution and Process, e2536.
   - Systematic review of prioritization strategies
   - Recommends severity-based ranking for limited resources
   - Discusses practical threshold derivation methods

3. Rao, R.S., et al. (2023). "A study of dealing class imbalance problem with 
   machine learning methods for code smell severity detection using PCA-based 
   feature selection technique." Scientific Reports, 13, 16245.
   - Defines 4-level severity for LCOM metric
   - Achieves 83-99% accuracy on Fontana's datasets
   - Validates threshold effectiveness

4. Gupta, A., & Chauhan, N.K. (2022). "A severity-based classification 
   assessment of code smells in Kotlin and Java application." Arabian Journal 
   for Science and Engineering, 47:1831–1848.
   - Java-specific threshold validation
   - Multi-level severity for WMC metric
   - Statistical analysis on real projects

THRESHOLD VALUES
================

All threshold values are from the above empirical studies:

LOC (Lines of Code):
    Low: 1-200      (Dewangan et al., 2023)
    Medium: 201-500 (Rao et al., 2023)
    High: 501-1000
    Critical: >1000

NOM (Number of Methods):
    Low: 1-10       (Dewangan et al., 2023)
    Medium: 11-20
    High: 21-40
    Critical: >40

WMC (Weighted Methods per Class):
    Low: 1-30       (Gupta & Chauhan, 2022)
    Medium: 31-60   (Verma et al., 2023)
    High: 61-100
    Critical: >100

CBO (Coupling Between Objects):
    Low: 1-5        (Dewangan et al., 2023)
    Medium: 6-10
    High: 11-20
    Critical: >20

LCOM (Lack of Cohesion of Methods):
    Low: 0.0-0.4    (Rao et al., 2023)
    Medium: 0.41-0.7 (Gupta & Chauhan, 2022)
    High: 0.71-0.9
    Critical: >0.9

EXAMPLE CALCULATION
===================

Class: UserService.java
    LOC: 850     -> HIGH (3)       x 0.25 = 0.75
    NOM: 45      -> CRITICAL (4)   x 0.15 = 0.60
    WMC: 120     -> CRITICAL (4)   x 0.25 = 1.00
    CBO: 8       -> MEDIUM (2)     x 0.20 = 0.40
    LCOM: 0.75   -> HIGH (3)       x 0.15 = 0.45
    
    Priority = 0.75 + 0.60 + 1.00 + 0.40 + 0.45 = 3.20 (CRITICAL)

Author: Rule-Based Java Decomposition Project
License: MIT
Version: 2.0 (Updated with Research from 2022-2023)
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

import pandas as pd

logger = logging.getLogger(__name__)


class SeverityLevel(Enum):
    """Severity levels for metrics (from recent research)."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class SeverityThresholds:
    """
    Severity thresholds for each metric.
    Based on empirical research (Dewangan et al. 2023, Rao et al. 2023, 
    Gupta & Chauhan 2022, Verma et al. 2023).
    """
    # LOC thresholds (Dewangan et al. 2023, Rao et al. 2023)
    loc_low: int = 200
    loc_medium: int = 500
    loc_high: int = 1000
    
    # NOM thresholds (Dewangan et al. 2023)
    nom_low: int = 10
    nom_medium: int = 20
    nom_high: int = 40
    
    # WMC thresholds (Gupta & Chauhan 2022, Verma et al. 2023)
    wmc_low: int = 30
    wmc_medium: int = 60
    wmc_high: int = 100
    
    # CBO thresholds (Dewangan et al. 2023)
    cbo_low: int = 5
    cbo_medium: int = 10
    cbo_high: int = 20
    
    # LCOM thresholds (Rao et al. 2023, Gupta & Chauhan 2022)
    lcom_low: float = 0.4
    lcom_medium: float = 0.7
    lcom_high: float = 0.9


@dataclass
class MetricWeights:
    """
    Weights for combining severity scores.
    Based on impact on maintainability (Verma et al. 2023).
    """
    loc: float = 0.25   # Size is fundamental
    wmc: float = 0.25   # Complexity drives maintenance
    cbo: float = 0.20   # Coupling affects change propagation
    lcom: float = 0.15  # Cohesion indicates separation needs
    nom: float = 0.15   # Method count reflects behavioral complexity
    
    def validate(self) -> bool:
        """Validate that weights sum to 1.0."""
        total = self.loc + self.wmc + self.cbo + self.lcom + self.nom
        return abs(total - 1.0) < 0.001
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'loc': self.loc,
            'wmc': self.wmc,
            'cbo': self.cbo,
            'lcom': self.lcom,
            'nom': self.nom
        }


class SeverityBasedScorer:
    """
    Calculates priority scores using severity-based approach.
    
    This scorer assigns severity levels (1-4) to each metric based on
    empirically validated thresholds, then calculates weighted priority.
    
    Example usage:
        scorer = SeverityBasedScorer()
        score, details = scorer.calculate_priority(metrics={
            'loc': 850, 'nom': 45, 'wmc': 120, 'cbo': 8, 'lcom': 0.75
        })
        print(f"Priority: {score:.2f} ({details['priority_label']})")
    """
    
    def __init__(self, 
                 thresholds: Optional[SeverityThresholds] = None,
                 weights: Optional[MetricWeights] = None):
        """
        Initialize the severity-based scorer.
        
        Args:
            thresholds: Custom severity thresholds (uses research-based defaults)
            weights: Custom metric weights (uses Verma et al. 2023 defaults)
        """
        self.thresholds = thresholds or SeverityThresholds()
        self.weights = weights or MetricWeights()
        
        if not self.weights.validate():
            logger.warning("Metric weights do not sum to 1.0")
        
        logger.info(f"Initialized SeverityBasedScorer with weights: {self.weights.to_dict()}")
    
    def get_severity_level(self, value: float, metric: str) -> SeverityLevel:
        """
        Determine severity level for a metric value.
        
        Args:
            value: Metric value
            metric: Metric name ('loc', 'nom', 'wmc', 'cbo', 'lcom')
            
        Returns:
            SeverityLevel enum
        """
        if metric == 'loc':
            if value <= self.thresholds.loc_low:
                return SeverityLevel.LOW
            elif value <= self.thresholds.loc_medium:
                return SeverityLevel.MEDIUM
            elif value <= self.thresholds.loc_high:
                return SeverityLevel.HIGH
            else:
                return SeverityLevel.CRITICAL
                
        elif metric == 'nom':
            if value <= self.thresholds.nom_low:
                return SeverityLevel.LOW
            elif value <= self.thresholds.nom_medium:
                return SeverityLevel.MEDIUM
            elif value <= self.thresholds.nom_high:
                return SeverityLevel.HIGH
            else:
                return SeverityLevel.CRITICAL
                
        elif metric == 'wmc':
            if value <= self.thresholds.wmc_low:
                return SeverityLevel.LOW
            elif value <= self.thresholds.wmc_medium:
                return SeverityLevel.MEDIUM
            elif value <= self.thresholds.wmc_high:
                return SeverityLevel.HIGH
            else:
                return SeverityLevel.CRITICAL
                
        elif metric == 'cbo':
            if value <= self.thresholds.cbo_low:
                return SeverityLevel.LOW
            elif value <= self.thresholds.cbo_medium:
                return SeverityLevel.MEDIUM
            elif value <= self.thresholds.cbo_high:
                return SeverityLevel.HIGH
            else:
                return SeverityLevel.CRITICAL
                
        elif metric == 'lcom':
            if value <= self.thresholds.lcom_low:
                return SeverityLevel.LOW
            elif value <= self.thresholds.lcom_medium:
                return SeverityLevel.MEDIUM
            elif value <= self.thresholds.lcom_high:
                return SeverityLevel.HIGH
            else:
                return SeverityLevel.CRITICAL
        
        else:
            logger.warning(f"Unknown metric: {metric}, defaulting to LOW")
            return SeverityLevel.LOW
    
    def calculate_priority(self, metrics: Dict[str, float]) -> tuple[float, Dict]:
        """
        Calculate priority score for a class.
        
        Args:
            metrics: Dictionary with keys: loc, nom, wmc, cbo, lcom
            
        Returns:
            Tuple of (priority_score, details_dict)
            - priority_score: Float between 0.0 and 4.0
            - details_dict: Breakdown of calculation
        """
        # Get metric values (with defaults)
        loc = metrics.get('loc', 0)
        nom = metrics.get('nom', 0)
        wmc = metrics.get('wmc', 0)
        cbo = metrics.get('cbo', 0)
        lcom = metrics.get('lcom', 0.0)
        
        # Determine severity levels
        severities = {
            'loc': self.get_severity_level(loc, 'loc'),
            'nom': self.get_severity_level(nom, 'nom'),
            'wmc': self.get_severity_level(wmc, 'wmc'),
            'cbo': self.get_severity_level(cbo, 'cbo'),
            'lcom': self.get_severity_level(lcom, 'lcom')
        }
        
        # Calculate weighted score
        score = 0.0
        contributions = {}
        
        for metric, severity in severities.items():
            weight = getattr(self.weights, metric)
            contribution = severity.value * weight
            score += contribution
            contributions[metric] = {
                'value': metrics.get(metric, 0),
                'severity': severity.name,
                'severity_score': severity.value,
                'weight': weight,
                'contribution': contribution
            }
        
        # Determine priority label
        if score < 1.0:
            priority_label = "LOW"
            recommendation = "No immediate action needed"
        elif score < 2.0:
            priority_label = "MEDIUM"
            recommendation = "Monitor for growth"
        elif score < 3.0:
            priority_label = "HIGH"
            recommendation = "Refactor when time permits"
        else:
            priority_label = "CRITICAL"
            recommendation = "Urgent refactoring required"
        
        # Count severity levels
        severity_counts = {
            'low': sum(1 for s in severities.values() if s == SeverityLevel.LOW),
            'medium': sum(1 for s in severities.values() if s == SeverityLevel.MEDIUM),
            'high': sum(1 for s in severities.values() if s == SeverityLevel.HIGH),
            'critical': sum(1 for s in severities.values() if s == SeverityLevel.CRITICAL)
        }
        
        # Check God Class detection rule (2+ metrics at HIGH/CRITICAL)
        high_critical_count = severity_counts['high'] + severity_counts['critical']
        is_god_class_candidate = high_critical_count >= 2
        
        details = {
            'priority_score': round(score, 2),
            'priority_label': priority_label,
            'recommendation': recommendation,
            'is_god_class_candidate': is_god_class_candidate,
            'severity_counts': severity_counts,
            'contributions': contributions,
            'metrics': metrics,
            'weights': self.weights.to_dict()
        }
        
        return round(score, 2), details
    
    def rank_classes(self, metrics_df: pd.DataFrame) -> pd.DataFrame:
        """
        Rank all classes by priority score.
        
        Args:
            metrics_df: DataFrame with columns: class_name, loc, nom, wmc, cbo, lcom
            
        Returns:
            DataFrame with added columns: priority_score, priority_label, 
            is_god_class_candidate, rank
        """
        result_df = metrics_df.copy()
        
        # Calculate priority for each class
        priorities = []
        labels = []
        is_god_class = []
        recommendations = []
        
        for _, row in metrics_df.iterrows():
            metrics = {
                'loc': row.get('loc', row.get('LOC', 0)),
                'nom': row.get('nom', row.get('NOM', 0)),
                'wmc': row.get('wmc', row.get('WMC', 0)),
                'cbo': row.get('cbo', row.get('CBO', 0)),
                'lcom': row.get('lcom', row.get('LCOM', 0.0))
            }
            
            score, details = self.calculate_priority(metrics)
            priorities.append(score)
            labels.append(details['priority_label'])
            is_god_class.append(details['is_god_class_candidate'])
            recommendations.append(details['recommendation'])
        
        result_df['priority_score'] = priorities
        result_df['priority_label'] = labels
        result_df['is_god_class_candidate'] = is_god_class
        result_df['recommendation'] = recommendations
        
        # Sort by priority descending and add rank
        result_df = result_df.sort_values('priority_score', ascending=False)
        result_df['rank'] = range(1, len(result_df) + 1)
        
        return result_df
    
    def get_decomposition_candidates(self,
                                     metrics_df: pd.DataFrame,
                                     min_priority: str = 'HIGH') -> pd.DataFrame:
        """
        Get classes that are candidates for decomposition.
        
        Args:
            metrics_df: DataFrame with class metrics
            min_priority: Minimum priority level ('HIGH' or 'CRITICAL')
            
        Returns:
            DataFrame with decomposition candidates
        """
        ranked = self.rank_classes(metrics_df)
        
        if min_priority.upper() == 'CRITICAL':
            candidates = ranked[ranked['priority_label'] == 'CRITICAL']
        else:  # HIGH or above
            candidates = ranked[ranked['priority_label'].isin(['HIGH', 'CRITICAL'])]
        
        return candidates
    
    def explain_priority(self, metrics: Dict[str, float]) -> str:
        """
        Generate human-readable explanation of priority calculation.
        
        Args:
            metrics: Dictionary with metric values
            
        Returns:
            Multi-line string explaining the calculation
        """
        score, details = self.calculate_priority(metrics)
        
        explanation = []
        explanation.append(f"Priority Score: {score:.2f} ({details['priority_label']})")
        explanation.append(f"Recommendation: {details['recommendation']}")
        explanation.append(f"God Class Candidate: {'Yes' if details['is_god_class_candidate'] else 'No'}")
        explanation.append("")
        explanation.append("Metric Breakdown:")
        
        for metric, contrib in details['contributions'].items():
            explanation.append(
                f"  {metric.upper():5s}: {contrib['value']:6.1f} -> "
                f"{contrib['severity']:8s} (score={contrib['severity_score']}) x "
                f"weight={contrib['weight']:.2f} = {contrib['contribution']:.2f}"
            )
        
        explanation.append("")
        explanation.append("Severity Distribution:")
        for level, count in details['severity_counts'].items():
            explanation.append(f"  {level.capitalize():8s}: {count} metrics")
        
        return "\n".join(explanation)


# Backward compatibility alias
PriorityScorer = SeverityBasedScorer


def create_scorer(weights: Optional[Dict[str, float]] = None) -> SeverityBasedScorer:
    """
    Factory function to create a scorer.
    
    Args:
        weights: Custom metric weights (optional)
        
    Returns:
        Configured SeverityBasedScorer instance
    """
    if weights:
        metric_weights = MetricWeights(**weights)
        return SeverityBasedScorer(weights=metric_weights)
    
    return SeverityBasedScorer()


if __name__ == "__main__":
    # Demonstration
    print("=" * 70)
    print("SEVERITY-BASED PRIORITY SCORING DEMONSTRATION")
    print("Based on Research: Dewangan et al. (2023), Verma et al. (2023),")
    print("                   Rao et al. (2023), Gupta & Chauhan (2022)")
    print("=" * 70)
    
    scorer = SeverityBasedScorer()
    
    # Example 1: UserService (from case study)
    print("\n### Example 1: UserService.java ###")
    metrics1 = {
        'loc': 850,
        'nom': 45,
        'wmc': 120,
        'cbo': 8,
        'lcom': 0.75
    }
    print(scorer.explain_priority(metrics1))
    
    # Example 2: Well-designed class
    print("\n" + "=" * 70)
    print("\n### Example 2: ProductCatalog.java (Well-Designed) ###")
    metrics2 = {
        'loc': 180,
        'nom': 12,
        'wmc': 25,
        'cbo': 4,
        'lcom': 0.35
    }
    print(scorer.explain_priority(metrics2))
    
    # Example 3: Borderline case
    print("\n" + "=" * 70)
    print("\n### Example 3: DataManager.java (Borderline) ###")
    metrics3 = {
        'loc': 450,
        'nom': 28,
        'wmc': 65,
        'cbo': 12,
        'lcom': 0.52
    }
    print(scorer.explain_priority(metrics3))
    
    print("\n" + "=" * 70)
    print("Priority Score Interpretation:")
    print("  0.0-1.0: LOW      - No action needed")
    print("  1.0-2.0: MEDIUM   - Monitor for growth")
    print("  2.0-3.0: HIGH     - Refactor when possible")
    print("  3.0-4.0: CRITICAL - Urgent refactoring")
    print("=" * 70)