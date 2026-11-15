# LLM evaluation

Runs each model on each class in `dataset/blind/` several times, stores every raw response, and
scores the answers with checks a script can verify. It replaces the January 2026 trial, which was
done by hand in chat interfaces, once per file, on files that contained the expected answer.

## Protocol

- **Input**: the Java source only. The prompt (`prompt.py`) contains no file name, label or metric.
  `run_eval.py` refuses to run if `leak_check.py` finds answer-revealing comments or file names.
- **Output**: a JSON object (severity, proposed classes with method lists, methods kept).
- **Trials**: 3 per file by default (`config.yaml`). Current Claude models and most reasoning models
  do not accept `temperature`, so determinism cannot be requested; run-to-run variation is measured
  and reported instead.
- **Recorded per call**: exact model ID as returned by the API, settings, prompt version, SHA-256 of
  the input, token counts from the API, wall-clock latency, request ID, timestamp.

## Measures (`score.py`)

| Measure | Meaning |
|---|---|
| severity accuracy | majority answer per file vs. `dataset/labels.csv`, with a 95% Wilson interval |
| consistency | files on which every trial gave the same severity |
| existence rate | share of method names in the proposal that are declared in the class |
| coverage | share of the class's methods assigned to a proposed class |
| duplicates | methods assigned to more than one proposed class |
| latency, tokens, cost | measured; cost = tokens x the prices you enter in `config.yaml` |

These replace the author-assigned 1-5 quality ratings. They do not measure whether a proposed split
is a *good design*; that still needs human raters (two raters, a written rubric, Cohen's kappa).

## Run

```bash
pip install -r requirements.txt
python run_eval.py --dry-run                 # no API calls: leak check, prompt sizes, call plan
export ANTHROPIC_API_KEY=...                 # and/or OPENAI_API_KEY, GEMINI_API_KEY
python run_eval.py --providers anthropic --limit 1    # smoke test, 3 calls
python run_eval.py                           # everything enabled in config.yaml
python score.py                              # writes results/scores.json and results/summary.md
```

A full run for one provider is 18 calls of roughly 700-7,700 input tokens each. Raw responses go
to `results/raw/<provider>/<class>/trial_<k>.json`; existing files are skipped, so a run can be resumed.

## Status

- The Claude provider uses the official Anthropic SDK and defaults to `claude-opus-5-5`.
- The OpenAI and Gemini providers have **not been run against the live APIs** (no keys were available
  when they were written). Set the model ID in `config.yaml`, run with `--limit 1` first, and fix
  whatever the SDK reports.
- Refusal fallbacks are deliberately off for Claude: a fallback would let a different model answer.
- No results are committed yet. Nothing in the thesis should cite this evaluation until it has been run.

## Legacy record

`legacy/january_2026_record.json` is a transcription of the only method-level recommendations kept
from the January trial (Claude 3.5 Sonnet, three files). `python score.py --legacy` scores it:

| Class | Named methods that exist | Coverage |
|---|---|---|
| OrderProcessor | 10/10 | 67% |
| InventoryManagementSystem | 16/25 | 57% |
| EnterpriseResourcePlanner | 15/67 | 28% |

The recorded proposal for EnterpriseResourcePlanner includes employee, department and payroll
services; the class contains no such code.
