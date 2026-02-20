# How the Rule-Based Java Decomposition Project Works
## Complete System Explanation

---

## 🎯 Project Goal

This project implements a **rule-based approach** for detecting Java classes that should be decomposed (split into smaller classes). Unlike ML or AI approaches, rule-based detection:

- Uses **explicit, configurable rules** that are transparent and explainable
- Combines **PMD static analysis** with **custom threshold rules**
- Provides **priority scoring** to rank decomposition candidates
- Runs **fast** (seconds, not minutes)

---

## 📁 Project Structure Explained

```
rule-based-java-decomposition/
│
├── config.yaml                 ← ALL SETTINGS LIVE HERE
│
├── run_pipeline.py             ← MAIN ENTRY POINT
│
├── src/                        ← SOURCE CODE
│   ├── analyzer/
│   │   └── rule_analyzer.py    ← Core rule engine
│   ├── metrics/
│   │   └── metric_extractor.py ← Metric extraction
│   ├── rules/
│   │   └── pmd_rules.xml       ← PMD ruleset
│   └── utils/
│       ├── data_collector.py   ← Repository cloning
│       └── report_generator.py ← HTML reports
│
├── data/
│   ├── raw/                    ← Cloned repositories
│   ├── processed/              ← Extracted metrics (CSV)
│   └── sample/                 ← Test data
│
├── results/
│   ├── charts/                 ← Visualization PNGs
│   └── reports/                ← HTML reports
│
├── notebooks/                  ← Jupyter analysis
├── docker/                     ← Container setup
└── tests/                      ← Unit tests
```

---

## 🔄 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           PHASE 1: DATA COLLECTION                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   GitHub Repos ──────► Clone to data/raw/                               │
│        │                                                                 │
│        ▼                                                                 │
│   ┌─────────────────────────────────────────────┐                       │
│   │        MetricExtractor                       │                       │
│   │   (Extracts: LOC, NOM, WMC, CBO, LCOM...)   │                       │
│   └─────────────────────────────────────────────┘                       │
│        │                                                                 │
│        ▼                                                                 │
│   data/processed/code_metrics.csv                                        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                          PHASE 2: RULE-BASED ANALYSIS                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   code_metrics.csv                                                       │
│         │                                                                │
│         ├──────────────────┬──────────────────┬─────────────────────────┤
│         ▼                  ▼                  ▼                          │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐                │
│   │  PMD RULES   │   │  THRESHOLD   │   │  COMPOSITE   │                │
│   │              │   │    RULES     │   │    RULES     │                │
│   │  GodClass    │   │              │   │              │                │
│   │  Excessive   │   │  LOC > 500   │   │ LargeClass   │                │
│   │  ClassLength │   │  NOM > 20    │   │ Candidate    │                │
│   │  TooMany     │   │  WMC > 60    │   │ (2+ metrics) │                │
│   │  Methods     │   │  CBO > 15    │   │              │                │
│   │  etc.        │   │  LCOM > 0.7  │   │ GodClass     │                │
│   │              │   │              │   │ Candidate    │                │
│   └──────────────┘   └──────────────┘   └──────────────┘                │
│         │                  │                  │                          │
│         └──────────────────┴──────────────────┘                          │
│                            │                                             │
│                            ▼                                             │
│                  ┌─────────────────────┐                                │
│                  │  COMBINE & SCORE    │                                │
│                  │                     │                                │
│                  │  Calculate priority │                                │
│                  │  score for each     │                                │
│                  │  flagged class      │                                │
│                  └─────────────────────┘                                │
│                            │                                             │
│                            ▼                                             │
│              results/analysis_results.csv                                │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                          PHASE 3: REPORTING                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   analysis_results.csv                                                   │
│         │                                                                │
│         ├──────────────────┬──────────────────┬─────────────────────────┤
│         ▼                  ▼                  ▼                          │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐                │
│   │ HTML REPORT  │   │   CHARTS     │   │    JSON      │                │
│   │              │   │              │   │   SUMMARY    │                │
│   │ Formatted    │   │ Bar charts   │   │              │                │
│   │ tables,      │   │ Histograms   │   │ Machine-     │                │
│   │ summaries    │   │ Heatmaps     │   │ readable     │                │
│   └──────────────┘   └──────────────┘   └──────────────┘                │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 File-by-File Explanation

### `config.yaml` - Central Configuration
```yaml
# Repositories to analyze
data:
  repositories:
    - name: "commons-lang"
      url: "https://github.com/apache/commons-lang.git"

# Rule thresholds with severity levels
rules:
  thresholds:
    lines_of_code:
      warning: 300      # Yellow flag
      critical: 500     # Orange flag
      severe: 1000      # Red flag
    number_of_methods:
      warning: 15
      critical: 20
      severe: 35

# Composite rules (combine multiple metrics)
  composite_rules:
    - name: "GodClassCandidate"
      conditions:
        min_violations: 3
        metrics:
          - "lines_of_code >= warning"
          - "number_of_methods >= warning"
          - "coupling_between_objects >= warning"
```

### `run_pipeline.py` - Main Entry Point
```python
# Orchestrates the entire pipeline:
# 1. Collects data (clones repos, extracts metrics)
# 2. Runs PMD analysis
# 3. Runs threshold analysis
# 4. Runs composite rule analysis
# 5. Combines results and calculates priority scores
# 6. Generates reports

python run_pipeline.py --all  # Run everything
```

---

### `src/analyzer/rule_analyzer.py`
**Purpose:** Core rule engine that detects decomposition candidates

```
Input:  data/processed/code_metrics.csv
Output: results/analysis_results.csv

Three analysis types:
┌────────────────────────────────────────────────────────────────┐
│ 1. PMD Analysis                                                │
│    - Runs PMD with pmd_rules.xml                              │
│    - Detects: GodClass, ExcessiveClassLength, TooManyMethods  │
│    - Falls back to regex-based analysis if PMD not installed  │
├────────────────────────────────────────────────────────────────┤
│ 2. Threshold Analysis                                          │
│    - Checks each metric against warning/critical/severe levels│
│    - Records which thresholds are exceeded                     │
├────────────────────────────────────────────────────────────────┤
│ 3. Composite Analysis                                          │
│    - Evaluates multi-metric rules                              │
│    - Example: "GodClassCandidate" needs 3+ violations         │
└────────────────────────────────────────────────────────────────┘
```

### `src/metrics/metric_extractor.py`
**Purpose:** Extract software metrics from Java files

```
Input:  data/raw/*/**.java
Output: data/processed/code_metrics.csv

Metrics extracted:
┌────────────────────────────────────────────────────────────────┐
│ Metric │ Name                          │ How Calculated       │
├────────────────────────────────────────────────────────────────┤
│ LOC    │ Lines of Code                 │ Non-blank, non-comment│
│ NOM    │ Number of Methods             │ Count method sigs    │
│ NOF    │ Number of Fields              │ Count field decls    │
│ CC     │ Cyclomatic Complexity         │ Branching statements │
│ WMC    │ Weighted Methods per Class    │ Sum of method CCs    │
│ CBO    │ Coupling Between Objects      │ Type references      │
│ LCOM   │ Lack of Cohesion of Methods   │ Field sharing ratio  │
│ DIT    │ Depth of Inheritance Tree     │ Inheritance depth    │
│ RFC    │ Response for a Class          │ Methods + calls      │
└────────────────────────────────────────────────────────────────┘
```

### `src/rules/pmd_rules.xml`
**Purpose:** PMD ruleset configuration

```xml
<ruleset name="LargeClassDetection">
    <!-- God Class Detection -->
    <rule ref="category/java/design.xml/GodClass"/>
    
    <!-- Size Metrics -->
    <rule ref="category/java/design.xml/ExcessiveClassLength">
        <properties>
            <property name="minimum" value="500"/>
        </properties>
    </rule>
    
    <!-- Complexity Metrics -->
    <rule ref="category/java/design.xml/CyclomaticComplexity">
        <properties>
            <property name="classReportLevel" value="50"/>
        </properties>
    </rule>
</ruleset>
```

---

## 🏃 Running the Pipeline

### Option 1: Complete Pipeline
```bash
python run_pipeline.py --all
```
This runs everything in sequence (~1-2 minutes per repository)

### Option 2: Step by Step
```bash
# Step 1: Clone repos and extract metrics
python run_pipeline.py --collect

# Step 2: Run rule-based analysis
python run_pipeline.py --analyze

# Step 3: Generate reports
python run_pipeline.py --report
```

### Option 3: Docker
```bash
cd docker
docker-compose up analyzer
```

---

## 📊 Output Files

After running, you'll find:

```
results/
├── analysis_results.csv      ← Main result: all flagged classes
├── pmd_violations.csv        ← PMD rule violations
├── threshold_violations.csv  ← Threshold violations
├── composite_violations.csv  ← Composite rule matches
├── evaluation_metrics.json   ← Precision, recall, F1
├── analysis_summary.json     ← Summary statistics
├── charts/
│   ├── violations_by_repo.png
│   ├── score_distribution.png
│   └── correlation_matrix.png
└── reports/
    └── report_YYYYMMDD.html  ← Full HTML report
```

---

## 🔑 Key Concepts

### Priority Scoring Formula

Classes are ranked by a weighted priority score:

```
Priority = 0.25 × LOC_score 
         + 0.25 × WMC_score 
         + 0.20 × CBO_score 
         + 0.15 × LCOM_score 
         + 0.15 × NOM_score

Where each metric_score is:
  - 5 if metric >= severe threshold
  - 3 if metric >= critical threshold
  - 1 if metric >= warning threshold
  - 0 otherwise
```

### Severity Weights

| Severity | Weight | Description |
|----------|--------|-------------|
| Warning  | 1      | Minor issue, could be improved |
| Critical | 3      | Significant problem |
| Severe   | 5      | Urgent refactoring needed |

### Why Rule-Based?

| Aspect | Rule-Based | ML | AI/LLM |
|--------|------------|-----|--------|
| **Speed** | ⚡ Fast (seconds) | ⚡ Fast | 🐢 Slow (minutes) |
| **Explainability** | ✅ High | ❌ Low | ❌ Low |
| **Setup Cost** | ✅ Low | 🔶 Medium | 🔶 Medium |
| **Data Needed** | ✅ None | ❌ Training data | ✅ None |
| **Customizable** | ✅ Easy | 🔶 Retrain | 🔶 Prompt eng |

---

## 🚀 Quick Start Commands

```bash
# 1. Verify setup
python test_setup.py

# 2. Run on sample data (included)
python run_pipeline.py --analyze

# 3. View results
cat results/analysis_results.csv

# 4. Open HTML report
open results/reports/report_*.html

# 5. Explore in Jupyter
jupyter notebook notebooks/analysis.ipynb
```

---

## 📚 For Your Thesis

This project supports writing about:

1. **Chapter 3 (Methodology):** Reference `config.yaml` for threshold values
2. **Chapter 4 (Implementation):** Point to specific modules in `src/`
3. **Chapter 5 (Results):** Use CSVs and charts from `results/`
4. **Reproducibility:** Docker setup ensures others can replicate

---

## ❓ Common Questions

### Q: PMD is not installed. Will it still work?
**A:** Yes! The analyzer has a built-in fallback that uses regex-based detection when PMD is unavailable.

### Q: How do I add my own repository?
**A:** Edit `config.yaml` and add to the `repositories` list:
```yaml
- name: "my-project"
  url: "https://github.com/me/my-project.git"
  branch: "main"
```

### Q: How do I change the thresholds?
**A:** Edit the `thresholds` section in `config.yaml`. Lower values = more sensitive detection.

### Q: What if I only want to analyze LOC and NOM?
**A:** Disable other rules in `config.yaml` under `rules.pmd.rules` and adjust composite rules accordingly.

---

## 🎯 Sample Output

```
=====================================
RULE-BASED ANALYSIS SUMMARY
=====================================

Total classes analyzed: 1,470
Classes flagged for decomposition: 127
Percentage flagged: 8.6%

Top 5 Priority Classes:
=====================================
1. DataProcessor (score: 4.25)
   LOC: 1250, Methods: 45, WMC: 554
   Violations: ExcessiveClassLength, TooManyMethods, GodClassCandidate

2. TransactionManager (score: 3.85)
   LOC: 1045, Methods: 40, WMC: 448
   Violations: ExcessiveClassLength, TooManyMethods, HighComplexity

3. SearchEngine (score: 3.50)
   LOC: 1120, Methods: 42, WMC: 454
   Violations: ExcessiveClassLength, GodClassCandidate
...
=====================================
```
