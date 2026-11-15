"""The single prompt sent to every model, and the response schema.

The prompt never contains the file name, the expected label or any metric
computed by the other pipelines. Severity definitions are qualitative so the
model has to judge the code rather than apply thresholds it was handed.
"""

from __future__ import annotations

PROMPT_VERSION = "2026-11-v1"

SEVERITY_LEVELS = ["NONE", "MINOR", "MAJOR", "CRITICAL"]

PROMPT_TEMPLATE = """\
You are reviewing one Java class for the God Class (Blob) design smell.

Rate its severity on this scale:
- NONE: cohesive class with one responsibility; no action needed.
- MINOR: mostly cohesive, some early signs of a second responsibility; monitor.
- MAJOR: several distinct responsibilities in one class; should be refactored.
- CRITICAL: many unrelated responsibilities; decomposition is urgent.

Then, if the severity is MAJOR or CRITICAL, propose an Extract Class
decomposition. Rules for the decomposition:
- Use only methods that are declared in the class shown below. Copy each
  method name exactly as written; do not invent, rename or merge methods.
- Assign each method to at most one new class.
- Methods that should stay in the original class go in "methods_kept".
If the severity is NONE or MINOR, return an empty "proposed_classes" list.

Java source:
```java
{source}
```
"""

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "severity": {"type": "string", "enum": SEVERITY_LEVELS},
        "is_god_class": {"type": "boolean"},
        "responsibilities": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Distinct responsibilities found in the class.",
        },
        "proposed_classes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "responsibility": {"type": "string"},
                    "methods": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["name", "responsibility", "methods"],
                "additionalProperties": False,
            },
        },
        "methods_kept": {"type": "array", "items": {"type": "string"}},
        "rationale": {"type": "string"},
    },
    "required": [
        "severity", "is_god_class", "responsibilities",
        "proposed_classes", "methods_kept", "rationale",
    ],
    "additionalProperties": False,
}

JSON_INSTRUCTION = (
    "\nRespond with a single JSON object and nothing else, with exactly these "
    "keys: severity (one of NONE, MINOR, MAJOR, CRITICAL), is_god_class "
    "(boolean), responsibilities (list of strings), proposed_classes (list of "
    "objects with name, responsibility, methods), methods_kept (list of "
    "strings), rationale (string)."
)


def build_prompt(source: str) -> str:
    return PROMPT_TEMPLATE.format(source=source)
