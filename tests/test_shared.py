"""Tests for the shared metric extractor, the score bins, the synthetic data
generator, the leak check and the LLM recommendation scorer.

    python -m pytest tests -q        (from the repository root)
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT / "llm-evaluation",
          ROOT / "ml-based-java-decomposition" / "ml-based-java-decomposition" / "src",
          ROOT / "rule-based-java-decomposition" / "rule-based-java-decomposition" / "src",
          ROOT):
    sys.path.insert(0, str(p))

from common.java_metrics import extract_metrics  # noqa: E402

SAMPLE = """package demo;

import java.util.*;

/**
 * This class with many words mentions Database and Scheduler in a comment.
 */
public class Basket {
    private List<Item> items = new ArrayList<>();
    private double taxRate;
    private String label = "class Fake extends Other";

    public Basket(double taxRate) { this.taxRate = taxRate; }

    public void add(Item item) {
        if (item != null && item.price > 0) {
            items.add(item);
        }
    }

    public double total() {
        double sum = 0;
        for (Item i : items) { sum += i.price; }
        return sum * (1 + taxRate);
    }

    public String describe() { return label; }
}

class Item {
    double price;
    double discounted(double pct) { return price * (1 - pct); }
}
"""


@pytest.fixture
def sample(tmp_path):
    f = tmp_path / "Basket.java"
    f.write_text(SAMPLE, encoding="utf-8")
    return f


def test_metrics_refer_to_the_primary_class_only(sample):
    m = extract_metrics(sample)
    assert m.class_name == "Basket"
    assert m.nom == 3            # add, total, describe; not Item.discounted, not the constructor
    assert m.noa == 3
    assert m.helper_classes == 1
    assert m.constructors == 1


def test_complexity_counts_branches_and_boolean_operators(sample):
    # add: 1 + if + &&  = 3;  total: 1 + for = 2;  describe: 1
    assert extract_metrics(sample).wmc == 6


def test_coupling_ignores_comments_strings_and_jdk_types(sample):
    assert extract_metrics(sample).cbo == 1   # Item only


def test_lcom_is_share_of_method_pairs_without_a_common_field(sample):
    # add{items}, total{items,taxRate}, describe{label}: pairs sharing a field = 1 of 3
    assert extract_metrics(sample).lcom == pytest.approx(2 / 3, abs=1e-4)


def test_loc_and_sloc(sample):
    m = extract_metrics(sample)
    assert m.loc == len(SAMPLE.splitlines())
    assert m.sloc < m.loc


def test_score_bins_label_the_nearest_level():
    from analyzer.priority_scorer import priority_label_for
    assert [priority_label_for(s) for s in (1.0, 1.49, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0)] == \
        ["LOW", "LOW", "MEDIUM", "MEDIUM", "HIGH", "HIGH", "CRITICAL", "CRITICAL"]
    # the earlier cut-offs could not produce LOW for any reachable score
    assert priority_label_for(1.0, legacy_bins=True) == "MEDIUM"


def test_all_metrics_at_one_level_score_that_level():
    from analyzer.priority_scorer import SeverityBasedScorer
    score, details = SeverityBasedScorer().calculate_priority(
        {"loc": 50, "nom": 3, "wmc": 5, "cbo": 1, "lcom": 0.1})
    assert score == pytest.approx(1.0)
    assert details["priority_label"] == "LOW"


def test_synthetic_generator_shape_seed_and_proportions():
    from models.ml_classifier import FEATURES, generate_synthetic_training_data
    X, y = generate_synthetic_training_data(400, random_state=1)
    X2, y2 = generate_synthetic_training_data(400, random_state=1)
    assert X.shape == (400, len(FEATURES)) and (X == X2).all() and (y == y2).all()
    assert "cyclomatic" not in FEATURES
    _, y3 = generate_synthetic_training_data(400, random_state=1, class_proportions=[0.6, 0.25, 0.1, 0.05])
    assert [int((y3 == k).sum()) for k in range(4)] == [240, 100, 40, 20]


def test_leak_check_flags_answer_revealing_comments(tmp_path):
    from leak_check import find_leaks
    leaky = tmp_path / "Example_4_CRITICAL_Planner.java"
    leaky.write_text("/** CRITICAL SEVERITY EXAMPLE\\n * Expected Result: urgent */\\nclass Planner {}", encoding="utf-8")
    clean = tmp_path / "Planner.java"
    clean.write_text("/** Plans things. */\\nclass Planner {}", encoding="utf-8")
    assert len(find_leaks(leaky)) >= 2
    assert find_leaks(clean) == []


def test_blind_dataset_has_no_leaks_and_matches_labels():
    import csv
    from leak_check import find_leaks
    files = sorted((ROOT / "dataset" / "blind").glob("*.java"))
    assert len(files) == 6
    assert all(find_leaks(f) == [] for f in files)
    with open(ROOT / "dataset" / "labels.csv", newline="", encoding="utf-8") as fh:
        labelled = {row["class_name"] for row in csv.DictReader(fh)}
    assert labelled == {f.stem for f in files}


def test_recommendation_scoring_counts_invented_and_covered_methods(sample):
    from java_methods import parse_java
    from score import score_recommendation
    answer = {
        "proposed_classes": [
            {"name": "A", "methods": ["add", "Basket.total(double)"]},
            {"name": "B", "methods": ["total", "refund"]},
        ],
        "methods_kept": ["describe"],
    }
    r = score_recommendation(answer, parse_java(sample))
    assert r["methods_distinct"] == 3 and r["methods_exist"] == 2
    assert r["methods_invented"] == ["refund"]
    assert r["existence_rate"] == pytest.approx(2 / 3, abs=1e-4)
    assert r["coverage"] == pytest.approx(2 / 3, abs=1e-4)
    assert r["accounted"] == 1.0
    assert r["duplicates"] == ["total"]
