#!/usr/bin/env python3
"""Score saved LLM responses with checks a script can verify.

    python score.py                       # scores results/raw -> results/scores.json, summary.md
    python score.py --legacy              # scores the transcribed January 2026 record

Severity is compared with the labels file. Recommendation quality is measured
against the parsed source instead of being rated by the author:

  existence rate  share of distinct method names in the proposal that are
                  declared in the class (1 - hallucination rate)
  coverage        share of the class's methods assigned to a proposed class
  accounted       coverage plus methods explicitly kept in the original class
  duplicates      method names assigned to more than one proposed class
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from java_methods import ClassStructure, normalise_method_name, parse_java  # noqa: E402

ALIASES = {"LOW": "NONE", "MEDIUM": "MINOR", "HIGH": "MAJOR"}
GOD = {"MAJOR", "CRITICAL"}


def canonical(severity: str | None) -> str | None:
    if not severity:
        return None
    s = severity.strip().upper()
    return ALIASES.get(s, s)


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for a proportion."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def score_recommendation(answer: dict, structure: ClassStructure) -> dict:
    real = structure.method_set
    per_class = [[normalise_method_name(m) for m in c.get("methods", [])]
                 for c in answer.get("proposed_classes", [])]
    named = [m for ms in per_class for m in ms]
    distinct = set(named)
    exist = distinct & real
    kept = {normalise_method_name(m) for m in answer.get("methods_kept", [])} & real
    counts = Counter(m for ms in per_class for m in set(ms))
    return {
        "n_proposed_classes": len(per_class),
        "methods_named": len(named),
        "methods_distinct": len(distinct),
        "methods_exist": len(exist),
        "methods_invented": sorted(distinct - real),
        "existence_rate": round(len(exist) / len(distinct), 4) if distinct else None,
        "coverage": round(len(exist) / len(real), 4) if real else None,
        "accounted": round(len(exist | kept) / len(real), 4) if real else None,
        "duplicates": sorted(m for m, c in counts.items() if c > 1),
    }


def load_labels(path: Path) -> dict[str, str]:
    labels = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            labels[row["class_name"].strip()] = canonical(row["severity"])
    return labels


def score_trial(record: dict, structure: ClassStructure, label: str | None) -> dict:
    out = {"class_name": record["class_name"], "trial": record.get("trial"), "label": label}
    resp = record.get("response")
    if record.get("error") or not resp:
        out.update(valid=False, problem=record.get("error", "no response"))
        return out
    try:
        answer = json.loads(resp["text"])
    except (json.JSONDecodeError, TypeError):
        out.update(valid=False, problem=resp.get("note") or "response is not valid JSON")
        return out
    severity = canonical(answer.get("severity"))
    out.update(
        valid=True,
        severity=severity,
        severity_correct=(severity == label) if label else None,
        god_class_correct=((severity in GOD) == (label in GOD)) if label else None,
        latency_s=resp.get("latency_s"),
        input_tokens=resp.get("input_tokens"),
        output_tokens=resp.get("output_tokens"),
        **score_recommendation(answer, structure),
    )
    return out


def mean(values):
    values = [v for v in values if v is not None]
    return round(statistics.fmean(values), 4) if values else None


def aggregate(trials: list[dict], prices: dict | None) -> dict:
    by_class = defaultdict(list)
    for t in trials:
        by_class[t["class_name"]].append(t)
    files = {}
    for cls, ts in sorted(by_class.items()):
        sev = [t.get("severity") for t in ts if t.get("valid")]
        majority = Counter(sev).most_common(1)[0][0] if sev else None
        files[cls] = {
            "label": ts[0]["label"],
            "answers": sev,
            "majority": majority,
            "majority_correct": (majority == ts[0]["label"]) if ts[0]["label"] and majority else None,
            "consistent_across_trials": len(set(sev)) == 1 if sev else None,
            "mean_existence_rate": mean(t.get("existence_rate") for t in ts),
            "mean_coverage": mean(t.get("coverage") for t in ts),
        }
    labelled = [f for f in files.values() if f["majority_correct"] is not None]
    k = sum(f["majority_correct"] for f in labelled)
    lo, hi = wilson(k, len(labelled))
    valid = [t for t in trials if t.get("valid")]
    with_proposal = [t for t in valid if t.get("existence_rate") is not None]
    god_files = [t for t in valid if t.get("label") in GOD]
    tokens_in = sum(t.get("input_tokens") or 0 for t in valid)
    tokens_out = sum(t.get("output_tokens") or 0 for t in valid)
    summary = {
        "n_files": len(files),
        "n_trials": len(trials),
        "n_invalid": len(trials) - len(valid),
        "severity_accuracy_files": f"{k}/{len(labelled)}",
        "severity_accuracy_wilson95": [round(lo, 3), round(hi, 3)],
        "severity_accuracy_trials": mean(float(t["severity_correct"]) for t in valid
                                         if t.get("severity_correct") is not None),
        "files_consistent_across_trials": f"{sum(bool(f['consistent_across_trials']) for f in files.values())}/{len(files)}",
        "mean_existence_rate": mean(t["existence_rate"] for t in with_proposal),
        "mean_coverage_on_god_classes": mean(t.get("coverage") for t in god_files),
        "trials_with_duplicates": sum(bool(t.get("duplicates")) for t in valid),
        "median_latency_s": round(statistics.median(t["latency_s"] for t in valid if t.get("latency_s")), 2)
        if any(t.get("latency_s") for t in valid) else None,
        "input_tokens": tokens_in,
        "output_tokens": tokens_out,
    }
    if prices and prices.get("input_per_mtok") is not None and valid:
        cost = tokens_in / 1e6 * prices["input_per_mtok"] + tokens_out / 1e6 * prices["output_per_mtok"]
        summary["cost_usd_total"] = round(cost, 4)
        summary["cost_usd_per_call"] = round(cost / len(valid), 4)
    return {"summary": summary, "files": files}


def write_markdown(results: dict, path: Path) -> None:
    lines = ["# LLM evaluation summary", "",
             "Generated by `score.py` from the raw responses. Do not edit by hand.", ""]
    for provider, r in results.items():
        s = r["summary"]
        lines += [f"## {provider} ({r.get('model', 'model not recorded')})", "",
                  "| Measure | Value |", "|---|---|"]
        for key, value in s.items():
            lines.append(f"| {key.replace('_', ' ')} | {value} |")
        lines += ["", "| Class | Label | Answers per trial | Majority | Existence rate | Coverage |",
                  "|---|---|---|---|---|---|"]
        for cls, f in r["files"].items():
            lines.append(f"| {cls} | {f['label']} | {', '.join(a or '-' for a in f['answers'])} | "
                         f"{f['majority']} | {f['mean_existence_rate']} | {f['mean_coverage']} |")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def score_legacy(cfg_dir: Path) -> int:
    legacy = json.loads((HERE / "legacy" / "january_2026_record.json").read_text(encoding="utf-8"))
    source_dir = (HERE / legacy["source_dir"]).resolve()
    print(f"Legacy record: {legacy['description']}\nSource files: {source_dir}\n")
    rows = []
    for item in legacy["recommendations"]:
        structure = parse_java(source_dir / item["file"])
        r = score_recommendation(item, structure)
        rows.append({"model": item["model"], "class_name": structure.class_name,
                     "methods_in_class": len(structure.methods), **r})
        print(f"{item['model']} on {structure.class_name} ({len(structure.methods)} methods): "
              f"{r['methods_exist']}/{r['methods_distinct']} named methods exist "
              f"(existence rate {r['existence_rate']}), coverage {r['coverage']}")
        if r["methods_invented"]:
            print(f"   not in the class: {', '.join(r['methods_invented'][:12])}"
                  f"{' ...' if len(r['methods_invented']) > 12 else ''}")
    out = HERE / "legacy" / "january_2026_scores.json"
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"\nWritten {out}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=str(HERE / "config.yaml"))
    ap.add_argument("--legacy", action="store_true", help="score the transcribed January 2026 record")
    args = ap.parse_args()
    cfg_path = Path(args.config).resolve()
    if args.legacy:
        return score_legacy(cfg_path.parent)

    cfg = yaml.safe_load(open(cfg_path, encoding="utf-8"))
    base = cfg_path.parent
    dataset_dir = (base / cfg["dataset_dir"]).resolve()
    results_dir = (base / cfg.get("results_dir", "results")).resolve()
    labels = load_labels((base / cfg["labels_file"]).resolve())
    structures = {s.class_name: s for s in (parse_java(f) for f in sorted(dataset_dir.glob("*.java")))}

    results = {}
    for provider_dir in sorted((results_dir / "raw").glob("*")):
        records = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(provider_dir.glob("*/trial_*.json"))]
        if not records:
            continue
        trials = [score_trial(r, structures[r["class_name"]], labels.get(r["class_name"]))
                  for r in records if r["class_name"] in structures]
        prices = ((cfg.get("providers") or {}).get(provider_dir.name) or {}).get("prices")
        results[provider_dir.name] = {
            "model": records[0].get("settings", {}).get("model"),
            "settings": records[0].get("settings"),
            "prompt_version": records[0].get("prompt_version"),
            **aggregate(trials, prices),
            "trials": trials,
        }
    if not results:
        print(f"No raw responses under {results_dir / 'raw'}. Run run_eval.py first.")
        return 1
    (results_dir / "scores.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    write_markdown(results, results_dir / "summary.md")
    for provider, r in results.items():
        s = r["summary"]
        print(f"{provider}: severity {s['severity_accuracy_files']} files "
              f"(95% CI {s['severity_accuracy_wilson95']}), existence rate {s['mean_existence_rate']}, "
              f"coverage {s['mean_coverage_on_god_classes']}")
    print(f"Written {results_dir / 'scores.json'} and summary.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
