# ML-Based Java Class Decomposition

A machine learning tool for detecting and classifying God Class code smells in Java, based on state-of-the-art research (2023-2025).

## Research Foundation

| Paper | Method | Accuracy |
|-------|--------|----------|
| Rao et al. (2023) | PCA + SMOTE + Random Forest | 99% |
| Dewangan et al. (2023) | Chi-square + XGBoost | 99.12% |
| Khleel & Nehéz (2024) | Data balancing + Deep Learning | 97.8% |

## Quick Start

```bash
pip install -r requirements.txt --break-system-packages
python run_pipeline.py --demo
```

## Features

- **4-Level Severity**: NONE → MINOR → MAJOR → CRITICAL
- **Multiple ML Models**: Random Forest, XGBoost, Gradient Boosting, Ensemble
- **Data Balancing**: SMOTE for class imbalance
- **Feature Selection**: PCA, Chi-square
- **17+ Code Metrics**: LOC, WMC, CBO, LCOM, NOM, etc.

## Project Structure

```
ml-based-java-decomposition/
├── run_pipeline.py              # Main entry point
├── config.yaml                  # Configuration
├── src/
│   ├── feature_extraction/
│   │   └── metric_extractor.py  # Extract code metrics
│   ├── models/
│   │   └── ml_classifier.py     # ML classifiers
│   └── preprocessing/
│       ├── data_balancer.py     # SMOTE balancing
│       └── feature_selector.py  # PCA/Chi-square
├── data/sample/                 # Sample Java files
└── results/                     # Output files
```

## Pipeline Commands

```bash
python run_pipeline.py --demo        # Run demo
python run_pipeline.py --all         # Full pipeline
python run_pipeline.py --extract     # Extract metrics only
python run_pipeline.py --train       # Train models only
python run_pipeline.py --predict     # Predict only
```

## References

1. Rao et al. (2023). Scientific Reports. DOI: 10.1038/s41598-023-43380-8
2. Dewangan et al. (2023). SN Computer Science. DOI: 10.1007/s42979-023-01979-8
