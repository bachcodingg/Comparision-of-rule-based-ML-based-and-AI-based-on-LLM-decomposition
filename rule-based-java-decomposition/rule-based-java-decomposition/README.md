# Rule-based pipeline

Rates a Java class from five metrics and drafts an Extract Class decomposition.

```bash
pip install -r requirements.txt
python run_pipeline.py --demo        # one class from ../../dataset/blind, step by step
python -m pytest tests -q            # 10 tests
```

## Severity score

Each metric is mapped to a level 1-4 (`src/analyzer/priority_scorer.py`):

| Metric | LOW (1) | MEDIUM (2) | HIGH (3) | CRITICAL (4) | Weight |
|---|---|---|---|---|---|
| LOC | <= 200 | <= 500 | <= 1000 | > 1000 | 0.25 |
| WMC | <= 30 | <= 60 | <= 100 | > 100 | 0.25 |
| CBO | <= 5 | <= 10 | <= 20 | > 20 | 0.20 |
| LCOM | <= 0.4 | <= 0.7 | <= 0.9 | > 0.9 | 0.15 |
| NOM | <= 10 | <= 20 | <= 40 | > 40 | 0.15 |

The priority score is the weighted sum (1.0-4.0) and the label is the nearest level
(< 1.5 LOW, < 2.5 MEDIUM, < 3.5 HIGH, otherwise CRITICAL). A class is flagged as a God Class
candidate when at least two metrics are HIGH or CRITICAL.

The thresholds and weights were chosen by the author with reference to the severity cut-offs
discussed in the code-smell literature. They have not been calibrated or validated on a labelled
dataset.

## Decomposition

`src/decomposer/decomposer.py` groups methods that share fields (Jaccard similarity above 0.3) and
writes one class per group plus a modified original. This is a draft: on the six evaluation
classes it produces output for four, none of which compiles, and it finds no grouping for the
largest class. See section 4 of `results/evaluation.md` in the repository root.

`src/decomposer/enhanced_decomposer.py` is an earlier experiment using different metrics (WMC,
ATFD, TCC). It is not used by the pipeline or the thesis.

The `--collect`, `--extract`, `--analyze` phases clone and scan open-source repositories listed in
`config.yaml`. They have not been used to produce any reported result; there is no labelled ground
truth for those repositories in this project.
