#!/usr/bin/env python3
"""
Simple script to format Python code using Black and check for syntax errors.
Run this before committing to catch indentation and formatting issues.
"""
import subprocess
import sys
from pathlib import Path

def format_code():
    """Format Python code and check for syntax errors"""
    project_root = Path(__file__).parent
    
    # Files to check/format
    python_files = list(project_root.rglob("*.py"))
    python_files = [f for f in python_files if "__pycache__" not in str(f) and "node_modules" not in str(f)]
    
    print(f"Found {len(python_files)} Python files to check...")
    
    # First, check for syntax errors
    print("\n🔍 Checking for syntax errors...")
    syntax_errors = []
    for py_file in python_files:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(py_file)],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            syntax_errors.append(py_file)
            print(f"  ❌ {py_file.relative_to(project_root)}: Syntax error!")
            print(f"     {result.stderr.strip()}")
    
    if syntax_errors:
        print(f"\n⚠️  Found syntax errors in {len(syntax_errors)} file(s).")
        print("   Please fix these errors before formatting.")
        return 1
    
    print("  ✅ No syntax errors found!")
    
    # Format with Black
    print("\n🎨 Formatting code with Black...")
    try:
        result = subprocess.run(
            ["black", "--check", "--diff", "."],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print("\n⚠️  Code needs formatting. Run this to auto-fix:")
            print("   black .")
            response = input("\nWould you like to format now? (y/n): ")
            if response.lower() == 'y':
                subprocess.run(["black", "."], cwd=project_root)
                print("✅ Code formatted!")
            else:
                return 1
        else:
            print("  ✅ Code is already formatted!")
    except FileNotFoundError:
        print("  ⚠️  Black not installed. Install with: pip install black")
        print("     Or use: python -m pip install black")
    
    return 0

if __name__ == "__main__":
    sys.exit(format_code())


