# Quick Start - Test Coverage

## Step 1: Activate Virtual Environment

**Windows (PowerShell):**
```powershell
cd d:\source\Python\FastAPI\adsmmpyapi
.\venv\Scripts\activate.ps1
```

**Windows (CMD):**
```cmd
cd d:\source\Python\FastAPI\adsmmpyapi
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
cd /path/to/adsmmpyapi
source venv/bin/activate
```

## Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `pytest` - Testing framework
- `pytest-cov` - Coverage plugin for pytest
- `coverage` - Coverage tool
- All other project dependencies

## Step 3: Run Tests with Coverage

```bash
# Basic coverage (terminal output)
pytest --cov=app --cov-report=term-missing

# HTML report
pytest --cov=app --cov-report=html

# All reports
pytest --cov=app --cov-report=term-missing --cov-report=html --cov-report=xml --cov-branch
```

## Step 4: View HTML Report

After running with `--cov-report=html`, open:
```
htmlcov/index.html
```

## Troubleshooting

### "pytest-cov: command not found"

**This is normal!** `pytest-cov` is a pytest plugin, not a standalone command. Use:
```bash
pytest --cov=app --cov-report=html
```

### "No module named pytest" or "No module named coverage"

1. Make sure virtual environment is activated (see Step 1)
2. Install dependencies: `pip install -r requirements.txt`

### "Could not find a version that satisfies the requirement pytest-cov"

1. Make sure you're in the virtual environment
2. Upgrade pip: `python -m pip install --upgrade pip`
3. Try installing again: `pip install pytest-cov coverage`

## Using Helper Scripts

**Windows:**
```powershell
powershell scripts/run_tests_with_coverage.ps1
```

**Linux/Mac:**
```bash
bash scripts/run_tests_with_coverage.sh
```

---

For detailed information, see [COVERAGE_SETUP.md](./COVERAGE_SETUP.md)
