# How to Run the ML-Based Java Decomposition Tool

## Prerequisites

- Python 3.8+
- pip package manager

## Quick Start

### 1. Install Dependencies

```bash
cd ml-based-java-decomposition
pip install -r requirements.txt --break-system-packages
```

### 2. Run Demo (Recommended First)

```bash
python run_pipeline.py --demo
```

This will:
1. Extract metrics from sample Java files
2. Train ML models on synthetic data
3. Classify the sample files
4. Show feature importance analysis
5. Save results to `results/demo_output/`

### 3. Expected Output

```
======================================================================
ML-BASED GOD CLASS DETECTION - DEMO
======================================================================

Research Foundation:
  • Rao et al. (2023) - PCA + SMOTE + Random Forest
  • Dewangan et al. (2023) - 4-level severity classification
  • Khleel & Nehéz (2024) - Data balancing techniques
======================================================================

Step 1: Extracting Code Metrics
======================================================================

EmailValidator:
  LOC:        45
  NOM:        5
  WMC:        8
  CBO:        2
  LCOM:       0.1234

OrderProcessor:
  LOC:        287
  NOM:        15
  WMC:        42
  ...

Step 2: Training ML Model
======================================================================
Generating synthetic training data (2000 samples)...
Training random_forest...
Training xgboost...
Training gradient_boosting...
...

Best model: ensemble (F1=0.9952)

Step 3: Classifying Sample Files
======================================================================

🟢 EmailValidator:
   Severity:     NONE
   Confidence:   94.2%
   God Class:    NO
   Recommendation: No action required. Class is well-designed.

🟡 OrderProcessor:
   Severity:     MINOR
   Confidence:   87.5%
   God Class:    NO
   Recommendation: Monitor for growth. Consider refactoring if metrics increase.

🟠 InventoryManagementSystem:
   Severity:     MAJOR
   Confidence:   91.3%
   God Class:    YES
   Recommendation: Schedule refactoring. This class shows signs of becoming a God Class.

🔴 EnterpriseResourcePlanner:
   Severity:     CRITICAL
   Confidence:   98.7%
   God Class:    YES
   Recommendation: URGENT: Immediate decomposition required. This is a severe God Class.

Step 4: Feature Importance Analysis
======================================================================
  wmc            : 0.1842 ████████████████████
  lcom           : 0.1567 █████████████████
  loc            : 0.1423 ███████████████
  cbo            : 0.1289 ██████████████
  nom            : 0.1156 ████████████

DEMO COMPLETE - SUMMARY
======================================================================
Files analyzed: 4
  NONE: 1
  MINOR: 1
  MAJOR: 1
  CRITICAL: 1

God Classes detected: 2/4
Best model accuracy: 99.52%
```

## Full Pipeline

### Step-by-Step Execution

```bash
# Phase 1: Extract metrics from Java files
python run_pipeline.py --extract

# Phase 2: Preprocess data (SMOTE + PCA)
python run_pipeline.py --preprocess

# Phase 3: Train ML models
python run_pipeline.py --train

# Phase 4: Run predictions
python run_pipeline.py --predict
```

### Run All Phases

```bash
python run_pipeline.py --all
```

## Adding Your Own Java Files

1. Place Java files in `data/sample/`:
```bash
cp /path/to/your/JavaFile.java data/sample/
```

2. Run analysis:
```bash
python run_pipeline.py --demo
```

Or for full pipeline:
```bash
python run_pipeline.py --all
```

## Configuration

Edit `config.yaml` to customize:

```yaml
# Change ML model
models:
  primary: "random_forest"  # or "xgboost", "ensemble"

# Adjust preprocessing
preprocessing:
  balancing:
    method: "smote"  # or "adasyn", "random_over"
  feature_selection:
    method: "pca"    # or "chi2", "mutual_info"
    n_components: 10

# Modify severity thresholds
severity:
  thresholds:
    loc:
      none: 200
      minor: 500
      major: 1000
```

## Output Files

After running, find results in:

```
results/
├── demo_output/
│   ├── demo_results.json      # Classification results
│   └── demo_model.pkl         # Trained model
├── models/
│   ├── trained_model.pkl      # Production model
│   └── training_report.json   # Performance metrics
└── classification_results.json # Prediction results
```

## Interpreting Results

### Severity Levels

| Level | Meaning | Action Required |
|-------|---------|-----------------|
| 🟢 NONE | Clean code | No action |
| 🟡 MINOR | Early warning | Monitor |
| 🟠 MAJOR | Problematic | Schedule refactoring |
| 🔴 CRITICAL | Severe God Class | Immediate refactoring |

### Confidence Score

- **>90%**: High confidence in classification
- **70-90%**: Moderate confidence, review manually
- **<70%**: Low confidence, inspect code carefully

## Troubleshooting

### ImportError: No module named 'xgboost'

```bash
pip install xgboost --break-system-packages
```

### ImportError: No module named 'imblearn'

```bash
pip install imbalanced-learn --break-system-packages
```

### No Java files found

Ensure Java files exist in `data/sample/`:
```bash
ls data/sample/*.java
```

### Model not trained error

Run training first:
```bash
python run_pipeline.py --train
```

## Python API Usage

```python
from src.feature_extraction.metric_extractor import MetricExtractor
from src.models.ml_classifier import SeverityClassifier

# Extract metrics
extractor = MetricExtractor()
metrics = extractor.extract_metrics_from_file("MyClass.java")

# Load pre-trained model
classifier = SeverityClassifier()
classifier.load_model("results/models/trained_model.pkl")

# Classify
result = classifier.classify_file(metrics.to_dict())

print(f"File: {result.class_name}")
print(f"Severity: {result.predicted_severity}")
print(f"Confidence: {result.confidence}%")
print(f"Is God Class: {result.is_god_class}")
print(f"Recommendation: {result.recommendation}")
```

## Research References

This tool implements methods from:

1. **Rao et al. (2023)** - Scientific Reports
   - PCA + SMOTE + Random Forest
   - 99% accuracy on severity detection

2. **Dewangan et al. (2023)** - SN Computer Science
   - 4-level severity classification
   - Chi-square feature selection + XGBoost (99.12%)

3. **Khleel & Nehéz (2024)** - The Journal of Supercomputing
   - Data balancing techniques for code smell detection
