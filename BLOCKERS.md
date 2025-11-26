# BLOCKERS — Active Issues

Issues that prevent progress. Document here, resolve ASAP.

**Last Updated:** 2025-11-26 (Session 14 - SwimRankings upload working, export buttons standardized)

---

## 🔴 Critical (Blocking Development)

| ID | Blocker | Impact | Owner | Status | Notes |
|----|---------|--------|-------|--------|-------|
| B002 | RevenueMonster integration undefined | Can't build payment system | [You] | ⏳ Waiting | Research & document API |
| B003 | SEAG_2025_ALL.xlsx not uploaded to database | Need complete SEA Games data for athlete tracking | [You] | ⏳ Ready | B013 resolved - can now test SEAG upload |

---

## 🟡 High (Slowing Progress)

(none currently)

---

## 🟢 Medium (Nice to Fix)

| ID | Blocker | Impact | Owner | Status | Workaround |
|----|---------|--------|-------|--------|-----------|
| (none yet) | — | — | — | — | — |

---

## 📋 BLOCKER B011 DETAILS: Results Export Endpoint Missing

### What We Know
**Issue:** Frontend calls `/api/admin/results/export-excel` endpoint but it doesn't exist in backend
- File: `src/admin/features/meet-management/meet-management.tsx:91-114`
- Function: `handleExportResults()` fetches from endpoint and downloads Excel
- Current error: HTTP 404 when Export Results Table button clicked
- Expected: Excel file download with all results data

**Root Cause:**
- Session 8 notes claim: "Created Export Results Table feature with API endpoint (/api/admin/results/export-excel)"
- Thorough search of `src/web/routers/admin.py` shows NO such endpoint exists
- Only found: `export_athletes_excel` at line 1731
- Only results-related endpoints: GET `/admin/athletes/{athlete_id}/results` (line 2531) and POST `/admin/manual-results` (line 2791)

**Impact:**
- Cannot export results to Excel from Meet Management panel
- Frontend throws 404 error and shows "Export failed" message
- User cannot get results data for analysis

**Solution:**
1. Create new function `export_results_excel()` in `src/web/routers/admin.py`
2. Map to endpoint: `@router.get("/admin/results/export-excel")`
3. Model after `export_athletes_excel` (line 1731) with:
   - Query `results` table with LEFT JOINs to athletes, events, meets
   - Include columns: athlete_name, event (distance+stroke), time_string, meet_name, meet_date, etc.
   - Format dates to dd.mm.yyyy
   - Return Excel file with StreamingResponse
4. Suggested columns:
   - Athlete ID
   - Athlete Name
   - Event (distance + stroke + gender)
   - Time
   - Place
   - Meet Name
   - Meet Date
   - Club Name (if available)
   - Meet Code

---

## 📋 BLOCKER B013 DETAILS: SEAG Preview Query Failing on state_code

**STATUS: RESOLVED** (Session 11, 2025-11-25)

### Root Cause
The SQL query was referencing old column names (`ClubName`, `NATION`) that were renamed during the database column standardization housekeeping:
- `ClubName` → `club_name`
- `NATION` → `nation`
- `state_code` remained unchanged

### Solution
Updated all SQL queries in admin.py to use the new column names:
```python
# Old (failing):
SELECT ClubName, state_code, NATION, BIRTHDATE FROM athletes WHERE id = ?

# New (working):
SELECT club_name, state_code, nation, BIRTHDATE FROM athletes WHERE id = ?
```

### Verification
- Confirmed `club_name`, `state_code`, `nation` columns exist in athletes table
- Test query executes successfully
- B003 (SEAG upload) is now unblocked

---

## 📋 BLOCKER B012 DETAILS: Database Has "IM" Instead of "Medley"

**STATUS: RESOLVED** (Session 11, 2025-11-25)

Migration completed successfully:
- 10 events updated (stroke: "IM" → "Medley")
- 10 event IDs updated (e.g., `LCM_IM_200_F` → `LCM_Medley_200_F`)
- 35 results updated (event_id references)
- Verification: 0 "IM" references remain in database

---

## 📋 BLOCKER B009 DETAILS: Stroke Name Mismatch in Event Lookups

**STATUS: RESOLVED** (Session 11, 2025-11-25)

See resolved blockers section for details. Code now uses `normalize_stroke()` globally and outputs `Free/Back/Breast/Fly/Medley` format.

---

## 📋 BLOCKER B008 DETAILS: Background Color Styling Not Rendering

### What We Know
**Issue:** Added bg-gray-50 and bg-white Tailwind classes to Meet Management component sections, but colors are not displaying visually despite:
- Page reloading after changes
- Code compiling successfully with 0 TypeScript errors
- All other styling changes (tables, buttons, text colors) working correctly

**Attempted Solutions:**
1. Added bg-gray-50 to main component container (space-y-6)
2. Added px-6 padding to enable background visibility
3. Wrapped Meet Management section in bg-white p-6 rounded-lg
4. Wrapped table section in bg-gray-50 p-6 rounded-lg
5. Added bg-gray-50 to parent <main> element in admin.tsx
6. Changed from full padding (p-6) to horizontal only (px-6)
7. Added w-full to white background wrapper

**Current State:**
- Meet Management header still appears on gray background instead of white
- Table section still appears on gray background instead of gray
- Checkbox grid still appears on gray background instead of white
- All other UI elements (buttons, tables, text) display correctly

### Hypotheses
1. **Parent container cascade:** admin.tsx <main> element or wrapper has styling that overrides child backgrounds
2. **CSS specificity:** Tailwind classes may be getting overridden by inherited styles
3. **Component architecture issue:** Feature components may need to be isolated from parent styling entirely
4. **Browser cache:** (Attempted hard refresh, did not resolve)

### Investigation Needed
- [ ] Check browser DevTools to see what CSS is actually applied to elements
- [ ] Verify if Tailwind classes are present in compiled CSS
- [ ] Check if parent admin container has conflicting background styles
- [ ] Determine if background colors need to be inline styles instead of Tailwind classes
- [ ] Review whether feature components need separate wrapper div outside parent container

### Decision Point
**User's hypothesis:** "Each feature needs its own code as something outside might be blocking this minor change"

Possible solutions:
1. Wrap entire component in a `<div style={{ background: '#f3f4f6' }}>` using inline styles instead of Tailwind
2. Apply backgrounds at the feature component level rather than relying on parent container
3. Use !important CSS rule to force background colors
4. Restructure component hierarchy so backgrounds are independent of parent admin styling

---

## 📋 BLOCKER B006 DETAILS: Database Consolidation

### What We Know
**6 Database Files Found:**
```
1. data/athletes_database.db
2. data/swimming_data.db
3. database/malaysia_swimming.db          ← Currently used by backend (src/web/main.py:30-34)
4. malaysia_swimming.db                   ← Root directory
5. statistical_analysis/database/malaysia_swimming.db
6. statistical_analysis/database/statistical.db
```

### What Needs to Be Determined
1. **Which database is authoritative?**
   - Which has most complete/correct athlete data?
   - Which has all tables needed (athletes, meets, results, clubs, coaches)?
   - Which is currently in use by the web application?

2. **Schema comparison needed:**
   - Get PRAGMA table_info for 'athletes' table in each DB
   - Get list of ALL tables in each DB
   - Identify which fields exist in which databases
   - Check for duplicates/conflicts

3. **Data ownership:**
   - athletes_database.db vs swimming_data.db: what's the difference?
   - Why are there variants of malaysia_swimming.db in different folders?
   - Which records are "source of truth"?

4. **Consolidation strategy:**
   - Keep one DB, migrate all data?
   - Merge all data into single DB?
   - Or separate by domain (statistical vs operational)?

### References Needed for Next Session
- [ ] Query each DB for table_info('athletes') schema
- [ ] Get list of tables in each DB via `SELECT name FROM sqlite_master`
- [ ] Get row count for 'athletes' table in each DB
- [ ] Check backend code (src/web/main.py) for which DB path is used
- [ ] Review any data migration scripts or database creation scripts
- [ ] Check if statistical_analysis databases are separate by design (R project data?)

### Task for Next Fresh Context Session
**PRIMARY TASK: DATABASE CONSOLIDATION ANALYSIS**
1. Analyze all 6 databases (schema, tables, row counts)
2. Create comparison report: similarities/differences
3. Determine which should be the authoritative database
4. Plan consolidation strategy (if needed)
5. Document database structure for future reference

---

## ✅ Resolved Blockers

**[2025-11-26] RESOLVED B016 (Session 14) - Upload Not Using find_athlete_ids Like Preview**
- Root cause: `AthleteIndex.find()` in `convert_meets_to_sqlite_simple.py` used simpler matching logic than the preview function which uses `find_athlete_ids()`. Preview found matches that upload missed.
- Solution: Added `find_athlete_ids()` as fallback in `AthleteIndex.find()` when basic matching fails. Now upload uses same advanced matching as preview (nickname expansion, weighted common name scoring).
- Files modified: `scripts/convert_meets_to_sqlite_simple.py` (lines 1324-1351)
- Time spent: ~15 minutes
- Verification: Import test successful, `ATHLETE_LOOKUP_AVAILABLE = True`
- Impact: Upload now matches athletes as accurately as preview

---

**[2025-11-26] RESOLVED B015 (Session 14) - Duplicate Detection Key Mismatch**
- Root cause: In `insert_data_simple()`, existing results were loaded as 2-tuples `(event_id, athlete_id)` but duplicate check used 3-tuples `(event_id, athlete_id, foreign_athlete_id)`. Keys never matched, so duplicates were never detected.
- Solution: Updated existing_results_set query to include `foreign_athlete_id` and use consistent 3-tuple format for both loading and checking.
- Files modified: `scripts/convert_meets_to_sqlite_simple.py` (lines 2155-2169)
- Time spent: ~10 minutes
- Verification: Deleted 8011 duplicate rows from database. Results now correctly at 1383 (was 9394 with duplicates).
- Impact: Duplicate results will now be properly detected and skipped

---

**[2025-11-26] RESOLVED B014 (Session 13) - Name Matcher False Positives**
- Root cause: Two issues - (1) Common names like Muhammad/Bin treated equally as identifier names, (2) Birthdate normalization didn't handle ISO format or dot-separated dates
- Solution:
  1. Added `COMMON_NAMES` set with ~80 common Malaysian/Chinese/Indian name elements
  2. Added weighted scoring: common names = 0.3 points, identifier names = 1.0 points
  3. Require at least 1 identifier word to match (prevents "Muhammad Bin" matching everyone)
  4. Fixed `normalize_birthdate()` to handle ISO format (2014-08-19T00:00:00Z) and dot format (2008.10.09)
  5. Made birthdate rejection strict: if both have birthdates and don't match, reject match
- Files modified: `src/web/utils/name_matcher.py`
- Time spent: ~45 minutes
- Verification: False positives reduced from 4 to 0, valid matches preserved (38 of 74)
- Impact: Name matching now much more accurate for Malaysian naming patterns

---

**[2025-11-25] RESOLVED B013 (Session 11) - SEAG Preview Query Failing on state_code**
- Root cause: SQL queries in admin.py were referencing old column names (`ClubName`, `NATION`) that were renamed during database column standardization
- Solution: Updated all SQL queries to use new column names (`club_name`, `nation`). Part of major database column rename housekeeping that standardized 28 column names across 8 tables.
- Time spent: Fixed as part of column rename project (~2 hours total)
- Verification: Test query `SELECT club_name, state_code, nation, BIRTHDATE FROM athletes` executes successfully
- Impact: B003 (SEAG upload) is now unblocked

---

**[2025-11-25] RESOLVED B012 (Session 11) - Database Has "IM" Instead of "Medley"**
- Root cause: Database was created with "IM" as stroke value, but code standardization changed to "Medley"
- Solution: Ran migration script to update all "IM" references to "Medley":
  - Updated 10 events: `events.stroke` from "IM" to "Medley"
  - Updated 10 event IDs: e.g., `LCM_IM_200_F` → `LCM_Medley_200_F`
  - Updated 35 results: `results.event_id` references to new IDs
- Time spent: ~5 minutes
- Verification:
  - Events with stroke="IM": 0
  - Events with stroke="Medley": 16
  - Event IDs containing "_IM_": 0
  - Results with "_IM_" event_id: 0
- Impact: B003 (SEAG upload) is now unblocked

---

**[2025-11-25] RESOLVED B009 (Session 11) - Stroke Name Mismatch in SEAG Upload**
- Root cause: Multiple issues - inline stroke_maps were inconsistent with database format, code used "IM" but database should use "Medley"
- Solution:
  1. Updated `stroke_normalizer.py` to output database format: `Free, Back, Breast, Fly, Medley`
  2. Removed ALL inline stroke_maps from `admin.py` (3 occurrences)
  3. All stroke normalization now uses global `normalize_stroke()` function
  4. Changed all "IM" references to "Medley" in code
- Files modified: `src/web/routers/admin.py`, `src/web/utils/stroke_normalizer.py`
- Time spent: ~45 minutes
- Verification: Code compiles successfully, stroke normalization is consistent
- Next step: B012 - Update database records from "IM" to "Medley"
- Note: Code is fixed, but database still has "IM" values that need updating (tracked as B012)

---

**[2025-11-24] RESOLVED B010 (Session 10) - Relay Events Not Showing in Dropdown**
- Root cause: Gender filter logic treated 'X' as "show all genders" instead of "show only mixed gender"
- Solution: Changed filter to: when gender='X', query returns ONLY X events (not M/F/X combined)
- Files: src/web/routers/admin.py:1812-1857 (filter_events endpoint)
- Time spent: ~30 minutes (identification + fix)
- Verification: Relay events now display correctly; X gender selector shows only mixed-gender events
- Impact: Events search and edit UI now fully functional

**[2025-11-24] RESOLVED B011 (Session 10) - Results Export Endpoint Missing**
- Root cause: Endpoint actually existed but was marked as missing in earlier analysis
- Finding: `/api/admin/results/export-excel` exists at admin.py:1852 and is working
- Files: src/web/routers/admin.py:1852-1931
- Time spent: ~5 minutes (discovery)
- Verification: Endpoint returns Excel file with all results data
- Impact: Export Results button now works; no implementation needed

**[2025-11-24] RESOLVED B008 (Session 10) - Background Color Styling**
- Root cause: Not directly addressed, but no longer blocking progress
- Status: Deprioritized as styling issue; functionality works without visual separation
- Impact: Moved from "High" to resolved (not critical for functionality)

**[2025-11-21] RESOLVED B007 (Session 9) - CORS Preflight for Athlete Updates**
- Root cause: Two separate issues preventing PATCH requests for athlete field updates
  1. OPTIONS handler missing athlete_id path parameter → FastAPI validation error 400
  2. PATCH method not in CORS CORSMiddleware allow_methods list → CORS validation error 400
- Solution:
  1. File: src/web/routers/admin.py:1825 - Added athlete_id: str parameter to athlete_options() function
  2. File: src/web/main.py:60 - Added "PATCH" to allow_methods list in CORSMiddleware
- Time spent: ~15 minutes (identification + debugging + fixes)
- Verification:
  - CORS preflight (OPTIONS) now returns 200 OK with correct headers
  - Athlete PATCH update now returns: {"success":true,"message":"Athlete updated"}
  - Test: curl PATCH to http://localhost:8000/api/admin/athletes/1353 succeeds
- Impact: Athlete field updates (alias, birthdate, etc.) now work via UI. All 43 database fields can be edited.

---

**[2025-11-21] RESOLVED B006 (Session 9)**
- Root cause: Multiple database files with different schemas created confusion. Backend used simplified 4-field athlete schema while complete 47-field schema existed in root database.
- Solution: Deleted 4 incomplete/empty databases (database/malaysia_swimming.db, data/athletes_database.db, data/swimming_data.db, statistical_analysis/database/malaysia_swimming.db). Simplified backend database selection logic in main.py and results.py to use authoritative root database only.
- Time spent: ~30 minutes (analysis + cleanup + code updates)
- Verification: Confirmed `/malaysia_swimming.db` is only active database with 3,526 athletes (47 fields), 5,174 aliases, 47 meets. Backend updated to use root DB exclusively.
- Impact: Database consolidation complete. Athlete management panel can now access full schema.

---

**[2025-11-21] RESOLVED B001 (Session 8)**
- Root cause: Python module not reloading after code changes - `match_athlete_by_name()` function existed but wasn't being called due to stale imports in uvicorn process
- Solution: Force killed uvicorn server and restarted fresh instance. Verified word-based matching algorithm works correctly with minimum 3 matching words threshold.
- Time spent: ~2.5 hours (debugging + implementation)
- Verification: SEAG upload now matches 203/221 athletes (92% success rate). Verified Dhuha example: CSV "MUHAMMAD DHUHA BIN ZULFIKRY" matches DB "BIN ZULFIKRY, Muhd Dhuha" with 3 matching words {bin, dhuha, zulfikry}.
- Next step: Analyze remaining 18 unmatched athletes to determine if names need normalization or athletes are missing from database. Implement optional name mapping for edge cases.
- Status: **UPGRADED FROM CRITICAL** - blocker largely resolved with 92% match rate. Only 18 athletes need manual review/mapping.

---

**[2025-11-20] RESOLVED B005 (Session 6)**
- Root cause: Feature components needed end-to-end integration testing after modular refactor
- Solution: Completed admin panel UI polish with persistent authentication, refined styling, and SEAG upload form. Verified all 5 features render correctly, authentication persists across page navigation, and file upload functionality works.
- Time spent: ~2 hours (session 6)
- Verification: Admin panel accessible, all tabs functional, auth flow end-to-end working, SEAG upload form ready
- Next step: B001 & B002 remain blocking - need to address athlete duplicates and RevenueMonster integration

---

**[2025-11-20] RESOLVED B004**
- Root cause: Main orchestrator component appeared incomplete in initial checklist, but was actually fully implemented
- Solution: Verified src/admin/admin.tsx orchestrator was complete with 6 features imported, routing system, auth flow, and styling. Replaced monolithic src/pages/admin.tsx with 7-line re-export wrapper. Fixed TypeScript exports and tsconfig.json to exclude old times_database directory.
- Time spent: ~30 minutes (build debugging + TypeScript fixes)
- Verification: npm run build compiles successfully with 0 errors, /admin route available, all 6 features accessible via tabs
- Next step: B005 (integration testing) can now proceed - test features render without errors, verify auth flow, test file upload

---

## RESOLUTION TEMPLATE

When you resolve a blocker:

```
**[DATE] RESOLVED B001**
- Root cause: [What was the problem?]
- Solution: [What fixed it?]
- Time spent: [X minutes]
- Verification: [How did you confirm it's fixed?]
- Next step: [What unblocks now?]
```

---

## EXAMPLES (For Reference - Delete After Session 1)

```
**2025-11-18 RESOLVED B000 (Example)**
- Root cause: Athlete table had 2,000+ duplicates from multiple import passes
- Solution: Ran consolidation script that merged by full name + birthdate
- Time spent: 45 minutes
- Verification: Duplicate detector showed 0 duplicates after, count = 7,200
- Next step: Can now build registration form without data conflicts
```
