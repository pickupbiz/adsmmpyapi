# PowerShell script to run the FastAPI application

Write-Host "Starting FastAPI application..." -ForegroundColor Green

# Navigate to project directory
$projectDir = Split-Path -Parent $PSScriptRoot
Set-Location $projectDir

# Check if venv exists
if (-not (Test-Path "venv\Scripts\activate.ps1")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: powershell scripts/setup_venv.ps1" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\activate.ps1

# Verify SQLAlchemy is installed
python -c "import sqlalchemy" 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Dependencies not installed!" -ForegroundColor Red
    Write-Host "Please run: powershell scripts/setup_venv.ps1" -ForegroundColor Yellow
    exit 1
}

# Run the application
Write-Host "Starting uvicorn server..." -ForegroundColor Yellow
Write-Host "Server will be available at: http://localhost:5055" -ForegroundColor Cyan
Write-Host "API docs at: http://localhost:5055/api/v1/docs" -ForegroundColor Cyan
Write-Host "`nPress Ctrl+C to stop the server`n" -ForegroundColor Yellow

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 5055
