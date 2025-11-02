# 🚀 TOMORROW'S STARTUP GUIDE - Malaysia Swimming Analytics
**Last Updated**: Current Session End

## 📍 WHERE WE ARE

### ✅ Completed Today
1. **SEAG File Processing**: Successfully updated `convert_meets_to_sqlite_fixed.py` to:
   - Process all sheets in Excel files (not just first sheet)
   - Filter out unwanted sheets (containing "lap", "x", "top result")
   - Extract meet names and cities from Excel data columns (15 and 14)
   - Correctly map SEAG file columns using positional indices
   - Handle SEAG-specific structure (header row detection, column mapping)

2. **Database Schema Updates**: Added columns to database:
   - `athletes`: `birth_date`, `nation`, `club_name`, `club_code`
   - `meets`: `city`
   - `results`: `time_seconds_numeric`, `rudolph_points`, `course`, `result_meet_date`

3. **Meet Deduplication**: Implemented `meet_id_map` to combine Men's and Women's files for the same meet into a single database record.

### ⚠️ Issues Identified & Status

#### 1. SEAG File Birthdate Situation (CRITICAL - NEEDS CLARIFICATION)
- **Current State**: 
  - Column 5 (labeled "BIRTHDATE") exists in SEAG file but is **empty** (NaN in all rows)
  - Column 18 (labeled "AGE") contains numeric values (17, 14, etc.)
  - **Your Note**: You said "age in that workbook is birthyear age"
  
- **Questions to Resolve**:
  1. Is column 18 actually **birthyear** (like 2008, 2011) or **age** (like 17, 14)?
     - If it's birthyear: We can calculate age from birthyear + meet year
     - If it's age: We cannot calculate exact birthdate without more info
  2. Do you have a separate file with actual birthdates for SEAG athletes?
  3. If column 18 is birthyear, we should update the code to:
     - Store birthyear in database (or calculate approximate birthdate)
     - Calculate age from birthyear and meet year

- **Current Code Behavior**: 
  - `process_seag_file()` reads column 18 as `birthyear`
  - Calculates age as: `age = meet_year - birthyear`
  - Sets `birth_date_str = None` (since column 5 is empty)

#### 2. Duplicate Meets Issue (NEEDS FIX)
- **Problem**: `verify_database.py` shows duplicate meet names:
  - 'SUKMA 2024' vs 'Sukan Malaysia XXI Msn'
  - 'MIAG 2025' vs '60th Malaysia Age Group Championships'
  - 'Malaysia Open 2025' vs '67th Malaysian Open Championships'
  
- **Root Cause**: Different naming conventions between:
  - Filename-based extraction (`extract_meet_info()`)
  - Excel data-based extraction (column 15)
  
- **Solution Needed**: Update `meet_id_map` logic to handle name variations better, or normalize names before creating keys.

#### 3. Birthdate Parsing (38.3% have birthdates)
- **Current**: Only 38.3% of athletes have birthdates in standard meet files
- **Next Step**: Improve parsing logic for edge cases in `process_standard_meet_file()`

#### 4. SEAG Club Names (Empty)
- **Current**: Column 16 (CLUBNAME) is empty in SEAG files
- **Note**: You mentioned you have a separate file with this information

## 🎯 TOMORROW'S PRIORITY TASKS

### Task 1: Clarify SEAG Birthdate/Birthyear Situation ⚠️ FIRST
**Action Items**:
1. Verify what column 18 actually contains:
   - Open SEAG_2025_ALL.xlsx
   - Look at column 18 values
   - Determine if they're ages (17, 14) or birthyears (2008, 2011)
2. If column 18 is birthyear:
   - Confirm we should calculate approximate birthdate from birthyear
   - Update code to store birthyear and/or calculated birthdate
3. If you have a separate file with birthdates:
   - Provide the file path
   - We'll create a script to merge birthdates into the database

**Files to Check**:
- `data/meets/SEAG_2025_ALL.xlsx` - Check column 18 values
- `scripts/convert_meets_to_sqlite_fixed.py` - Lines 480-586 (process_seag_file function)

### Task 2: Fix Duplicate Meets ⚠️
**Action Items**:
1. Review `verify_database.py` output to identify all duplicate meet pairs
2. Update `extract_meet_info()` or `meet_id_map` logic to normalize meet names
3. Create a meet name normalization function (strip extra words, handle abbreviations)
4. Re-run conversion and verify no duplicates

**Files to Modify**:
- `scripts/convert_meets_to_sqlite_fixed.py` - `extract_meet_info()` and `main()` functions

### Task 3: Improve Birthdate Parsing
**Action Items**:
1. Run a query to find athletes missing birthdates
2. Sample some raw Excel rows to identify edge cases
3. Improve parsing logic for various date formats
4. Re-run conversion and verify improved birthdate coverage

### Task 4: Populate SEAG Club Names (When File Available)
**Action Items**:
1. Once you provide the club name file, create a script to:
   - Match SEAG athletes by name
   - Update `club_name` in database
   - Handle any name mismatches

## 📂 KEY FILES & LOCATIONS

### Main Conversion Script
- **File**: `scripts/convert_meets_to_sqlite_fixed.py`
- **Purpose**: Converts Excel meet files to SQLite database
- **Key Functions**:
  - `process_standard_meet_file()`: Processes MO/MIAG/SUKMA/State meets
  - `process_seag_file()`: Processes SEAG files
  - `extract_meet_info()`: Extracts meet info from filename
  - `main()`: Orchestrates the conversion process

### Database
- **File**: `malaysia_swimming.db` (in project root)
- **Tables**:
  - `athletes`: Name, gender, birth_date, nation, club_name, club_code, state_code
  - `meets`: Name, date, city, course
  - `results`: Links athletes to meets and events, includes times, points, place
  - `events`: Event definitions (distance, stroke, gender)

### Verification Script
- **File**: `verify_database.py`
- **Purpose**: Checks database contents and identifies issues
- **Usage**: `python verify_database.py`

### Meet Files Location
- **Path**: `data/meets/`
- **Files**: 9 Excel files including SEAG_2025_ALL.xlsx

## 🔍 QUICK START COMMANDS

### Check Current Database Status
```bash
cd "C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics"
python verify_database.py
```

### Inspect SEAG File Structure
```bash
python check_seag_structure.py
```

### Re-run Conversion (After Fixes)
```bash
python scripts/convert_meets_to_sqlite_fixed.py
```

### Check Specific Data
```bash
python -c "import sqlite3; conn = sqlite3.connect('malaysia_swimming.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM athletes WHERE birth_date IS NOT NULL'); print(f'Athletes with birthdates: {cursor.fetchone()[0]}'); cursor.execute('SELECT COUNT(*) FROM athletes'); print(f'Total athletes: {cursor.fetchone()[0]}'); conn.close()"
```

## 📋 TODO LIST STATUS

1. ⚠️ **seag_birthdates**: Verify SEAG file birthdate situation - Column 5 empty, Column 18 labeled "AGE" but you said it's birthyear. Need clarification on what column 18 actually contains and if we have a separate birthdate file.

2. ⚠️ **investigate_duplicate_meets**: Fix duplicate meets - 'SUKMA 2024' vs 'Sukan Malaysia XXI Msn', etc. Root cause: different naming between filename and Excel data extraction.

3. ⏳ **improve_birthdate_parsing**: Only 38.3% of athletes have birthdates. Need to improve parsing for edge cases.

4. ⏳ **seag_club_names**: Populate from separate file when available.

## 💡 NOTES FOR NEW CHAT SESSION

When starting a new chat, provide:
1. **Clarification on SEAG Column 18**: 
   - "In SEAG_2025_ALL.xlsx, column 18 is labeled 'AGE' but contains values like 17, 14. You mentioned it's 'birthyear age' - can you confirm if these are birthyears (2008, 2011) or actual ages (17, 14)?"
   
2. **Birthdate File**: 
   - "Do you have a separate file with birthdates for SEAG athletes? If so, what's the file path and format?"
   
3. **Current Status**: 
   - "We completed SEAG file processing today. The database has all columns added. Issues: (1) SEAG birthdates unclear, (2) duplicate meets, (3) only 38.3% birthdate coverage. See TOMORROW_START_GUIDE.md for details."

4. **Key Files**:
   - Conversion script: `scripts/convert_meets_to_sqlite_fixed.py`
   - Database: `malaysia_swimming.db`
   - Verification: `verify_database.py`
   - SEAG structure check: `check_seag_structure.py`

---

**Remember**: Always verify the SEAG column 18 situation first - this affects how we calculate ages and store birthdate data!




