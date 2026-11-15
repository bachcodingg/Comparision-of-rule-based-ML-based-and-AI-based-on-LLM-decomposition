"""Class metrics computed from the Java syntax tree (javalang).

This is the single source of metric values for the rule-based pipeline, the
ML pipeline and the evaluation scripts. The two earlier regex extractors gave
different values for the same file and counted the methods of every helper
class in the file as methods of the main class.

Definitions (all metrics except LOC/SLOC refer to the PRIMARY class: the public
top-level type, or the first top-level type if none is public):

  LOC    physical lines in the file, including comments and blank lines
  SLOC   lines that contain code (comments and blank lines removed)
  NOM    methods declared in the primary class (constructors excluded)
  NOA    fields declared in the primary class
  WMC    sum of the cyclomatic complexity of those methods; one method scores
         1 + the number of if / for / while / do / case / catch / ?: / && / ||
  CBO    distinct class types the primary class refers to, excluding itself,
         type parameters and common JDK types (see JDK_TYPES). This is an
         approximation: without a classpath a name cannot be resolved, so JDK
         types are removed by name.
  LCOM   share of method pairs that use no common field of the class, in [0, 1]
         (0 = every pair shares a field, 1 = no pair does). 0 when the class
         has fewer than two methods or no fields.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from itertools import combinations
from pathlib import Path

import javalang
from javalang import tree as T

JDK_TYPES = frozenset("""
String Integer Long Double Float Boolean Byte Short Character Object Class Void Number
List ArrayList LinkedList Map HashMap TreeMap LinkedHashMap Set HashSet TreeSet LinkedHashSet
Collection Collections Iterator Iterable Optional Stream Collectors Queue Deque ArrayDeque
PriorityQueue Arrays Math System Runtime Thread Runnable Objects UUID
Exception RuntimeException Error Throwable IllegalArgumentException IllegalStateException
NullPointerException IOException IndexOutOfBoundsException UnsupportedOperationException
StringBuilder StringBuffer Comparable Comparator Serializable Cloneable
Date Calendar LocalDate LocalDateTime LocalTime Instant Duration BigDecimal BigInteger
SimpleDateFormat DateFormat DecimalFormat NumberFormat
Pattern Matcher Scanner Random File Path Paths Files
PrintStream PrintWriter FileWriter FileReader BufferedReader BufferedWriter
InputStream OutputStream Reader Writer
""".split())

_NON_CODE = re.compile(
    r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\'', re.DOTALL)


@dataclass
class ClassMetrics:
    file_path: str
    class_name: str
    loc: int
    sloc: int
    nom: int
    noa: int
    wmc: int
    cbo: int
    lcom: float
    helper_classes: int      # other types declared in the same file
    constructors: int

    def to_dict(self) -> dict:
        return asdict(self)


def _count_sloc(source: str) -> int:
    def blank(match):
        text = match.group(0)
        if text[0] in "\"'":
            return '""'
        return "\n" * text.count("\n")
    return sum(1 for line in _NON_CODE.sub(blank, source).splitlines() if line.strip())


def primary_type(compilation_unit):
    types = list(compilation_unit.types)
    if not types:
        raise ValueError("no top-level type declaration")
    for t in types:
        if "public" in (t.modifiers or set()):
            return t
    return types[0]


def cyclomatic_complexity(method) -> int:
    cc = 1
    for _, node in method:
        if isinstance(node, (T.IfStatement, T.ForStatement, T.WhileStatement,
                             T.DoStatement, T.CatchClause, T.TernaryExpression)):
            cc += 1
        elif isinstance(node, T.SwitchStatementCase):
            cc += len(node.case or [])
        elif isinstance(node, T.BinaryOperation) and node.operator in ("&&", "||"):
            cc += 1
    return cc


def fields_used(method, field_names: set[str]) -> set[str]:
    """Fields of the class that a method reads, writes or calls a method on."""
    shadowed = {p.name for p in method.parameters}
    for _, node in method:
        if isinstance(node, T.VariableDeclarator):
            shadowed.add(node.name)
    used: set[str] = set()
    for _, node in method:
        if isinstance(node, T.This):
            for sel in node.selectors or []:
                if isinstance(sel, T.MemberReference) and sel.member in field_names:
                    used.add(sel.member)
                break  # only the first selector is a member of `this`
        elif isinstance(node, T.MemberReference):
            head = (node.qualifier or node.member).split(".")[0]
            if head in field_names and head not in shadowed:
                used.add(head)
        elif isinstance(node, T.MethodInvocation) and node.qualifier:
            head = node.qualifier.split(".")[0]
            if head in field_names and head not in shadowed:
                used.add(head)
    return used


def lcom(methods, field_names: set[str]) -> float:
    if len(methods) < 2 or not field_names:
        return 0.0
    usage = [fields_used(m, field_names) for m in methods]
    pairs = list(combinations(usage, 2))
    disjoint = sum(1 for a, b in pairs if not (a & b))
    return round(disjoint / len(pairs), 4)


def coupled_types(cls) -> set[str]:
    type_params = {p.name for p in (cls.type_parameters or [])}
    names: set[str] = set()
    for _, node in cls:
        if isinstance(node, T.ReferenceType):
            names.add(node.name)
        elif isinstance(node, T.ClassCreator) and isinstance(node.type, T.ReferenceType):
            names.add(node.type.name)
    return names - JDK_TYPES - type_params - {cls.name}


def extract_metrics(file_path: str | Path) -> ClassMetrics:
    """Parse one Java file and return the metrics of its primary class."""
    path = Path(file_path)
    source = path.read_text(encoding="utf-8", errors="replace")
    unit = javalang.parse.parse(source)
    cls = primary_type(unit)
    methods = list(cls.methods)
    field_names = {d.name for f in cls.fields for d in f.declarators}
    return ClassMetrics(
        file_path=str(path),
        class_name=cls.name,
        loc=len(source.splitlines()),
        sloc=_count_sloc(source),
        nom=len(methods),
        noa=len(field_names),
        wmc=sum(cyclomatic_complexity(m) for m in methods),
        cbo=len(coupled_types(cls)),
        lcom=lcom(methods, field_names),
        helper_classes=len(unit.types) - 1,
        constructors=len(getattr(cls, "constructors", []) or []),
    )


if __name__ == "__main__":
    import sys

    print(f"{'class':30s} {'LOC':>5s} {'SLOC':>5s} {'NOM':>4s} {'NOA':>4s} {'WMC':>4s} {'CBO':>4s} {'LCOM':>6s}")
    for arg in sys.argv[1:]:
        p = Path(arg)
        for f in sorted(p.glob("*.java")) if p.is_dir() else [p]:
            m = extract_metrics(f)
            print(f"{m.class_name:30s} {m.loc:5d} {m.sloc:5d} {m.nom:4d} {m.noa:4d} "
                  f"{m.wmc:4d} {m.cbo:4d} {m.lcom:6.2f}")
