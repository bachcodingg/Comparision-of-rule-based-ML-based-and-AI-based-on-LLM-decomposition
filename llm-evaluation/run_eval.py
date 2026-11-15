#!/usr/bin/env python3
"""Run the LLM evaluation: every model x every file x N trials, raw output saved.

    python run_eval.py --dry-run                 # no API calls: leak check, sizes, call plan
    python run_eval.py --providers anthropic     # one vendor
    python run_eval.py                           # every vendor enabled in config.yaml

Each call is written to results/raw/<provider>/<class>/trial_<k>.json. Existing
files are skipped, so an interrupted run can be resumed. Score with score.py.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from java_methods import parse_java  # noqa: E402
from leak_check import find_leaks  # noqa: E402
from prompt import PROMPT_VERSION, build_prompt  # noqa: E402


def load_config(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def resolve(base: Path, value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else (base / p).resolve()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=str(HERE / "config.yaml"))
    ap.add_argument("--providers", help="comma-separated subset of the enabled providers")
    ap.add_argument("--trials", type=int, help="override trials from config")
    ap.add_argument("--limit", type=int, help="only the first N files (smoke test)")
    ap.add_argument("--dry-run", action="store_true", help="make no API calls")
    ap.add_argument("--allow-leaks", action="store_true",
                    help="run even if a file reveals its label (results are then not valid evidence)")
    args = ap.parse_args()

    cfg_path = Path(args.config).resolve()
    cfg = load_config(cfg_path)
    dataset_dir = resolve(cfg_path.parent, cfg["dataset_dir"])
    out_dir = resolve(cfg_path.parent, cfg.get("results_dir", "results")) / "raw"
    trials = args.trials or cfg.get("trials", 3)

    files = sorted(dataset_dir.glob("*.java"))
    if args.limit:
        files = files[: args.limit]
    if not files:
        print(f"No .java files in {dataset_dir}")
        return 1

    # 1. Leak check
    leaky = {f.name: find_leaks(f) for f in files}
    leaky = {k: v for k, v in leaky.items() if v}
    if leaky:
        print("Label leakage found in the input files:")
        for name, items in leaky.items():
            print(f"  {name}: {len(items)} finding(s), e.g. {items[0]}")
        if not args.allow_leaks and not args.dry_run:
            print("Refusing to run. Remove the answer-revealing comments/file names, or pass --allow-leaks.")
            return 2

    # 2. Plan
    enabled = {n: c for n, c in (cfg.get("providers") or {}).items() if (c or {}).get("enabled")}
    if args.providers:
        wanted = [p.strip() for p in args.providers.split(",")]
        enabled = {n: (cfg.get("providers") or {}).get(n) or {} for n in wanted}
    prompts = {}
    print(f"\nPrompt version {PROMPT_VERSION}; dataset {dataset_dir}")
    for f in files:
        source = f.read_text(encoding="utf-8", errors="replace")
        structure = parse_java(f)
        prompts[f] = (build_prompt(source), structure, hashlib.sha256(source.encode("utf-8")).hexdigest())
        print(f"  {structure.class_name:32s} {len(structure.methods):3d} methods  "
              f"prompt ~{len(prompts[f][0]) // 4:5d} tokens (chars/4 estimate)")
    n_calls = len(files) * trials * len(enabled)
    print(f"\nPlanned: {len(enabled)} provider(s) x {len(files)} file(s) x {trials} trial(s) = {n_calls} calls")
    for name, pcfg in enabled.items():
        print(f"  {name}: model={pcfg.get('model') or '(provider default)'}")
    if args.dry_run:
        print("\nDry run: no API calls made.")
        return 0
    if not enabled:
        print("No provider enabled in config.yaml.")
        return 1

    # 3. Run
    from providers import build_provider

    failures = 0
    for name, pcfg in enabled.items():
        provider = build_provider(name, pcfg)
        for f, (prompt, structure, digest) in prompts.items():
            for k in range(1, trials + 1):
                target = out_dir / name / structure.class_name / f"trial_{k}.json"
                if target.exists():
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                record = {
                    "provider": name,
                    "settings": provider.settings(),
                    "prompt_version": PROMPT_VERSION,
                    "file": f.name,
                    "class_name": structure.class_name,
                    "source_sha256": digest,
                    "trial": k,
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "leak_findings": leaky.get(f.name, []),
                }
                try:
                    record["response"] = provider.complete(prompt)
                    status = f"{record['response']['latency_s']:.1f}s"
                except Exception as e:  # recorded, not hidden: a failed call is a result
                    record["error"] = f"{type(e).__name__}: {e}"
                    status = "ERROR " + record["error"][:80]
                    failures += 1
                target.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
                print(f"  {name:10s} {structure.class_name:32s} trial {k}: {status}")
    print(f"\nDone. Raw responses in {out_dir}. Failed calls: {failures}. Next: python score.py")
    return 0 if failures == 0 else 3


if __name__ == "__main__":
    sys.exit(main())
