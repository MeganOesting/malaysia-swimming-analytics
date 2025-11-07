# 🚀 Malaysia Swimming Analytics — Session Startup Guide

Use this checklist at the beginning of every engagement. New developer? New chat? Read this file first, out loud, with the user so everyone agrees on the ground rules.

1. Tell the user you are reading the startup guide.
2. Recite the command rules below verbatim.
3. Confirm the current focus items and agree on the first task.

---

## 🚦 Assistant Command Rules (read verbatim)
- **Shell:** Windows `cmd.exe` only. No heredocs, no raw newlines inside `python -c`.
- **Interpreter path:** Always prefix Python calls with the explicit interpreter:
  ```cmd
  cd "C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics" && "C:\Users\megan\AppData\Local\Programs\Python\Python313\python.exe" <command>
  ```
- **Plan first.** Describe the steps you intend to run and wait for approval when the workflow is new or destructive.
- **Long commands → script.** If you cannot keep it on one line, write a helper in `temp_scripts/` and run that file instead of pasting multi-line code.
- **Repeat these rules** at the start of every session or when the user asks.

Quick health check: `"…python.exe" scripts\session_checkup.py` (run from a clean shell).

---

## 📍 Project Snapshot (November 2025)
- **Active stack:** FastAPI backend + SQLite + Next.js frontend.
- **Database:** `malaysia_swimming.db` with tables `athletes`, `athlete_aliases`, `events`, `meets`, `results`, `records`, `record_history`, `states`, `clubs`.
- **Primary data sources:**
  - `data/manual_matching/consolidated_registration_subset.xlsx`
  - `data/manual_matching/consolidated_results_athlete_birthdat_fullname.xlsx`
  - merged output `data/manual_matching/consolidated_athlete_ID_rebuilt.xlsx`
- **Key scripts:**
  - `scripts/convert_meets_to_sqlite_simple.py`
  - `temp_scripts/rebuild_consolidated_athletes.py`
  - `temp_scripts/setup_athlete_aliases.py`
  - `temp_scripts/check_missing_aliases.py`
- **Current focus:** rebuild the athlete master list + alias table, validate SUKMA uploads through the admin UI, and document every manual correction for the next developer.

Legacy Flask app exists for reference only—do not modify it unless the user explicitly says so.

---

## 🧭 Startup Modes
### New system (default)
- **Backend:**
  ```cmd
  cd "C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics"
  uvicorn src.web.main:app --reload --host 127.0.0.1 --port 8000
  ```
- **Frontend (separate terminal):**
  ```cmd
  cd "C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics"
  npm run dev
  ```
- **Tip:** keep backend, frontend, and manual command shells separate. Killing `npm run dev` prompts will drop the frontend.

### Legacy reference (only if you must compare behaviour)
```cmd
cd "C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics\Malaysia Times Database"
python -m Malaysia_Times_Database.Malaysia_Database
```

### Docker stack (optional parity)
```cmd
cd "C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics"
docker-compose up -d
```

### Access points
- Frontend: <http://localhost:3000>
- Admin panel: <http://localhost:3000/admin> (password `MAS2025`)
- API base: <http://localhost:8000>
- Docs: <http://localhost:8000/api/docs>

---

## ✅ Session Checklist
1. Backend + frontend terminals running? (`uvicorn` and `npm run dev`).
2. Dependencies current?
   - `"…python.exe" -m pip install -r requirements.txt`
   - `npm install`
3. Database snapshot: `"…python.exe" verify_database.py`.
4. Quick counts:
   ```cmd
   cd "C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics" && "C:\Users\megan\AppData\Local\Programs\Python\Python313\python.exe" -c "import sqlite3; c=sqlite3.connect('malaysia_swimming.db'); cur=c.cursor(); cur.execute('SELECT COUNT(*) FROM athletes'); print('athletes:', cur.fetchone()[0]); cur.execute('SELECT COUNT(*) FROM results'); print('results:', cur.fetchone()[0]); c.close()"
   ```
5. Run `scripts/session_checkup.py` for a full diagnostic if anything looks off.

---

## 📦 Focus Items
1. **Athlete master rebuild**
   - Refresh merged workbook: `temp_scripts/rebuild_consolidated_athletes.py`.
   - Load `athletes` table from the rebuilt sheet (coordinate with user on final loader script).
   - Seed aliases: `temp_scripts/setup_athlete_aliases.py`; append new variants as SUKMA uploads reveal them (`temp_scripts/check_missing_aliases.py`).
2. **Meet upload QA**
   - Use `scripts/convert_meets_to_sqlite_simple.py` (no other converter is supported).
   - Capture validation errors; log unresolved names in `temp_scripts/missing_aliases.txt`.
   - Confirm admin UI reflects inserted vs skipped counts and prints PDF summary correctly.
3. **Documentation & handoff**
   - Keep `Malaysia Swimming Analytics Handbook.md` and `WHAT_S_NEXT.md` aligned with real progress.
   - Record nation/club overrides or alias decisions before ending the session.

---

## 🔍 Quick Reference
- Backend entry: `src/web/main.py`
- Admin router: `src/web/routers/admin.py`
- Admin UI: `src/pages/admin.tsx`
- Meet converter: `scripts/convert_meets_to_sqlite_simple.py`
- Consolidation helpers: `temp_scripts/rebuild_consolidated_athletes.py`, `temp_scripts/setup_athlete_aliases.py`, `temp_scripts/check_missing_aliases.py`
- Database: `malaysia_swimming.db`

---

## 🧠 Legacy vs New Tips
- Legacy system is reference-only. Mirror behaviour; do not edit it without explicit instruction.
- UI styling is locked—stick to behavioural fixes.
- When you discover a new rule (alias format, nation override, etc.), document it immediately for the next developer.

---

## 🤝 Ready to Work
1. Tell the user you have reviewed this guide.
2. Spin up backend and frontend (or confirm they are already running).
3. Align on the first focus item (athlete rebuild, alias mapping, or upload QA).
4. Keep notes of manual fixes, then update `WHAT_S_NEXT.md` before you sign off.

Thanks for keeping the project handoff-ready.


