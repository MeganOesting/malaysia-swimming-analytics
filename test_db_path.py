from pathlib import Path

# Simulate the path calculation from admin.py
admin_file = Path("src/web/routers/admin.py")
if admin_file.exists():
    project_root = admin_file.parent.parent.parent.parent
    print(f"Project root: {project_root}")
    print(f"Absolute path: {project_root.absolute()}")
    
    root_db = project_root / "malaysia_swimming.db"
    db_folder_db = project_root / "database" / "malaysia_swimming.db"
    
    print(f"\nRoot DB: {root_db.absolute()}")
    print(f"  Exists: {root_db.exists()}")
    
    print(f"\nDatabase folder DB: {db_folder_db.absolute()}")
    print(f"  Exists: {db_folder_db.exists()}")
    
    # Check actual database location
    actual_db = Path("malaysia_swimming.db")
    print(f"\nActual DB in current dir: {actual_db.absolute()}")
    print(f"  Exists: {actual_db.exists()}")


