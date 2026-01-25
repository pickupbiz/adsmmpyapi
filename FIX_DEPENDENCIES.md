# Fix: ModuleNotFoundError - Dependencies Not Installed

## Problem

You're seeing this error:
```
ModuleNotFoundError: No module named 'sqlalchemy'
```

This happens because:
1. The virtual environment is **not activated**, OR
2. Dependencies are **not installed** in the virtual environment

## Quick Fix (Windows PowerShell)

### Option 1: Use Setup Script (Recommended)

```powershell
cd d:\source\Python\FastAPI\adsmmpyapi
powershell scripts/setup_venv.ps1
```

This script will:
- Create virtual environment if it doesn't exist
- Activate it
- Install all dependencies
- Verify installation

### Option 2: Manual Setup

```powershell
# 1. Navigate to project directory
cd d:\source\Python\FastAPI\adsmmpyapi

# 2. Create virtual environment (if it doesn't exist)
python -m venv venv

# 3. Activate virtual environment
.\venv\Scripts\activate.ps1

# 4. Upgrade pip
python -m pip install --upgrade pip

# 5. Install all dependencies
pip install -r requirements.txt

# 6. Verify installation
python -c "import sqlalchemy; print('SQLAlchemy installed:', sqlalchemy.__version__)"
```

## Running the Application

### Option 1: Use Run Script (Recommended)

```powershell
powershell scripts/run_app.ps1
```

### Option 2: Manual Run

```powershell
# IMPORTANT: Activate venv first!
.\venv\Scripts\activate.ps1

# Then run
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 5055
```

## Troubleshooting

### Issue: "Execution Policy" Error

If you get an execution policy error when running `.ps1` scripts:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### Issue: "venv\Scripts\activate.ps1" Not Found

The virtual environment doesn't exist. Create it:

```powershell
python -m venv venv
.\venv\Scripts\activate.ps1
pip install -r requirements.txt
```

### Issue: Still Getting ModuleNotFoundError After Activation

1. **Verify you're in the venv:**
   ```powershell
   # Your prompt should show (venv) at the beginning
   # Check Python path:
   python -c "import sys; print(sys.executable)"
   # Should show: ...\adsmmpyapi\venv\Scripts\python.exe
   ```

2. **Reinstall dependencies:**
   ```powershell
   .\venv\Scripts\activate.ps1
   pip install --force-reinstall -r requirements.txt
   ```

3. **Check if packages are installed:**
   ```powershell
   pip list | Select-String "sqlalchemy"
   ```

### Issue: Using Wrong Python Interpreter

Make sure you're using the venv Python, not system Python:

```powershell
# Wrong - uses system Python
python -m uvicorn app.main:app

# Correct - activate venv first
.\venv\Scripts\activate.ps1
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 5055
```

## Verification Checklist

After setup, verify everything works:

```powershell
# 1. Activate venv
.\venv\Scripts\activate.ps1

# 2. Check Python path (should be in venv)
python -c "import sys; print(sys.executable)"

# 3. Check key packages
python -c "import sqlalchemy; print('SQLAlchemy:', sqlalchemy.__version__)"
python -c "import fastapi; print('FastAPI:', fastapi.__version__)"
python -c "import uvicorn; print('Uvicorn:', uvicorn.__version__)"

# 4. Try importing your app
python -c "from app.main import app; print('App imported successfully!')"
```

## Best Practices

1. **Always activate venv before running:**
   ```powershell
   .\venv\Scripts\activate.ps1
   ```

2. **Use the helper scripts:**
   - `scripts/setup_venv.ps1` - One-time setup
   - `scripts/run_app.ps1` - Run application (auto-activates venv)

3. **Check your prompt:**
   - When venv is active, you should see `(venv)` at the start of your prompt

4. **If in doubt, reactivate:**
   ```powershell
   deactivate  # if already activated
   .\venv\Scripts\activate.ps1
   ```

---

**Last Updated:** January 23, 2026
