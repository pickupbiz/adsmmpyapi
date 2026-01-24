# PowerShell script to set up virtual environment and install dependencies

Write-Host "Setting up virtual environment and installing dependencies..." -ForegroundColor Green

# Navigate to project directory
$projectDir = Split-Path -Parent $PSScriptRoot
Set-Location $projectDir

# Check if venv exists, create if not
if (-not (Test-Path "venv\Scripts\activate.ps1")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    
    if (-not (Test-Path "venv\Scripts\activate.ps1")) {
        Write-Host "ERROR: Failed to create virtual environment!" -ForegroundColor Red
        exit 1
    }
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\activate.ps1

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet

# Install dependencies
Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor Yellow
python -m pip install -r requirements.txt

# Verify installation
Write-Host "`nVerifying installation..." -ForegroundColor Yellow
python -c "import sqlalchemy; print(f'SQLAlchemy version: {sqlalchemy.__version__}')" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: SQLAlchemy not installed correctly!" -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ Setup complete! Virtual environment is ready." -ForegroundColor Green
Write-Host "`nTo activate the virtual environment in the future, run:" -ForegroundColor Cyan
Write-Host "  .\venv\Scripts\activate.ps1" -ForegroundColor White
Write-Host "`nTo run the application:" -ForegroundColor Cyan
Write-Host "  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 5055" -ForegroundColor White
