# How ML-Based God Class Detection Works

## Overview

This document explains the methodology behind the ML-based God Class detection system, based on state-of-the-art research from 2023-2025.

## Research Foundation

### Key Papers

| Paper | Year | Contribution | Accuracy |
|-------|------|--------------|----------|
| Rao et al. | 2023 | PCA + SMOTE + Random Forest | 99% |
| Dewangan et al. | 2023 | 4-level severity + Chi-square + XGBoost | 99.12% |
| Khleel & Nehéz | 2024 | Bi-LSTM + Data balancing | 97.8% |
| Alkharabsheh et al. | 2025 | Code representation comparison | 94.48% |
| Li et al. | 2024 | O-Bagging for severity ranking | 98.5% |

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ML-BASED GOD CLASS DETECTION                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐    ┌──────────────┐    ┌─────────────┐    ┌────────┐ │
│  │  Java    │───▶│   Metric     │───▶│   Data      │───▶│  ML    │ │
│  │  Files   │    │  Extraction  │    │ Preprocess  │    │ Models │ │
│  └──────────┘    └──────────────┘    └─────────────┘    └────────┘ │
│                         │                   │                │      │
│                         ▼                   ▼                ▼      │
│                  ┌──────────────┐    ┌─────────────┐    ┌────────┐ │
│                  │ CK Metrics   │    │ SMOTE +     │    │ Voting │ │
│                  │ LOC,WMC,CBO  │    │ PCA/Chi²    │    │Ensemble│ │
│                  │ LCOM,NOM...  │    │             │    │        │ │
│                  └──────────────┘    └─────────────┘    └────────┘ │
│                                                                      │
│                              ┌───────────────────────┐              │
│                              │   SEVERITY OUTPUT     │              │
│                              ├───────────────────────┤              │
│                              │ 🟢 NONE - No smell    │              │
│                              │ 🟡 MINOR - Monitor    │              │
│                              │ 🟠 MAJOR - Refactor   │              │
│                              │ 🔴 CRITICAL - Urgent  │              │
│                              └───────────────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

## Phase 1: Metric Extraction

### CK Metrics Suite (Chidamber & Kemerer, 1994)

The foundation of code smell detection is software metrics:

| Metric | Full Name | Description | God Class Indicator |
|--------|-----------|-------------|---------------------|
| **LOC** | Lines of Code | Total lines in class | Size indicator |
| **SLOC** | Source LOC | Non-blank, non-comment | Actual code size |
| **WMC** | Weighted Methods per Class | Sum of method complexities | Complexity |
| **CBO** | Coupling Between Objects | Dependencies on other classes | Coupling |
| **LCOM** | Lack of Cohesion | Methods not sharing fields | Cohesion (inverted) |
| **NOM** | Number of Methods | Count of methods | Size indicator |
| **RFC** | Response for a Class | Methods callable from class | Complexity |
| **DIT** | Depth of Inheritance | Inheritance tree depth | Structure |

### Extraction Process

```python
# Example extraction for a Java file
metrics = {
    'loc': 847,           # Lines of code
    'sloc': 723,          # Source lines
    'wmc': 156,           # Total cyclomatic complexity
    'cyclomatic': 89,     # McCabe complexity
    'cbo': 23,            # Coupled classes
    'lcom': 0.78,         # Low cohesion (high = bad)
    'nom': 47,            # Number of methods
    'noa': 19             # Number of attributes
}
```

## Phase 2: Data Preprocessing

### Problem: Class Imbalance

Real-world code smell datasets are highly imbalanced (Rao et al. 2023):

```
Original Distribution:
┌─────────────────────────────────────────────┐
│ NONE     ████████████████████████████  280  │
│ MINOR    █████                          47  │
│ MAJOR    ███████                        63  │
│ CRITICAL ██                             30  │
└─────────────────────────────────────────────┘
```

### Solution: SMOTE (Synthetic Minority Over-sampling)

Based on Rao et al. (2023), SMOTE generates synthetic samples:

```
After SMOTE:
┌─────────────────────────────────────────────┐
│ NONE     ████████████████████████████  280  │
│ MINOR    ████████████████████████████  280  │
│ MAJOR    ████████████████████████████  280  │
│ CRITICAL ████████████████████████████  280  │
└─────────────────────────────────────────────┘
```

**How SMOTE works:**
1. Select a minority class sample
2. Find k nearest neighbors (k=5)
3. Randomly select one neighbor
4. Create synthetic sample on line between them
5. Repeat until balanced

### Feature Selection: PCA

Principal Component Analysis reduces dimensionality while preserving variance:

```
Original: 17 features → PCA → 10 components (95% variance)

Top Components:
PC1: 0.32 (WMC + LOC combination)
PC2: 0.25 (LCOM + CBO combination)
PC3: 0.18 (NOM + NOA combination)
...
```

## Phase 3: ML Models

### Random Forest (Best Performer)

Based on Rao et al. (2023) and Cluster Computing (2024):

```
Random Forest Configuration:
├── n_estimators: 100
├── max_depth: 15
├── min_samples_split: 5
├── class_weight: balanced
└── Performance: 99%+ accuracy
```

**Why Random Forest works:**
- Handles non-linear relationships
- Built-in feature importance
- Robust to outliers
- No feature scaling required
- Reduces overfitting through bagging

### XGBoost (Second Best)

Based on Dewangan et al. (2023):

```
XGBoost Configuration:
├── n_estimators: 100
├── max_depth: 6
├── learning_rate: 0.1
├── subsample: 0.8
└── Performance: 99.12% accuracy
```

### Voting Ensemble

Combines multiple models for robustness:

```
Ensemble Architecture:
┌────────────────────────────────────────┐
│            Voting Classifier           │
│                                        │
│  ┌──────────┐  ┌──────────┐  ┌──────┐ │
│  │ Random   │  │ XGBoost  │  │ GB   │ │
│  │ Forest   │  │          │  │      │ │
│  │ (40%)    │  │ (35%)    │  │(25%) │ │
│  └────┬─────┘  └────┬─────┘  └──┬───┘ │
│       │             │            │     │
│       └──────┬──────┴────────────┘     │
│              ▼                         │
│       Soft Voting                      │
│    (probability average)               │
└────────────────────────────────────────┘
```

## Phase 4: Severity Classification

### 4-Level System (Dewangan et al. 2023)

| Level | Score | Criteria | Action |
|-------|-------|----------|--------|
| **NONE** | 0 | All metrics below threshold | No action |
| **MINOR** | 1 | 1-2 metrics elevated | Monitor |
| **MAJOR** | 2 | 3+ metrics elevated | Schedule refactoring |
| **CRITICAL** | 3 | Multiple severe violations | Immediate action |

### Threshold Values

Based on empirical studies:

| Metric | NONE | MINOR | MAJOR | CRITICAL |
|--------|------|-------|-------|----------|
| LOC | <200 | 200-500 | 500-1000 | >1000 |
| NOM | <10 | 10-20 | 20-40 | >40 |
| WMC | <30 | 30-60 | 60-100 | >100 |
| CBO | <5 | 5-10 | 10-20 | >20 |
| LCOM | <0.3 | 0.3-0.5 | 0.5-0.7 | >0.7 |

## Feature Importance

From Random Forest analysis:

```
Feature Importance for God Class Detection:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WMC            : 0.1842 ████████████████████
LCOM           : 0.1567 █████████████████
LOC            : 0.1423 ███████████████
CBO            : 0.1289 ██████████████
NOM            : 0.1156 ████████████
Cyclomatic     : 0.0934 ██████████
TCC            : 0.0678 ███████
Fan-out        : 0.0534 ██████
DIT            : 0.0312 ███
NOA            : 0.0265 ███
```

**Key Insight:** WMC (Weighted Methods per Class) and LCOM (Lack of Cohesion) are the strongest predictors, supporting the theoretical definition of God Class as a class with too many responsibilities (high WMC) and low cohesion (high LCOM).

## Comparison with Rule-Based Approaches

| Aspect | Rule-Based | ML-Based |
|--------|------------|----------|
| **Accuracy** | 72-82% | 99%+ |
| **Speed** | <1 second | 2-5 seconds |
| **Transparency** | High | Medium (with LIME) |
| **Adaptability** | Low (fixed rules) | High (learns patterns) |
| **Training Data** | Not required | Required |
| **Novel Cases** | Poor | Good |
| **False Positives** | Higher | Lower |

## Usage Examples

### Basic Usage

```python
from src.models.ml_classifier import SeverityClassifier
from src.feature_extraction.metric_extractor import MetricExtractor

# Extract metrics
extractor = MetricExtractor()
metrics = extractor.extract_metrics_from_file("MyClass.java")

# Classify
classifier = SeverityClassifier()
classifier.load_model("trained_model.pkl")
result = classifier.classify_file(metrics.to_dict())

print(f"Severity: {result.predicted_severity}")
print(f"Confidence: {result.confidence}%")
print(f"Is God Class: {result.is_god_class}")
```

### Training Custom Model

```python
from src.models.ml_classifier import SeverityClassifier
from src.preprocessing.data_balancer import DataBalancer

# Load your labeled data
X, y = load_training_data()

# Balance data
balancer = DataBalancer(method='smote')
X_balanced, y_balanced = balancer.balance(X, y)

# Train
classifier = SeverityClassifier()
performances = classifier.train(X_balanced, y_balanced, feature_names)

# Save
classifier.save_model("my_model.pkl")
```

## References

1. Rao, R.S., et al. (2023). "A study of dealing class imbalance problem with machine learning methods for code smell severity detection using PCA-based feature selection technique." *Scientific Reports* 13, 16245.

2. Dewangan, S., et al. (2023). "Severity Classification of Code Smells Using Machine-Learning Methods." *SN Computer Science* 4, 779.

3. Khleel, N.A.A., Nehéz, K. (2024). "Improving accuracy of code smells detection using machine learning with data balancing techniques." *The Journal of Supercomputing* 80.

4. Alkharabsheh, K., et al. (2025). "From code to insight: studying code representation techniques for ML-based God class detection." *Automated Software Engineering*.

5. Li, Y., et al. (2024). "Revisiting Code Smell Severity Prioritization using learning to rank techniques." *Expert Systems with Applications*.

6. Chidamber, S.R., Kemerer, C.F. (1994). "A metrics suite for object oriented design." *IEEE TSE*.

7. Fontana, F.A., Zanoni, M. (2017). "Code smell severity classification using machine learning techniques." *Knowledge-Based Systems* 128.
