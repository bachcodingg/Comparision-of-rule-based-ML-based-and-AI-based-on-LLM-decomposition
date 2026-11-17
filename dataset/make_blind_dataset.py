#!/usr/bin/env python3


import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = (ROOT / "rule-based-java-decomposition" / "rule-based-java-decomposition"
              / "data" / "sample")
OUT_DIR = ROOT / "dataset" / "blind"

# original file name -> name of the evaluation copy (= public class name)
FILES = {
    "Example_1_LOW_EmailValidator.java": "EmailValidator.java",
    "Example_2_MEDIUM_OrderProcessor.java": "OrderProcessor.java",
    "UserService.java": "UserService.java",
    "ClothingInventoryManager.java": "ClothingInventoryManager.java",
    "Example_3_HIGH_InventoryManagementSystem.java": "InventoryManagementSystem.java",
    "Example_4_CRITICAL_EnterpriseResourcePlanner.java": "EnterpriseResourcePlanner.java",
}

# A comment containing any of these reveals the label or the expected analysis.
LEAK = re.compile(
    r"severity|expected|priority|god\s*class|decompos|refactor|single responsibility"
    r"|\bSRP\b|violat|cohesi|coupling|\bLOC\b|\bNOM\b|\bWMC\b|\bCBO\b|\bLCOM\b"
    r"|\b(?:LOW|MEDIUM|HIGH|CRITICAL)\b|problems with this class|responsibilit"
    r"|too many|should be|demonstration|example of"
    # section banners: they partition the methods into named responsibilities
    # and give hand-counted method and complexity totals
    r"|={4,}|\d+\s+methods|complexity\s+\d+",
    re.IGNORECASE,
)

# comments and literals in one pass, so comment markers inside strings are ignored
TOKEN = re.compile(
    r'(?P<block>/\*.*?\*/)'
    r'|(?P<line>//[^\n]*)'
    r'|(?P<string>"(?:\\.|[^"\\\n])*")'
    r"|(?P<char>'(?:\\.|[^'\\\n])*')",
    re.DOTALL,
)


def strip_leaking_comments(source: str):
    removed = []

    def _sub(match):
        if match.group("block") or match.group("line"):
            text = match.group(0)
            if LEAK.search(text):
                removed.append(text)
                return ""
        return match.group(0)

    cleaned = TOKEN.sub(_sub, source)
    # drop lines left empty by a removed comment, collapse runs of blank lines
    cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip() + "\n", removed


def remaining_leaks(source: str):
    hits = []
    for match in TOKEN.finditer(source):
        if (match.group("block") or match.group("line")) and LEAK.search(match.group(0)):
            hits.append(match.group(0))
    return hits


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    status = 0
    for original, target in FILES.items():
        source = (SOURCE_DIR / original).read_text(encoding="utf-8")
        cleaned, removed = strip_leaking_comments(source)

        if target == "EnterpriseResourcePlanner.java":
            # java.util.* and java.sql.* both declare Date; name the one used.
            cleaned = cleaned.replace("import java.util.*;\n",
                                      "import java.util.*;\nimport java.util.Date;\n", 1)

        left = remaining_leaks(cleaned)
        if left:
            status = 1
        (OUT_DIR / target).write_text(cleaned, encoding="utf-8", newline="\n")
        print(f"{original:52s} -> blind/{target:32s} "
              f"lines {len(source.splitlines()):5d} -> {len(cleaned.splitlines()):5d}, "
              f"comments removed: {len(removed):2d}, leaks left: {len(left)}")
    return status


if __name__ == "__main__":
    sys.exit(main())
