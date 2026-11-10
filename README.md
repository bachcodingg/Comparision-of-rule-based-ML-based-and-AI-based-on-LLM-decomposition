# God Class Detection & Decomposition — Complete Project v2.1

## BSc Thesis: Comparing Rule-Based, ML, and AI-Agent Approaches
**Author:** Vo Gia Bach | **LUT University** | **2026** | **Examiner:** Jussi Kasurinen

---

## What This Project Does (Plain English)

When software grows over years, some code files become too big and messy — doing hundreds of unrelated things in one place. Programmers call these "God Classes." They make software harder to fix and more likely to break.

This project tests three ways to find messy files automatically: (1) simple rules that check if a file is too big, (2) machine learning that learns patterns from examples, and (3) AI chatbots that read the code and give advice. No single method works best everywhere, so the solution is to use all three together.

---

## Quick Start

```bash
# Rule-based pipeline
cd rule-based-java-decomposition
pip install -r requirements.txt
python run_pipeline_v2.py --demo

# ML pipeline (v2.1)
cd ../ml-based-java-decomposition
pip install -r requirements.txt
python run_pipeline_v2.py --demo

# Scan an entire Java project
python run_pipeline_v2.py --scan /path/to/java/project
```

## Prerequisites

- Python 3.10+ (tested on 3.11)
- Git (for cloning validation repos)
- Java 17+ (optional — only needed for PMD in rule-based pipeline)
- Docker (optional — for reproducible execution)

## Installation

```bash
# Rule-Based (16 tests)
cd rule-based-java-decomposition
pip install -r requirements.txt
pytest tests/ -v

# ML (27 tests)
cd ../ml-based-java-decomposition
pip install -r requirements.txt
pytest tests/ -v
```

## ML Pipeline v2.1 — 10-Step Process

| Step | Name | What happens |
|---|---|---|
| 1 | Metric Extraction | AST-based parsing → 11 features (8 base + 3 derived) |
| 2 | Data Preprocessing | 2000 correlated synthetic samples, SMOTE, PCA |
| 3 | Model Training | RF, XGBoost, GB, SVM + stacking ensemble + Platt calibration |
| 4 | Classification | Classify files with calibrated confidence scores |
| 5 | Feature Importance | Random Forest importance rankings |
| 6 | Visualization | 6 thesis-quality figures |
| 7 | Save Results | JSON exports of all metrics, predictions, models |
| 8 | **Decomposition** | ML-informed decomposition plans + Extract Class code generation |
| 9 | **Dashboard** | 6 model comparison figures (confusion, calibration, radar) |
| 10 | **Sensitivity** | Threshold perturbation analysis with thesis-ready text |

## Project Structure

```
rule-based-java-decomposition/          ~6,200 lines, 22 modules
  src/analyzer/                         Rule evaluation + priority scoring
  src/decomposer/                       Extract Class code generation
  src/metrics/                          AST + regex metric extraction

ml-based-java-decomposition/            ~5,400 lines, 27 modules
  src/feature_extraction/               AST + regex metric extraction
  src/models/                           Stacking classifier + calibration
  src/preprocessing/                    SMOTE + PCA
  src/evaluation/                       Statistical eval + sensitivity analysis
  src/decomposer/                       ML decomposition recommender (NEW)
  src/scanner/                          Batch repository scanner (NEW)
  src/visualization/                    Charts + model dashboard (NEW)
```

## ML v2.1 New Features

- **ML Decomposer** (~850 lines): Root cause analysis, responsibility clustering, Extract Class code generation
- **Repository Scanner** (~385 lines): Batch scan projects with confidence-prioritized reporting
- **Model Dashboard** (~355 lines): Confusion matrices, calibration curves, radar chart
- **Sensitivity Analysis** (~280 lines): Threshold perturbation ±30%, stability assessment
- **Docker Config**: Dockerfile + docker-compose matching rule-based project
- **Stacking Ensemble**: Replaces simple voting with meta-learner
- **Platt Calibration**: Meaningful confidence scores
- **Derived Features**: method_density, avg_method_size, fields_per_method

## Scanning a Java Repository

```bash
python run_pipeline_v2.py --scan /path/to/java/project
# Results: results/scan_results.csv and scan_results.json
```

## Analyzing New Files

```bash
cp YourClass.java ml-based-java-decomposition/data/sample/
cd ml-based-java-decomposition && python run_pipeline_v2.py --demo
```

## Common Errors

| Error | Fix |
|---|---|
| ModuleNotFoundError: javalang | pip install javalang (falls back to regex) |
| ModuleNotFoundError: xgboost | pip install xgboost (uses 3 models without it) |
| Java/PMD not found | Optional — use Docker for full setup |
| AST parsing failed | Normal — automatic regex fallback |

## Manual Tasks Still Required

1. **Inter-Rater Reliability**: Send evaluation_package/ to classmate, run task3_inter_rater.py
2. **Multi-Trial AI Evaluation**: Run task2_ai_agent_eval.py with API keys (~$3.75)
3. **Page Count Check**: Verify "46 pages" in both abstracts matches actual page count
