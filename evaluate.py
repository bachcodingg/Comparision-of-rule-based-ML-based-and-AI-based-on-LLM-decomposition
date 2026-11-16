#!/usr/bin/env python3
"""
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import math
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RULE = ROOT / "rule-based-java-decomposition" / "rule-based-java-decomposition"
ML = ROOT / "ml-based-java-decomposition" / "ml-based-java-decomposition"
for p in (ML / "src", RULE / "src", ROOT):
    sys.path.insert(0, str(p))

from common.java_metrics import extract_metrics  # noqa: E402
from analyzer.priority_scorer import SeverityBasedScorer, priority_label_for  # noqa: E402
from decomposer.decomposer import decompose_java_file  # noqa: E402
from models.ml_classifier import (  # noqa: E402
    FEATURES, SeverityClassifier, generate_synthetic_training_data)

RULE_TO_SEVERITY = {"LOW": "NONE", "MEDIUM": "MINOR", "HIGH": "MAJOR", "CRITICAL": "CRITICAL"}
GOD = {"MAJOR", "CRITICAL"}
IMBALANCED = [0.60, 0.25, 0.10, 0.05]


def wilson(k: int, n: int, z: float = 1.96) -> list[float]:
    if n == 0:
        return [0.0, 1.0]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0.0, c - h), 3), round(min(1.0, c + h), 3)]


def load_labels() -> dict[str, str]:
    with open(ROOT / "dataset" / "labels.csv", newline="", encoding="utf-8") as f:
        return {r["class_name"]: r["severity"] for r in csv.DictReader(f)}


def agreement(pred: dict[str, str], labels: dict[str, str]) -> dict:
    k = sum(pred[c] == labels[c] for c in labels)
    kg = sum((pred[c] in GOD) == (labels[c] in GOD) for c in labels)
    return {"severity_correct": f"{k}/{len(labels)}", "severity_wilson95": wilson(k, len(labels)),
            "god_class_correct": f"{kg}/{len(labels)}", "god_class_wilson95": wilson(kg, len(labels))}


def median_seconds(fn, repeats: int = 5) -> float:
    times = []
    for _ in range(repeats):
        t = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t)
    return round(statistics.median(times), 4)


def rule_based(files, metrics, labels) -> dict:
    scorer = SeverityBasedScorer()
    rows, pred, pred_legacy = [], {}, {}
    for f in files:
        m = metrics[f.stem].to_dict()
        score, details = scorer.calculate_priority(m)
        label = RULE_TO_SEVERITY[details["priority_label"]]
        legacy = RULE_TO_SEVERITY[priority_label_for(score, legacy_bins=True)]
        pred[f.stem], pred_legacy[f.stem] = label, legacy
        rows.append({
            "class_name": f.stem, "label": labels[f.stem], "score": round(score, 2),
            "severity": label, "severity_legacy_bins": legacy,
            "god_class_candidate": bool(details["is_god_class_candidate"]),
            "metric_levels": {k: v["severity"] for k, v in details["contributions"].items()},
            "seconds": median_seconds(lambda f=f: scorer.calculate_priority(extract_metrics(f).to_dict())),
        })
    t = scorer.thresholds
    return {
        "thresholds": {
            "loc": [t.loc_low, t.loc_medium, t.loc_high], "nom": [t.nom_low, t.nom_medium, t.nom_high],
            "wmc": [t.wmc_low, t.wmc_medium, t.wmc_high], "cbo": [t.cbo_low, t.cbo_medium, t.cbo_high],
            "lcom": [t.lcom_low, t.lcom_medium, t.lcom_high]},
        "weights": {k: getattr(scorer.weights, k) for k in ("loc", "wmc", "cbo", "lcom", "nom")},
        "files": rows,
        "agreement": agreement(pred, labels),
        "agreement_legacy_bins": agreement(pred_legacy, labels),
        "median_seconds_per_file": round(statistics.median(r["seconds"] for r in rows), 4),
    }


def train(proportions=None, smote=False, pca=False):
    X, y = generate_synthetic_training_data(n_samples=2000, random_state=42, class_proportions=proportions)
    clf = SeverityClassifier({}, use_smote=smote, use_pca=pca)
    started = time.perf_counter()
    perf = clf.train(X, y, FEATURES)
    return clf, perf, round(time.perf_counter() - started, 1)


def classify_files(clf, files, metrics):
    out = {}
    for f in files:
        m = metrics[f.stem].to_dict()
        out[f.stem] = clf.classify_file(m)
    return out


def machine_learning(files, metrics, labels, quick: bool) -> dict:
    clf, perf, train_seconds = train()
    results = classify_files(clf, files, metrics)
    pred = {c: r.predicted_severity for c, r in results.items()}
    rows = [{
        "class_name": c, "label": labels[c], "severity": r.predicted_severity,
        "confidence": r.confidence, "probabilities": r.probabilities,
        "seconds": median_seconds(lambda c=c: clf.classify_file(metrics[c].to_dict())),
    } for c, r in results.items()]
    out = {
        "features": FEATURES,
        "training": {"samples": 2000, "hold_out_share": 0.2, "seed": 42, "cv_folds": 5,
                     "cv_on": "training split only", "train_seconds_all_models": train_seconds},
        "models_on_synthetic_hold_out": {n: p.to_dict() for n, p in perf.items()},
        "feature_importance_random_forest": {k: round(float(v), 4)
                                              for k, v in clf.get_feature_importance("random_forest").items()},
        "files": rows,
        "agreement": agreement(pred, labels),
        "median_seconds_per_file": round(statistics.median(r["seconds"] for r in rows), 4),
    }
    if quick:
        return out

    ablation = []
    for data_name, proportions in (("balanced", None), ("imbalanced 60/25/10/5", IMBALANCED)):
        for smote in (False, True):
            for pca in (False, True):
                if data_name == "balanced" and not smote and not pca:
                    c, p = clf, perf
                else:
                    c, p, _ = train(proportions, smote, pca)
                file_pred = {k: r.predicted_severity for k, r in classify_files(c, files, metrics).items()}
                e = p["ensemble"]
                ablation.append({
                    "training_data": data_name, "smote": smote, "pca": pca,
                    "ensemble_accuracy": e.accuracy, "ensemble_f1_macro": e.f1_macro,
                    "ensemble_cv_f1": f"{e.cv_mean:.3f} +/- {e.cv_std:.3f}",
                    "files_correct": agreement(file_pred, labels)["severity_correct"],
                })
    out["ablation"] = ablation
    return out


def javac_errors(directory: Path) -> int | None:
    javac = shutil.which("javac")
    sources = sorted(directory.glob("*.java"))
    if not javac or not sources:
        return None
    build = directory / "_build"
    build.mkdir(exist_ok=True)
    proc = subprocess.run([javac, "-d", str(build), *map(str, sources)],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    shutil.rmtree(build, ignore_errors=True)
    return (proc.stdout + proc.stderr).count("error:")


def decomposition(files, metrics, labels) -> dict:
    out_root = ROOT / "results" / "decomposition"
    if out_root.exists():
        shutil.rmtree(out_root)
    rows = []
    for f in files:
        target = out_root / f.stem
        target.mkdir(parents=True, exist_ok=True)
        result = decompose_java_file(str(f), str(target))
        generated = sorted(p.name for p in target.glob("*.java"))
        names = [e.name for e in result.extracted_classes]
        row = {
            "class_name": f.stem, "label": labels[f.stem],
            "produced_output": bool(result.success and generated),
            "extracted_classes": len(names),
            "duplicate_class_names": len(names) - len(set(names)),
            "methods_moved": sum(len(e.methods) for e in result.extracted_classes),
            "methods_in_class": metrics[f.stem].nom,
            "files_written": generated,
            "javac_errors": javac_errors(target) if generated else None,
            "message": result.message,
        }
        if generated:
            after = {}
            for name in generated:
                try:
                    m = extract_metrics(target / name)
                    after[name] = {"nom": m.nom, "wmc": m.wmc, "lcom": m.lcom}
                except Exception as e:
                    after[name] = f"not parsable ({type(e).__name__})"
            row["metrics_after"] = after
        else:
            target.rmdir()
        rows.append(row)
    attempted = [r for r in rows if r["produced_output"]]
    compiled = [r for r in attempted if r["javac_errors"] == 0]
    return {
        "files": rows,
        "produced_output": f"{len(attempted)}/{len(rows)}",
        "output_compiles": f"{len(compiled)}/{len(attempted)}" if shutil.which("javac") else "javac not found",
    }


def write_markdown(r: dict, path: Path) -> None:
    L = ["# Evaluation results", "",
         "Generated by `python evaluate.py`. Do not edit by hand; rerun instead.", "",
         "Six classes, labels assigned by the author (`dataset/labels.csv`). With six items the "
         "95% intervals are wide; the counts are a sanity check, not an accuracy estimate.", "",
         "## 1. Class metrics (primary class, syntax tree)", "",
         "| Class | LOC | SLOC | NOM | NOA | WMC | CBO | LCOM | Label |", "|---|---|---|---|---|---|---|---|---|"]
    for m in r["metrics"]:
        L.append(f"| {m['class_name']} | {m['loc']} | {m['sloc']} | {m['nom']} | {m['noa']} | {m['wmc']} | "
                 f"{m['cbo']} | {m['lcom']:.2f} | {m['label']} |")
    rb = r["rule_based"]
    L += ["", "## 2. Rule-based severity", "",
          "| Class | Label | Score | Severity | Severity (legacy bins) | God Class flag |", "|---|---|---|---|---|---|"]
    for f in rb["files"]:
        L.append(f"| {f['class_name']} | {f['label']} | {f['score']:.2f} | {f['severity']} | "
                 f"{f['severity_legacy_bins']} | {'yes' if f['god_class_candidate'] else 'no'} |")
    a, al = rb["agreement"], rb["agreement_legacy_bins"]
    L += ["", f"- Severity agreement: {a['severity_correct']} (95% CI {a['severity_wilson95']}); "
              f"with the legacy bins {al['severity_correct']}.",
          f"- God Class (MAJOR or CRITICAL) agreement: {a['god_class_correct']} (95% CI {a['god_class_wilson95']}).",
          f"- Median time per file: {rb['median_seconds_per_file']} s.",
          f"- Thresholds (LOW/MEDIUM/HIGH upper bounds): {rb['thresholds']}; weights: {rb['weights']}."]
    ml = r["machine_learning"]
    L += ["", "## 3. Machine learning", "",
          "Hold-out results on synthetic data drawn from the same generator as the training data. "
          "They show that the models recover the generator's ranges and say nothing about real code.", "",
          "| Model | Accuracy | Precision (w) | Recall (w) | F1 (w) | F1 (macro) | 5-fold CV F1 |", "|---|---|---|---|---|---|---|"]
    for n, p in ml["models_on_synthetic_hold_out"].items():
        L.append(f"| {n} | {p['accuracy']:.4f} | {p['precision']:.4f} | {p['recall']:.4f} | {p['f1_score']:.4f} | "
                 f"{p['f1_macro']:.4f} | {p['cv_mean']:.3f} +/- {p['cv_std']:.3f} |")
    L += ["", "| Class | Label | Predicted | Confidence | P(NONE) | P(MINOR) | P(MAJOR) | P(CRITICAL) |",
          "|---|---|---|---|---|---|---|---|"]
    for f in ml["files"]:
        pr = f["probabilities"]
        L.append(f"| {f['class_name']} | {f['label']} | {f['severity']} | {f['confidence']:.1f}% | "
                 f"{pr['NONE']} | {pr['MINOR']} | {pr['MAJOR']} | {pr['CRITICAL']} |")
    a = ml["agreement"]
    L += ["", f"- Severity agreement on the six classes: {a['severity_correct']} (95% CI {a['severity_wilson95']}); "
              f"God Class agreement {a['god_class_correct']}.",
          f"- Median inference time per file: {ml['median_seconds_per_file']} s; "
          f"training all models: {ml['training']['train_seconds_all_models']} s.",
          "", "Random Forest feature importance (a property of the generator's ranges, not of real code):", "",
          "| Feature | Importance |", "|---|---|"]
    L += [f"| {k} | {v:.4f} |" for k, v in ml["feature_importance_random_forest"].items()]
    if "ablation" in ml:
        L += ["", "Ablation (ensemble; synthetic hold-out; six-class agreement):", "",
              "| Training data | SMOTE | PCA | Accuracy | F1 (macro) | CV F1 | Classes correct |", "|---|---|---|---|---|---|---|"]
        for x in ml["ablation"]:
            L.append(f"| {x['training_data']} | {'yes' if x['smote'] else 'no'} | {'yes' if x['pca'] else 'no'} | "
                     f"{x['ensemble_accuracy']:.4f} | {x['ensemble_f1_macro']:.4f} | {x['ensemble_cv_f1']} | {x['files_correct']} |")
    d = r["decomposition"]
    L += ["", "## 4. Rule-based Extract Class output", "",
          "| Class | Label | Output produced | Classes extracted | Duplicate names | Methods moved | javac errors |",
          "|---|---|---|---|---|---|---|"]
    for f in d["files"]:
        L.append(f"| {f['class_name']} | {f['label']} | {'yes' if f['produced_output'] else 'no'} | {f['extracted_classes']} | "
                 f"{f['duplicate_class_names']} | {f['methods_moved']}/{f['methods_in_class']} | "
                 f"{'-' if f['javac_errors'] is None else f['javac_errors']} |")
    L += ["", f"- Output produced for {d['produced_output']} classes; output that compiles: {d['output_compiles']}.", ""]
    path.write_text("\n".join(L), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quick", action="store_true", help="skip the SMOTE/PCA ablation")
    args = ap.parse_args()
    logging.disable(logging.CRITICAL)

    labels = load_labels()
    files = sorted((ROOT / "dataset" / "blind").glob("*.java"))
    missing = {f.stem for f in files} ^ set(labels)
    if missing:
        print(f"dataset/blind and dataset/labels.csv disagree on: {sorted(missing)}")
        return 1
    order = ["NONE", "MINOR", "MAJOR", "CRITICAL"]
    files.sort(key=lambda f: (order.index(labels[f.stem]), f.stem))
    metrics = {f.stem: extract_metrics(f) for f in files}

    results = {
        "dataset": {"files": len(files), "labels": "dataset/labels.csv (assigned by the author)"},
        "metrics": [{**metrics[f.stem].to_dict(), "label": labels[f.stem]} for f in files],
        "rule_based": rule_based(files, metrics, labels),
        "machine_learning": machine_learning(files, metrics, labels, args.quick),
        "decomposition": decomposition(files, metrics, labels),
    }
    for m in results["metrics"]:
        m["file_path"] = Path(m["file_path"]).name
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    (out / "evaluation.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    write_markdown(results, out / "evaluation.md")
    print(f"Rule-based severity agreement: {results['rule_based']['agreement']['severity_correct']}")
    print(f"ML severity agreement:         {results['machine_learning']['agreement']['severity_correct']}")
    print(f"Decomposer output compiles:    {results['decomposition']['output_compiles']}")
    print(f"Written {out / 'evaluation.md'} and evaluation.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
