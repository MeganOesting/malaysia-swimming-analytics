# BLOCKERS — Active Issues

Issues that prevent progress. Document here, resolve ASAP.

**Last Updated:** 2025-11-21

---

## 🔴 Critical (Blocking Development)

| ID | Blocker | Impact | Owner | Status | Workaround |
|----|---------|--------|-------|--------|-----------|
| B002 | RevenueMonster integration undefined | Can't build payment system | [You] | ⏳ Waiting | Research & document API |

---

## 🟡 High (Slowing Progress)

| ID | Blocker | Impact | Owner | Status | Workaround |
|----|---------|--------|-------|--------|-----------|
| B003 | SEAG_2025_ALL.xlsx not uploaded to database | Need complete SEA Games data for athlete tracking | [You] | ⏳ Pending | Upload via admin panel when ready |
| B005 | Feature components need integration test | Can't confirm modular architecture works end-to-end | [You] | ✅ RESOLVED | Authentication works, all features render correctly |

---

## 🟢 Medium (Nice to Fix)

| ID | Blocker | Impact | Owner | Status | Workaround |
|----|---------|--------|-------|--------|-----------|
| (none yet) | — | — | — | — | — |

---

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
