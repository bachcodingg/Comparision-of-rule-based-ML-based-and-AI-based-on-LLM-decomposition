"""Ground-truth structure of a Java file, used to score LLM recommendations.

The primary class is the public top-level type, or the first top-level type
when none is public. Helper classes declared in the same file are reported
separately and are not counted as methods of the primary class.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import javalang


@dataclass
class ClassStructure:
    file: str
    class_name: str
    methods: list[str]                 # declared directly in the primary class
    fields: list[str]
    helper_classes: list[str] = field(default_factory=list)
    parser: str = "javalang"

    @property
    def method_set(self) -> set[str]:
        return set(self.methods)


def _primary_type(tree):
    types = list(tree.types)
    if not types:
        raise ValueError("no top-level type declaration found")
    for t in types:
        if "public" in (t.modifiers or set()):
            return t
    return types[0]


def parse_java(path: str | Path) -> ClassStructure:
    path = Path(path)
    source = path.read_text(encoding="utf-8", errors="replace")
    tree = javalang.parse.parse(source)
    primary = _primary_type(tree)
    methods = [m.name for m in primary.methods]
    fields = [d.name for f in primary.fields for d in f.declarators]
    helpers = [t.name for t in tree.types if t is not primary]
    nested = (
        javalang.tree.ClassDeclaration,
        javalang.tree.EnumDeclaration,
        javalang.tree.InterfaceDeclaration,
    )
    helpers += [b.name for b in primary.body if isinstance(b, nested)]
    return ClassStructure(
        file=path.name,
        class_name=primary.name,
        methods=methods,
        fields=fields,
        helper_classes=helpers,
    )


_CALL_SUFFIX = re.compile(r"\s*\(.*$")


def normalise_method_name(raw: str) -> str:
    """'OrderService.addOrder(Order o)' -> 'addOrder'."""
    name = _CALL_SUFFIX.sub("", raw.strip())
    return name.split(".")[-1].strip()


if __name__ == "__main__":
    import json
    import sys

    for arg in sys.argv[1:]:
        s = parse_java(arg)
        print(json.dumps({
            "file": s.file, "class": s.class_name, "n_methods": len(s.methods),
            "n_fields": len(s.fields), "helper_classes": s.helper_classes,
        }))
