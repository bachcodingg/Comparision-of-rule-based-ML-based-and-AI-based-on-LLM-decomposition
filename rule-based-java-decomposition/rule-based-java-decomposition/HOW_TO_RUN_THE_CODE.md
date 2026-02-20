# 🚀 HOW TO RUN THE CODE

## Rule-Based Java Class Decomposition Tool

**Author:** Vo Gia Bach  
**University:** Technical University of Munich (TUM), Germany  
**Advisor:** Sivajeet Chand  
**Version:** 2.0 (January 2026)

---

## 📋 Table of Contents

1. [System Requirements](#1-system-requirements)
2. [Quick Start (5 minutes)](#2-quick-start-5-minutes)
3. [Detailed Installation](#3-detailed-installation)
4. [Running the Tool](#4-running-the-tool)
5. [Understanding Output](#5-understanding-output)
6. [Troubleshooting](#6-troubleshooting)
7. [Advanced Usage](#7-advanced-usage)

---

## 1. System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| **Operating System** | Windows 10+, macOS 10.14+, Linux (Ubuntu 20.04+) |
| **Python** | Python 3.8 or higher (3.10+ recommended) |
| **RAM** | 4 GB minimum, 8 GB recommended |
| **Disk Space** | 500 MB free space |

### Required Software

- ✅ Python 3.8+ with pip
- ✅ Git (for cloning repositories)

### Optional Software

- ⚪ PMD 7.0+ (for enhanced analysis)
- ⚪ Java JDK 8+ (if analyzing local Java projects)

---

## 2. Quick Start (5 minutes)

For those who want to get started quickly:

### Windows (Command Prompt or PowerShell)

```cmd
:: Step 1: Extract the project
unzip rule-based-java-decomposition.zip
cd rule-based-java-decomposition\rule-based-java-decomposition

:: Step 2: Create virtual environment
python -m venv venv
venv\Scripts\activate

:: Step 3: Install dependencies
pip install -r requirements.txt

:: Step 4: Run the demo
python run_pipeline.py --demo
```

### macOS/Linux (Terminal)

```bash
# Step 1: Extract the project
unzip rule-based-java-decomposition.zip
cd rule-based-java-decomposition/rule-based-java-decomposition

# Step 2: Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Step 3: Install dependencies
pip install -r requirements.txt

# Step 4: Run the demo
python run_pipeline.py --demo
```

**Expected Output (Demo Mode):**
```
======================================================================
Rule-Based Java Class Decomposition Tool
Version 2.0 - Research-Based Approach (2022-2023)
======================================================================
...
Priority Score: 2.95 / 4.00
Priority Label: HIGH
God Class Candidate: Yes
...
DEMO COMPLETE!
```

---

## 3. Detailed Installation

### Step 1: Verify Python Installation

**Windows:**
```cmd
python --version
pip --version
```

**macOS/Linux:**
```bash
python3 --version
pip3 --version
```

Expected: `Python 3.8.x` or higher

**If Python is not installed:**
- Windows: Download from https://python.org (check "Add Python to PATH")
- macOS: `brew install python3`
- Linux: `sudo apt-get install python3 python3-pip`

### Step 2: Verify Git Installation

```bash
git --version
```

Expected: `git version 2.x.x`

**If Git is not installed:**
- Windows: Download from https://git-scm.com
- macOS: `brew install git` or install Xcode Command Line Tools
- Linux: `sudo apt-get install git`

### Step 3: Extract Project Files

**Option A: From ZIP file**
```bash
# Extract the ZIP
unzip rule-based-java-decomposition.zip
cd rule-based-java-decomposition/rule-based-java-decomposition
```

**Option B: From Git repository (if available)**
```bash
git clone [repository-url]
cd rule-based-java-decomposition
```

### Step 4: Verify Project Structure

After extraction, you should see:
```
rule-based-java-decomposition/
├── config.yaml           # Configuration file
├── run_pipeline.py       # Main entry point
├── requirements.txt      # Python dependencies
├── README.md             # Project documentation
├── test_setup.py         # Setup verification script
├── src/                  # Source code
│   ├── analyzer/         # Rule analysis modules
│   ├── decomposer/       # Decomposition modules
│   ├── metrics/          # Metric extraction
│   └── utils/            # Utilities
├── data/
│   └── sample/           # Sample Java files
├── results/              # Output directory
└── docs/                 # Documentation
```

### Step 5: Create Virtual Environment (Recommended)

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` prefix in your terminal.

### Step 6: Install Dependencies

```bash
pip install -r requirements.txt
```

Expected output:
```
Successfully installed pandas numpy pyyaml matplotlib seaborn jinja2 ...
```

### Step 7: Verify Installation

```bash
python test_setup.py
```

Expected output:
```
==================================================
Rule-Based Java Decomposition - Setup Check
==================================================

Python Version:
------------------------------
✓ Python 3.x.x

Dependencies:
------------------------------
✓ pandas
✓ numpy
✓ yaml
...

==================================================
✓ All checks passed. Ready to run!
==================================================
```

---

## 4. Running the Tool

### Available Commands

| Command | Description |
|---------|-------------|
| `python run_pipeline.py --demo` | Run demo on sample file |
| `python run_pipeline.py --all` | Run complete pipeline |
| `python run_pipeline.py --extract` | Extract metrics only |
| `python run_pipeline.py --analyze` | Run analysis only |
| `python run_pipeline.py --prioritize` | Calculate priorities only |
| `python run_pipeline.py --report` | Generate HTML report |
| `python run_pipeline.py --help` | Show all options |

### Demo Mode (Recommended First Step)

```bash
python run_pipeline.py --demo
```

This analyzes the sample `UserService.java` file and demonstrates:
1. **Metric Extraction** - Calculates LOC, NOM, WMC, CBO, LCOM
2. **Priority Scoring** - Assigns severity levels and calculates priority
3. **God Class Detection** - Determines if class needs refactoring
4. **Recommendations** - Provides actionable suggestions

### Analyzing Sample Files

The tool includes example files at different severity levels in `data/sample/`:

| File | Expected Severity |
|------|-------------------|
| `Example_1_LOW_EmailValidator.java` | LOW (Score: ~1.0) |
| `Example_2_MEDIUM_OrderProcessor.java` | MEDIUM (Score: ~1.5-2.0) |
| `Example_3_HIGH_InventoryManagementSystem.java` | HIGH (Score: ~2.5-3.0) |
| `Example_4_CRITICAL_EnterpriseResourcePlanner.java` | CRITICAL (Score: ~3.5-4.0) |

### Analyzing Your Own Files

1. **Place your Java files** in `data/sample/` directory
2. **Edit config.yaml** to point to your files
3. **Run the analysis:**
   ```bash
   python run_pipeline.py --analyze
   ```

### Full Pipeline (For Repository Analysis)

To analyze complete repositories:

1. **Configure repositories** in `config.yaml`:
   ```yaml
   data:
     repositories:
       - name: my-project
         url: https://github.com/user/my-project.git
   ```

2. **Run all phases:**
   ```bash
   python run_pipeline.py --all
   ```

---

## 5. Understanding Output

### Priority Score Interpretation

| Score Range | Label | Action Required |
|-------------|-------|-----------------|
| 0.0 - 1.0 | **LOW** | No immediate action needed |
| 1.0 - 2.0 | **MEDIUM** | Monitor for future growth |
| 2.0 - 3.0 | **HIGH** | Refactor when time permits |
| 3.0 - 4.0 | **CRITICAL** | Urgent refactoring required |

### Severity Thresholds

Based on recent research (2022-2023):

| Metric | LOW | MEDIUM | HIGH | CRITICAL |
|--------|-----|--------|------|----------|
| **LOC** | ≤200 | 201-500 | 501-1000 | >1000 |
| **NOM** | ≤10 | 11-20 | 21-40 | >40 |
| **WMC** | ≤30 | 31-60 | 61-100 | >100 |
| **CBO** | ≤5 | 6-10 | 11-20 | >20 |
| **LCOM** | ≤0.4 | 0.41-0.7 | 0.71-0.9 | >0.9 |

### God Class Detection Rule

A class is flagged as a **God Class candidate** when:
- **2 or more metrics** are at HIGH or CRITICAL severity

### Output Files

After running, check these directories:

- `results/demo_output/` - Demo results (JSON format)
- `results/reports/` - Analysis reports
- `results/charts/` - Visualization charts
- `logs/` - Execution logs

---

## 6. Troubleshooting

### Common Issues and Solutions

#### Issue 1: "python" command not found

**Solution (Windows):**
```cmd
:: Use py launcher
py --version
py run_pipeline.py --demo
```

**Solution (macOS/Linux):**
```bash
# Use python3 explicitly
python3 --version
python3 run_pipeline.py --demo
```

#### Issue 2: pip install fails with permission error

**Solution:**
```bash
# Use --user flag
pip install -r requirements.txt --user

# Or use virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

#### Issue 3: "Module not found" error

**Solution:**
```bash
# Ensure you're in the correct directory
cd rule-based-java-decomposition/rule-based-java-decomposition

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

#### Issue 4: "Config file not found" error

**Solution:**
```bash
# Check you're in the correct directory
ls config.yaml  # Should show the file

# If not, navigate to the correct location
cd rule-based-java-decomposition/rule-based-java-decomposition
```

#### Issue 5: Virtual environment activation fails (Windows)

**Solution:**
```cmd
:: If you get execution policy error
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

:: Then try again
venv\Scripts\activate
```

#### Issue 6: "PMD not found" warning

This is **optional** - the tool works without PMD. To install PMD:
1. Download from https://pmd.github.io
2. Add PMD to your PATH
3. Verify: `pmd --version`

### Getting Help

If you encounter issues:

1. **Check the logs:** `logs/analysis.log`
2. **Run setup test:** `python test_setup.py`
3. **Check Python version:** Must be 3.8+
4. **Verify dependencies:** `pip list`

---

## 7. Advanced Usage

### Custom Configuration

Edit `config.yaml` to customize:

```yaml
# Threshold customization
thresholds:
  loc:
    low: 200
    medium: 500
    high: 1000
  # ... other metrics

# Metric weights
weights:
  loc: 0.25
  wmc: 0.25
  cbo: 0.20
  lcom: 0.15
  nom: 0.15

# Output settings
output:
  results_dir: "results"
  generate_charts: true
  generate_report: true
```

### Batch Analysis

To analyze multiple files:

```bash
# Create a list of files
echo "data/sample/Example_1_LOW_EmailValidator.java" > files.txt
echo "data/sample/Example_2_MEDIUM_OrderProcessor.java" >> files.txt

# Run batch analysis
python run_pipeline.py --analyze --batch files.txt
```

### Integration with CI/CD

Example GitHub Actions workflow:

```yaml
name: Code Quality Check
on: [push, pull_request]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: python run_pipeline.py --analyze
```

### Research References

This tool is based on:

1. **Dewangan et al. (2023)** - 4-level severity classification
2. **Verma et al. (2023)** - Priority scoring approach  
3. **Rao et al. (2023)** - Empirical threshold validation
4. **Gupta & Chauhan (2022)** - Java-specific assessment

---

## 📞 Support

**Author:** Vo Gia Bach  
**University:** Technical University of Munich (TUM), Germany  
**Advisor:** Sivajeet Chand

For questions or issues, please refer to the project documentation or contact through university channels.

---

*Last Updated: January 2026*
