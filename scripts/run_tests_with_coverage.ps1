# PowerShell script to run tests with coverage reporting

Write-Host "Running tests with coverage..." -ForegroundColor Green

# Activate virtual environment if it exists
if (Test-Path "venv\Scripts\activate.ps1") {
    & .\venv\Scripts\activate.ps1
} elseif (Test-Path ".venv\Scripts\activate.ps1") {
    & .\.venv\Scripts\activate.ps1
}

# Install/upgrade coverage dependencies
Write-Host "Installing coverage dependencies..." -ForegroundColor Yellow
python -m pip install -q --upgrade pip
python -m pip install -q pytest-cov coverage

# Run tests with coverage
Write-Host "Running pytest with coverage..." -ForegroundColor Yellow
pytest `
    --cov=app `
    --cov-report=term-missing `
    --cov-report=html `
    --cov-report=xml `
    --cov-branch `
    -v

Write-Host ""
Write-Host "Coverage reports generated:" -ForegroundColor Green
Write-Host "  - Terminal: Shown above"
Write-Host "  - HTML: htmlcov\index.html"
Write-Host "  - XML: coverage.xml"
Write-Host ""
Write-Host "To view HTML report, open htmlcov\index.html in your browser" -ForegroundColor Cyan
