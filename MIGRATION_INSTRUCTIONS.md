# Folder Reorganization (Completed October 2025)

> Status: All migration steps executed and verified. This document is preserved for reference only; you do **not** need to rerun the scripts unless you intentionally reset the repository structure.

## ✅ COMPLETED: Script Updates
- Fixed `build_delta_html.py` - Now handles relative paths dynamically
- Fixed `db_schema.py` - Database path adapts to new structure
- Fixed `run_mot_delta_analysis.py` - Period Data and Delta Data paths updated
- Fixed `build_delta_index.py` - Delta Data path updated
- Fixed `compare_deltas_canada.py` - Excel workbook and reports paths updated
- Fixed `load_canada_tracks.py` - Excel workbook path updated

## 📋 NEXT STEPS: Run Migration

### Step 1: Run the Migration Batch Script

**In your command prompt, run:**
```batch
cd "C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics"
MIGRATE_FOLDERS.bat
```

This will:
- Copy reference data to `reference_data/imports/`
- Copy meet data to `meets/active/2024-25/`
- Copy Statistical Analysis project to `statistical_analysis/`
- Copy Times Database project to `times_database/`
- Move temporary scripts to `temp_scripts/`

### Step 2: After Migration, Verify Structure

Check these folders exist and have files:
- ✅ `reference_data/imports/` - Should have 2 Excel files
- ✅ `meets/active/2024-25/` - Should have 9 Excel files
- ✅ `statistical_analysis/data/Period Data/` - Should have 4 period folders
- ✅ `statistical_analysis/data/Delta Data/` - Should have 84 folders
- ✅ `statistical_analysis/reports/` - Should have 2 files
- ✅ `times_database/src/` - Should have web application files
- ✅ `times_database/scripts/` - Should have conversion scripts

### Step 3: Extract Statistical Database Tables

The statistical analysis database needs to be separated from the main database.

**Run this Python command:**
```python
# Extract statistical tables to new database
import sqlite3, shutil, os

# Source database
src_db = "database/malaysia_swimming.db"
# Target database
dst_db = "statistical_analysis/database/statistical.db"

# Ensure directory exists
os.makedirs(os.path.dirname(dst_db), exist_ok=True)

# Copy database
shutil.copy2(src_db, dst_db)

# Connect and verify tables exist
conn = sqlite3.connect(dst_db)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cur.fetchall()]
print("Tables in statistical database:", tables)
conn.close()

print("Database copied to:", dst_db)
```

### Step 4: Update Script Paths for Times Database

After migration, scripts in `times_database/scripts/` need path updates:

**Scripts that reference `data/meets/`:**
- `convert_meets_to_sqlite_fixed.py`
- `convert_meets_to_sql.py`
- `convert_excel_to_sql.py`
- Other conversion scripts

**Update pattern:** `data/meets/` → `../meets/active/2024-25/`

**Scripts that reference `data/reference/`:**
- Scripts that load club mapping
- Scripts that load MAP/MOT/AQUA tables

**Update pattern:** `data/reference/` → `../reference_data/imports/`

*(Historical log: statistical tables were moved to `statistical_analysis/database/statistical.db` on 2025‑10‑xx; Times Database now contains only web-app tables as verified by `python scripts\cleanup_statistical_tables.py` and `python scripts\test_sqlite_db.py`.)*

### Step 5: Update Docker Configuration

Move `docker-compose.yml` to `times_database/` and update volume mounts:

```yaml
volumes:
  - ./src:/app/src
  - ../meets:/app/meets
  - ../reference_data:/app/reference_data
  - ./scripts:/app/scripts
  - ./database:/app/database
```

### Step 6: Test Everything

1. **Test Statistical Analysis:**
   ```bash
   cd statistical_analysis
   python scripts/load_canada_tracks.py
   python scripts/build_delta_index.py
   ```

2. **Test Times Database:**
   ```bash
   cd times_database
   # Test database connection
   python scripts/test_database_connection.py
   ```

3. **Regenerate HTML Index:**
   ```bash
   cd statistical_analysis
   python scripts/build_delta_html.py
   ```

### Step 7: Clean Up (After Verification)

Only after everything works:
- Delete old `Statistical Analysis/` folder
- Delete old `data/` folder (or archive it)
- Delete old `src/` folder (if moved successfully)

## 🚨 IMPORTANT NOTES

1. **Keep original folders** until everything is verified
2. **Database files** are copied, not moved (for safety)
3. **All scripts** have been updated to handle both old and new structures
4. **Test thoroughly** before deleting old folders




