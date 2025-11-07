# Code Formatting Guide

This project uses automated code formatting to prevent indentation errors and maintain consistent style.

## Quick Setup

1. **Install Black (code formatter):**
   ```bash
   pip install black
   ```

2. **Format your code:**
   ```bash
   black src/
   ```
   Or format the entire project:
   ```bash
   black .
   ```

3. **Check for syntax errors before committing:**
   ```bash
   python format_code.py
   ```

## Preventing Indentation Errors

### Option 1: Format Before Committing (Recommended)

Always run Black before committing Python code:
```bash
black src/web/routers/admin.py
```

### Option 2: Auto-format on Save (VS Code)

1. Install the "Black Formatter" extension in VS Code
2. Add to `.vscode/settings.json`:
   ```json
   {
     "editor.formatOnSave": true,
     "editor.defaultFormatter": "ms-python.black-formatter",
     "[python]": {
       "editor.defaultFormatter": "ms-python.black-formatter"
     }
   }
   ```

### Option 3: Pre-commit Hook

Create `.git/hooks/pre-commit`:
```bash
#!/bin/sh
black --check src/ || exit 1
python -m py_compile src/**/*.py || exit 1
```

## Common Issues Fixed

- ✅ Inconsistent indentation (mixed tabs/spaces)
- ✅ Missing colons after if/else/for/try/except
- ✅ Misaligned blocks
- ✅ Line length violations

## Manual Syntax Check

Before running the server, quickly check for syntax errors:
```bash
python -m py_compile src/web/routers/admin.py
```

If no output, the file is syntactically correct!

## Configuration

Formatting settings are in `pyproject.toml`:
- Line length: 100 characters
- Target Python versions: 3.9-3.13

## Tips

1. **Always format after manual edits** - Even if you think it's correct, Black will catch subtle issues
2. **Use your IDE's formatter** - Set up auto-format on save
3. **Run the syntax checker** - Before committing, run `python format_code.py`
4. **One command fixes everything:**
   ```bash
   black . && python -m py_compile src/web/routers/admin.py
   ```












