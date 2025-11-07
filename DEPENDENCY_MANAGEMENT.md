# 📦 Dependency Management Guide

## Why Dependencies Get "Lost"

### Understanding Python Package Installation

**Python packages are NOT installed globally** - they're installed **per Python environment**. This means:

1. **Each Python installation has its own packages**
   - Python 3.10 vs Python 3.11 vs Python 3.14 have separate package locations
   - `C:\Python310\Lib\site-packages\` vs `C:\Python314\Lib\site-packages\`

2. **Virtual environments isolate packages**
   - If you use `venv` or `virtualenv`, packages are isolated to that environment
   - Activating the environment is required to access those packages

3. **System restore or Windows updates**
   - Can reset Python package locations
   - May require re-installation

4. **Multiple Python installations**
   - Different Python versions on the same system have separate packages
   - `python` command might point to a different Python than expected

### How to Detect Missing Dependencies

**Python Backend:**
```bash
# If you see this error:
ModuleNotFoundError: No module named 'fastapi'

# It means FastAPI is not installed in the Python environment you're using
```

**Node.js Frontend:**
```bash
# If you see this error:
Error: Cannot find module 'next'

# It means Next.js is not installed (node_modules folder missing or incomplete)
```

## Solutions

### Automated Solution (Recommended)

**Double-click `start-dev.bat`** - This script:
1. Checks if Python and Node.js are installed
2. Detects missing dependencies
3. Installs them automatically
4. Starts both servers

### Manual Solution

**Step 1: Check what's missing**
```bash
# Double-click check-dependencies.bat
# Or manually:
python -c "import fastapi; print('FastAPI OK')" 2>nul || echo "FastAPI missing"
dir node_modules\next >nul 2>&1 && echo "Next.js OK" || echo "Next.js missing"
```

**Step 2: Install Python dependencies**
```bash
# Install all Python packages from requirements.txt
pip install -r requirements.txt

# Or use python -m pip to ensure correct Python
python -m pip install -r requirements.txt

# Verify installation
python -c "import fastapi, uvicorn, pandas; print('All packages OK')"
```

**Step 3: Install Node.js dependencies**
```bash
# Install all Node.js packages from package.json
npm install

# Verify installation
dir node_modules\next >nul 2>&1 && echo "Next.js installed" || echo "Installation failed"
```

## Troubleshooting

### "ModuleNotFoundError" but packages show as installed

**Problem**: Using a different Python than where packages are installed

**Solution**:
```bash
# Check which Python you're using
python --version
where python

# Check where packages are installed
python -c "import sys; print(sys.path)"

# Install using the same Python
python -m pip install -r requirements.txt
```

### Packages installed but still getting errors

**Problem**: Python environment changed or virtual environment not activated

**Solution**:
```bash
# If using virtual environment, activate it first
# venv\Scripts\activate  (Windows)
# source venv/bin/activate  (Linux/Mac)

# Then install packages
pip install -r requirements.txt
```

### Node modules missing after npm install

**Problem**: Installation failed or incomplete

**Solution**:
```bash
# Delete node_modules and package-lock.json
rmdir /s /q node_modules
del package-lock.json

# Reinstall
npm install
```

## Best Practices

1. **Use the automated script** (`start-dev.bat`) for consistent setup
2. **Check dependencies** before starting development (`check-dependencies.bat`)
3. **Keep requirements.txt updated** when adding new Python packages
4. **Keep package.json updated** when adding new Node.js packages
5. **Document any environment-specific setup** in team notes

## Current Project Dependencies

### Python (requirements.txt)
- FastAPI (web framework)
- Uvicorn (ASGI server)
- Pandas (data processing)
- OpenPyXL (Excel file handling)
- SQLite3 (built-in, no install needed)

### Node.js (package.json)
- Next.js (React framework)
- React & React DOM
- TypeScript
- Tailwind CSS
- Various UI libraries

## Quick Reference

```bash
# Check dependencies
check-dependencies.bat

# Start everything (automated)
start-dev.bat

# Manual Python install
pip install -r requirements.txt

# Manual Node install
npm install

# Verify Python packages
python -c "import fastapi, uvicorn, pandas; print('OK')"

# Verify Node packages
dir node_modules\next >nul 2>&1 && echo "OK" || echo "Missing"
```








