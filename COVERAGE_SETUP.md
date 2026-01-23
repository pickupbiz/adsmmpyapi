# Test Coverage Setup Guide

This guide explains how to set up and use test coverage for the Aerospace Parts Material Management API.

## Installation

### 1. Activate Virtual Environment

**Windows (PowerShell):**
```powershell
# Navigate to project directory
cd d:\source\Python\FastAPI\adsmmpyapi

# Activate virtual environment
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

### 2. Install Coverage Dependencies

```bash
# Install from requirements.txt (includes pytest-cov and coverage)
pip install -r requirements.txt

# Or install manually
pip install pytest-cov coverage
```

### 3. Verify Installation

```bash
# Check pytest version
pytest --version

# Check if pytest-cov plugin is available (run a test with coverage to verify)
pytest --help | grep -i cov

# Check coverage version
coverage --version

# Or verify via pip
pip show pytest-cov
pip show coverage
```

**Note:** `pytest-cov` is a pytest plugin, not a standalone command. You cannot run `pytest-cov --version` directly. Use `pytest --cov=app` to use the plugin.

## Running Tests with Coverage

### Basic Coverage Commands

```bash
# Run tests with coverage (terminal output only)
pytest --cov=app --cov-report=term-missing

# Run tests with coverage (HTML report)
pytest --cov=app --cov-report=html

# Run tests with coverage (all report formats)
pytest --cov=app --cov-report=term-missing --cov-report=html --cov-report=xml --cov-branch
```

### Using Helper Scripts

**Linux/Mac:**
```bash
bash scripts/run_tests_with_coverage.sh
```

**Windows (PowerShell):**
```powershell
powershell scripts/run_tests_with_coverage.ps1
```

### Coverage Report Formats

1. **Terminal Output** (`--cov-report=term-missing`)
   - Shows coverage percentage and missing lines
   - Displays in the terminal after tests run

2. **HTML Report** (`--cov-report=html`)
   - Generates interactive HTML report
   - Location: `htmlcov/index.html`
   - Open in browser to see detailed line-by-line coverage

3. **XML Report** (`--cov-report=xml`)
   - Generates `coverage.xml`
   - Useful for CI/CD integration
   - Compatible with tools like Codecov, Coveralls

4. **Branch Coverage** (`--cov-branch`)
   - Analyzes branch coverage (if/else, try/except, etc.)
   - Provides more detailed coverage metrics

## Coverage Configuration

### Configuration File: `.coveragerc`

The `.coveragerc` file configures:
- **Source directories**: Only `app/` is measured
- **Exclusions**: Tests, migrations, scripts, venv are excluded
- **Report settings**: HTML and XML output locations

### Viewing Coverage Reports

**HTML Report:**
```bash
# After running with --cov-report=html
# Open in browser:
# - Linux/Mac: open htmlcov/index.html
# - Windows: start htmlcov/index.html
# - Or navigate to htmlcov/index.html manually
```

**Terminal Report:**
- Automatically displayed when using `--cov-report=term-missing`
- Shows coverage percentage per module
- Lists missing lines

## Coverage Goals

### Current Coverage Areas

✅ **Well Covered:**
- Purchase Order workflows
- Material receipt validation
- PO status transitions
- Role-based access control
- Dashboard and reporting

📊 **Coverage Metrics:**
- Run `pytest --cov=app --cov-report=term-missing` to see current coverage

### Improving Coverage

1. **Identify Gaps:**
   ```bash
   pytest --cov=app --cov-report=html
   # Open htmlcov/index.html and look for red lines
   ```

2. **Focus on Critical Paths:**
   - Authentication and authorization
   - PO approval workflows
   - Material lifecycle management
   - Error handling

3. **Add Tests for:**
   - Edge cases
   - Error conditions
   - Boundary values
   - Integration scenarios

## Troubleshooting

### Issue: "pytest-cov not found" or "No module named pytest"

**Solution:**
1. **Activate virtual environment first:**
   ```powershell
   # Windows PowerShell
   .\venv\Scripts\activate.ps1
   
   # Windows CMD
   venv\Scripts\activate.bat
   
   # Linux/Mac
   source venv/bin/activate
   ```

2. **Install packages:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation:**
   ```bash
   pip show pytest-cov
   pip show coverage
   pytest --version
   ```

**Note:** If you see "pytest-cov: command not found", remember that `pytest-cov` is a pytest plugin, not a standalone command. Use `pytest --cov=app` instead.

### Issue: Coverage shows 0%

**Possible Causes:**
1. Source path is incorrect
2. Tests aren't importing the app modules
3. Coverage configuration excludes source files

**Solution:**
- Check `.coveragerc` source path
- Verify `--cov=app` matches your app directory name
- Check that tests import from `app` module

### Issue: Coverage includes test files

**Solution:**
- Check `.coveragerc` omit patterns
- Ensure test files are excluded in configuration

### Issue: HTML report not generated

**Solution:**
```bash
# Ensure htmlcov directory exists
mkdir -p htmlcov

# Run with HTML report option
pytest --cov=app --cov-report=html
```

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Run tests with coverage
  run: |
    pip install -r requirements.txt
    pytest --cov=app --cov-report=xml --cov-report=html

- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

### GitLab CI Example

```yaml
test:
  script:
    - pip install -r requirements.txt
    - pytest --cov=app --cov-report=xml
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

## Best Practices

1. **Run Coverage Regularly:**
   - Before committing code
   - In CI/CD pipeline
   - Before releases

2. **Aim for High Coverage:**
   - Target: 80%+ overall coverage
   - Critical paths: 90%+ coverage
   - Focus on business logic, not just lines

3. **Review Coverage Reports:**
   - Check HTML reports for detailed analysis
   - Identify untested code paths
   - Add tests for critical missing coverage

4. **Use Branch Coverage:**
   - Enable `--cov-branch` for better analysis
   - Identifies untested code branches

## Additional Resources

- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Test Coverage Best Practices](https://martinfowler.com/bliki/TestCoverage.html)

---

**Last Updated:** January 23, 2026
