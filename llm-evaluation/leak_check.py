"""Refuse to evaluate on inputs that tell the model the answer.

The January 2026 evaluation sent files whose header comments contained the
expected severity, hand-computed metrics, the priority score and a suggested
decomposition, and whose file names contained the label. This check scans the
comments and the file name for that kind of text.
"""

from __future__ import annotations

import re
from pathlib import Path

_COMMENT = re.compile(r"/\*.*?\*/|//[^\n]*", re.DOTALL)

# Each pattern is matched case-insensitively inside comments only.
_LEAK_PATTERNS = [
    r"\b(low|medium|high|critical|none|minor|major)\s+(severity|priority)\b",
    r"\bseverity\s+(example|level)",
    r"\bexpected\s+result\b",
    r"\bpriority\s+score\b",
    r"\bgod\s*class\b",
    r"\bsuggested\s+decomposition\b",
    r"\bshould\s+be\s+(decomposed|refactored|split)\b",
    r"\bviolates\s+the\s+single\s+responsibility\b",
    r"\b(loc|nom|wmc|cbo|lcom)\s*:\s*~?\d",
    r"\brefactor(ing)?\s+(needed|required|when)\b",
]
_LEAK_RE = [re.compile(p, re.IGNORECASE) for p in _LEAK_PATTERNS]
_NAME_RE = re.compile(r"(?<![a-z])(low|medium|high|critical|none|minor|major)(?![a-z])", re.IGNORECASE)


def find_leaks(path: str | Path) -> list[str]:
    """Return human-readable descriptions of label-revealing text."""
    path = Path(path)
    findings: list[str] = []
    if _NAME_RE.search(path.stem.replace("_", " ")):
        findings.append(f"file name contains a severity word: {path.name}")
    source = path.read_text(encoding="utf-8", errors="replace")
    for comment in _COMMENT.findall(source):
        for rx in _LEAK_RE:
            m = rx.search(comment)
            if m:
                line = source.count("\n", 0, source.find(comment)) + 1
                findings.append(f"comment near line {line}: '{m.group(0)}'")
                break
    return findings


if __name__ == "__main__":
    import sys

    bad = 0
    for arg in sys.argv[1:]:
        for p in sorted(Path(arg).glob("*.java")) if Path(arg).is_dir() else [Path(arg)]:
            leaks = find_leaks(p)
            bad += bool(leaks)
            print(f"{'LEAK' if leaks else 'ok  '}  {p.name}")
            for item in leaks[:5]:
                print(f"        {item}")
            if len(leaks) > 5:
                print(f"        ... and {len(leaks) - 5} more")
    sys.exit(1 if bad else 0)
