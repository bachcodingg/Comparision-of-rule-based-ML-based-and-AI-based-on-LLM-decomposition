# ML pipeline

Classifies a Java class into NONE / MINOR / MAJOR / CRITICAL from seven metrics
(LOC, SLOC, WMC, CBO, LCOM, NOM, NOA) with Random Forest, XGBoost, Gradient Boosting, an RBF SVM
and a soft-voting ensemble of the three tree models.

```bash
pip install -r requirements.txt
python run_pipeline.py --demo                 # train, classify the classes in ../../dataset/blind
python run_pipeline.py --demo --smote --pca   # with SMOTE oversampling and PCA (95% variance)
python run_pipeline.py --demo --sample-dir /path/to/java/files
```

## What the numbers mean

The training data is synthetic. `generate_synthetic_training_data` in `src/models/ml_classifier.py`
draws each sample from a hand-chosen range box for one severity level and labels it with that
level. Hold-out accuracy (about 96-100%) therefore measures how well a model recovers those boxes.
It is not an estimate of accuracy on real code, and feature importances describe the boxes, not
God Classes. The ranges were adjusted during development while the six sample classes were being
classified, so those classes are not an independent test set either.

Metrics come from `common/java_metrics.py` at the repository root, the same extractor the
rule-based pipeline uses. Seeds are fixed at 42. Results for the thesis are produced by
`python evaluate.py` in the repository root.

To make this pipeline evidence about real code, replace the generator with labelled data, for
example the Blob reviews in the MLCQ dataset, which use the same four severity levels.
