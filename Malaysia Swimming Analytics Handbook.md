# Malaysia Swimming Analytics — Developer Handbook (November 2025)

This handbook gives a new developer everything needed to take over the project in a fresh chat, tool, or IDE. Pair it with `SESSION_START.md` for daily operations.

---

## 1. System Overview
- **Frontend:** Next.js + React + TypeScript (`src/pages`, `src/components`).
- **Backend:** FastAPI (`src/web`), served locally via `uvicorn` against SQLite.
- **Database:** `malaysia_swimming.db` in the repository root. SQLite is authoritative for local work; Docker/PostgreSQL is optional parity only.
- **Authentication:** Admin panel protected by a simple password (`MAS2025`). OAuth/JWT not yet implemented.
- **Legacy system:** Flask + Excel remains for historical reference. Do not modify it unless instructed.

---

## 2. Environment & Daily Startup
1. Open three terminals:
   - `Backend`: `uvicorn src.web.main:app --reload --host 127.0.0.1 --port 8000`
   - `Frontend`: `npm run dev`
   - `Manual`: idle shell for Python scripts and inspections
2. Access points:
   - Frontend/UI: <http://localhost:3000>
   - Admin panel: <http://localhost:3000/admin>
   - API base: <http://localhost:8000>
   - API docs: <http://localhost:8000/api/docs>
3. Dependency refresh (when packages change):
   - Python: `"…python.exe" -m pip install -r requirements.txt`
   - Node: `npm install`
4. Quick status: `"…python.exe" scripts/session_checkup.py`

All commands must follow the windows-specific pattern from `SESSION_START.md`.

---

## 3. Data Sources & Consolidation Pipeline
We maintain a single authoritative workbook that merges registration data and result exports.

| Step | Script | Output |
| --- | --- | --- |
| 1 | `temp_scripts/rebuild_consolidated_athletes.py` | `data/manual_matching/consolidated_athlete_ID_rebuilt.xlsx` |
| 2 | (TBD) Load merged workbook into `athletes` table (current scripts `load_athletes_pass1/2/3.py` will be replaced). | `athletes` table |
| 3 | `temp_scripts/setup_athlete_aliases.py` | Initializes `athlete_aliases` with canonical names |
| 4 | `temp_scripts/check_missing_aliases.py` | Reports unmatched names after a meet upload |

**Source workbooks:**
- `data/manual_matching/consolidated_registration_subset.xlsx`
- `data/manual_matching/consolidated_results_athlete_birthdat_fullname.xlsx`

Merged workbook columns include:
- `FULLNAME`, `FIRSTNAME`, `LASTNAME`, `MIDDLENAME`, `SUFFIX`
- `BIRTHDATE` (normalized), `Birthday_raw`
- `IC_NORMALIZED`, `IC_DIGIT_COUNT`
- `SOURCE_FILE`, `SOURCE_SHEET`, `BIRTHDATE_MATCH`

When loading the database, new developers should re-run the merge script, inspect the workbook, and then load `athletes` + aliases before processing meets.

---

## 4. Database Schema (SQLite)
- `athletes(id, FULLNAME, BIRTHDATE, …, IC, NATION)` — authoritative list.
- `athlete_aliases(id, athlete_id, alias_fullname, is_canonical, notes)` — every name variant encountered in meet files. `alias_fullname` is unique case-insensitively.
- `events` — canonical event catalog (LCM + SCM, including relay variants).
- `meets` — meet metadata; `meet_type` doubles as alias code.
- `results` — meet entries. `time_seconds_numeric` sourced from `SWIMTIME_N`, `time_string` from `SWIMTIME`.
- `records`, `record_history` — national, age-group, single-age, and SEA 61 relay records.
- `states`, `clubs` — reference data loaded via `temp_scripts/load_clubs_by_state.py`.

Constraints worth noting:
- `records` unique on `(event_id, category_type, category_value)`.
- `athlete_aliases` unique on lowercased alias.
- `results` expects `athlete_id`, `event_id`, `meet_id` to exist before insert.

---

## 5. Meet Conversion Workflow
Script: `scripts/convert_meets_to_sqlite_simple.py`

Key behaviour:
- Resolves athletes through `athlete_aliases` → `athletes`. Missing entries surface as validation errors.
- Requires `events` to be pre-seeded (`temp_scripts/setup_events.py`).
- Reads meet workbooks (standard MAS format + relay sheets). Sheets starting with `4 x` are treated as relays.
- Validates:
  - Missing athlete mapping
  - Nation mismatches between athlete master and workbook
  - Club lookups against `clubs`
  - Gender mismatches
- Uses `SWIMTIME_N` as numeric time and `SWIMTIME` as formatted string.
- Collects inserted vs skipped counts for detailed frontend reporting.

Support scripts:
- `temp_scripts/check_missing_aliases.py` — run after a failed upload to list missing aliases.
- `temp_scripts/missing_aliases.txt` — manual log of outstanding names that need to be mapped.

Manual intervention process:
1. Run the converter via the admin UI or CLI.
2. If 422 errors appear, inspect `missing_aliases.txt` or the script output.
3. Decide whether to add a new alias or create a new athlete row in the master workbook.
4. Update `athlete_aliases` (preferred) and rerun the upload.

---

## 6. Admin Frontend Highlights
File: `src/pages/admin.tsx`
- Tabs: File Upload, Manual Entry, Manage Meets, Athlete Info, Club Info.
- Upload tab shows per-file validation report (inserted vs skipped counts plus issue breakdown).
- Manual entry, athlete, and club panels provide placeholder UI; functionality is still minimal and can be extended as needed.

Keep styling changes minimal—layout has already been approved.

---

## 7. Documentation & Handoff Expectations
- `SESSION_START.md` — operational checklist and command rules.
- `Malaysia Swimming Analytics Handbook.md` (this file) — system overview.
- `WHAT_S_NEXT.md` — live roadmap; update it before you leave a session.
- `PROFESSIONAL_FOLDER_STRUCTURE_ANALYSIS.md` — rationale for folder organization (informational).

When you finish a work block:
1. Update `WHAT_S_NEXT.md` with what was done and what remains.
2. Note any manual data fixes (aliases, clubs, nations) so the next developer understands the context.
3. Commit or stash temp scripts only after confirming with the user; production scripts live under `scripts/` or `temp_scripts/` as appropriate.

---

## 8. Outstanding Work Items (November 2025)
1. **Finalize athlete loader** — rewrite the pass scripts to consume `consolidated_athlete_ID_rebuilt.xlsx` in a single controlled step.
2. **Alias management UI/API** — allow admins to map new aliases without shell access.
3. **Meet validation polishing** — surface nation/club corrections interactively through the admin panel.
4. **Records data entry** — continue populating open/age-group/relay records using the new schema.
5. **Docker parity** — optional; ensure SQLite work transfers cleanly to the PostgreSQL target when requested.

Keep this list in sync with `WHAT_S_NEXT.md` so incoming developers know where to start.

---

## 9. Quick Reference Commands
```cmd
:: Rebuild consolidated athlete workbook
cd "C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics" && "C:\Users\megan\AppData\Local\Programs\Python\Python313\python.exe" temp_scripts\rebuild_consolidated_athletes.py

:: Seed alias table
cd "C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics" && "C:\Users\megan\AppData\Local\Programs\Python\Python313\python.exe" temp_scripts\setup_athlete_aliases.py

:: Check missing aliases after an upload
cd "C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics" && "C:\Users\megan\AppData\Local\Programs\Python\Python313\python.exe" temp_scripts\check_missing_aliases.py

:: Run meet conversion (CLI)
cd "C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics" && "C:\Users\megan\AppData\Local\Programs\Python\Python313\python.exe" scripts\convert_meets_to_sqlite_simple.py <path-to-meet.xls>
```

---

## 10. Contact & Notes
- The project owner will specify any manual overrides (e.g., alias decisions). Log them immediately.
- If the environment suddenly fails or commands hang, verify you followed the command rules from `SESSION_START.md`. Nine times out of ten, a stray newline or missing interpreter path is the culprit.
- Keep the repository tidy: archive deprecated scripts under `archive/` only when the user agrees.

Welcome aboard — keep everything documented, predictable, and ready for the next handoff.
