#!/usr/bin/env python3
"""
Malaysia Swimming Analytics - Session Checkup Script
Automated health checks for new development sessions
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent


def check_python() -> Tuple[bool, str]:
    """Check Python installation and version"""
    try:
        result = subprocess.run(
            ["python", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            return True, version
        return False, "Python not found"
    except Exception as e:
        return False, f"Error checking Python: {str(e)}"


def check_node() -> Tuple[bool, str]:
    """Check Node.js installation and version"""
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            return True, version
        return False, "Node.js not found"
    except Exception as e:
        return False, f"Error checking Node.js: {str(e)}"


def check_python_packages() -> Tuple[bool, List[str], List[str]]:
    """Check if required Python packages are installed"""
    required = ["fastapi", "uvicorn", "pandas", "openpyxl", "sqlite3"]
    installed = []
    missing = []
    
    for package in required:
        if package == "sqlite3":
            # sqlite3 is built-in
            try:
                import sqlite3
                installed.append(package)
            except ImportError:
                missing.append(package)
        else:
            try:
                __import__(package)
                installed.append(package)
            except ImportError:
                missing.append(package)
    
    return len(missing) == 0, installed, missing


def check_node_modules() -> Tuple[bool, bool]:
    """Check if node_modules exists"""
    node_modules = PROJECT_ROOT / "node_modules"
    next_js = node_modules / "next"
    return node_modules.exists(), next_js.exists()


def check_database() -> Tuple[bool, Dict[str, int]]:
    """Check database status"""
    db_path = PROJECT_ROOT / "malaysia_swimming.db"
    if not db_path.exists():
        # Try database folder
        db_path = PROJECT_ROOT / "database" / "malaysia_swimming.db"
    
    if not db_path.exists():
        return False, {}
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get table counts
        stats = {}
        tables = ["athletes", "meets", "events", "results"]
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                stats[table] = count
            except sqlite3.OperationalError:
                stats[table] = -1  # Table doesn't exist
        
        conn.close()
        return True, stats
    except Exception as e:
        return False, {"error": str(e)}


def check_ports() -> Tuple[bool, bool]:
    """Check if backend and frontend are running"""
    backend_running = False
    frontend_running = False
    
    try:
        # Check port 8000 (backend)
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if ":8000" in result.stdout:
            backend_running = True
        
        # Check port 3000 or 3001 (frontend)
        if ":3000" in result.stdout or ":3001" in result.stdout:
            frontend_running = True
    except Exception:
        # If netstat fails, assume unknown
        pass
    
    return backend_running, frontend_running


def check_project_structure() -> Dict[str, bool]:
    """Check if required project structure exists"""
    required = {
        "src": PROJECT_ROOT / "src",
        "src/web": PROJECT_ROOT / "src" / "web",
        "src/pages": PROJECT_ROOT / "src" / "pages",
        "scripts": PROJECT_ROOT / "scripts",
        "requirements.txt": PROJECT_ROOT / "requirements.txt",
        "package.json": PROJECT_ROOT / "package.json",
    }
    
    structure = {}
    for name, path in required.items():
        structure[name] = path.exists()
    
    return structure


def main():
    """Run all health checks and print summary"""
    print("=" * 70)
    print("Malaysia Swimming Analytics - Session Checkup")
    print("=" * 70)
    print()
    
    # Python check
    print("[1/7] Checking Python...")
    python_ok, python_version = check_python()
    print(f"   {'✓' if python_ok else '✗'} {python_version}")
    print()
    
    # Node.js check
    print("[2/7] Checking Node.js...")
    node_ok, node_version = check_node()
    print(f"   {'✓' if node_ok else '✗'} {node_version}")
    print()
    
    # Python packages check
    print("[3/7] Checking Python packages...")
    packages_ok, installed, missing = check_python_packages()
    if packages_ok:
        print(f"   ✓ All packages installed: {', '.join(installed)}")
    else:
        print(f"   ✗ Missing packages: {', '.join(missing)}")
        print(f"   → Run: pip install -r requirements.txt")
    print()
    
    # Node modules check
    print("[4/7] Checking Node.js modules...")
    node_modules_exists, next_exists = check_node_modules()
    if next_exists:
        print("   ✓ Node modules installed")
    elif node_modules_exists:
        print("   ⚠ Node modules folder exists but Next.js missing")
        print("   → Run: npm install")
    else:
        print("   ✗ Node modules not found")
        print("   → Run: npm install")
    print()
    
    # Database check
    print("[5/7] Checking database...")
    db_exists, db_stats = check_database()
    if db_exists:
        if db_stats:
            print("   ✓ Database found")
            for table, count in db_stats.items():
                if count >= 0:
                    print(f"      {table}: {count:,} records")
                else:
                    print(f"      {table}: table missing")
        else:
            print("   ✓ Database found (empty)")
    else:
        print("   ⚠ Database not found (will be created on first upload)")
    print()
    
    # Ports check
    print("[6/7] Checking server status...")
    backend_running, frontend_running = check_ports()
    print(f"   Backend (8000): {'✓ Running' if backend_running else '✗ Not running'}")
    print(f"   Frontend (3000/3001): {'✓ Running' if frontend_running else '✗ Not running'}")
    if not backend_running and not frontend_running:
        print("   → Run: start-dev.bat or start servers manually")
    print()
    
    # Project structure check
    print("[7/7] Checking project structure...")
    structure = check_project_structure()
    all_ok = all(structure.values())
    if all_ok:
        print("   ✓ All required folders and files present")
    else:
        print("   ⚠ Missing items:")
        for name, exists in structure.items():
            if not exists:
                print(f"      ✗ {name}")
    print()
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    issues = []
    if not python_ok:
        issues.append("Python not installed")
    if not node_ok:
        issues.append("Node.js not installed")
    if not packages_ok:
        issues.append("Python packages missing")
    if not next_exists:
        issues.append("Node modules missing")
    if not backend_running and not frontend_running:
        issues.append("Servers not running")
    
    if issues:
        print("⚠️  Issues found:")
        for issue in issues:
            print(f"   - {issue}")
        print()
        print("💡 Quick fixes:")
        if not packages_ok:
            print("   pip install -r requirements.txt")
        if not next_exists:
            print("   npm install")
        if not backend_running and not frontend_running:
            print("   start-dev.bat  (or start servers manually)")
    else:
        print("✅ All checks passed! Ready to develop.")
        if not backend_running or not frontend_running:
            print()
            print("💡 Start servers with: start-dev.bat")
    print()


if __name__ == "__main__":
    main()







