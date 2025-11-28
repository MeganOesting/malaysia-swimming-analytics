# Malaysia Swimming Analytics Handbook

**Last Updated:** 2025-11-28

This handbook provides project context, architecture overview, and development history for stakeholder presentations and developer onboarding.

---

## 1. Project Overview

### Purpose
A web-based analytics platform for Malaysian swimming performance tracking, enabling:
- National team selection support via standardized point systems (AQUA, MAP, MOT)
- Athlete development tracking across age groups
- Meet results management and historical analysis
- Podium target time calculations for international competition benchmarks

### Key Metrics
| Metric | Description |
|--------|-------------|
| AQUA Points | FINA-based performance points for international comparison |
| MAP Points | Malaysia Age Points - rewards improvement within age cohorts |
| MOT (Malaysia On Track) | Development trajectory vs podium targets |

### Current Database (as of Nov 2025)
- **4,279 athletes** (Malaysian + foreign competitors)
- **55,701 results** (competition times)
- **48 meets** (from 2025 SwimRankings data)

---

## 2. Technical Architecture

### Stack
| Layer | Technology |
|-------|------------|
| Frontend | Next.js + React + TypeScript |
| Backend | FastAPI (Python) |
| Database | SQLite (`malaysia_swimming.db` at project root) |
| Authentication | Password-based (MAS2025), no OAuth/JWT yet |

### Key Directories
```
project root/
  malaysia_swimming.db     <- Single source of truth database
  src/
    web/
      main.py              <- API entry point
      routers/admin.py     <- All admin endpoints
      utils/               <- Global utilities (name_matcher, athlete_lookup, etc.)
    admin/
      admin.tsx            <- Main admin orchestrator
      features/            <- Modular feature components
        athlete-management/
        meet-management/
        manual-entry/
        club-management/
        coach-management/
      shared/              <- Shared hooks, components, types
    pages/
      index.tsx            <- Main results page
      admin.tsx            <- Re-exports src/admin/admin.tsx
  scripts/                 <- Production-ready utilities
```

### Admin Panel Tabs
1. **Base Table Management** - Export MAP/MOT/AQUA/Podium tables
2. **Meet Management** - Upload meet files, manage existing meets
3. **Athlete Management** - Search, edit, export athletes
4. **Club Management** - Manage clubs by state
5. **Coach Management** - Manage coaching staff

---

## 3. Database Schema (Current)

### Core Tables
| Table | Purpose | Key Fields |
|-------|---------|------------|
| `athletes` | Malaysian registered swimmers | id, fullname, BIRTHDATE, Gender, nation, club_name, state_code |
| `foreign_athletes` | Non-Malaysian competitors | id, fullname, birthdate, gender, nation, club_name |
| `results` | Competition times | athlete_id, foreign_athlete_id, event_id, meet_id, time_seconds, aqua_points |
| `events` | Event catalog (LCM/SCM) | event_id, course, stroke, distance, gender |
| `meets` | Meet metadata | id, meet_type, meet_alias, meet_date, meet_year |
| `clubs` | Club registry | club_code, club_name, state_code |

### Foreign Athlete System
Two-table system separates Malaysian athletes from foreign competitors:
- `results.athlete_id` -> Malaysian swimmers
- `results.foreign_athlete_id` -> Foreign competitors
- Never both populated for same result

### Stroke Format Standard
Database uses: `Free, Back, Breast, Fly, Medley`
- "Medley" not "IM" for individual medley events
- All normalization via `normalize_stroke()` in `src/web/utils/stroke_normalizer.py`

### Base Time Tables (event_id Schema)
All base time tables use `event_id` as the primary lookup key for consistency with results table.

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `aqua_base_times` | World Aquatics base times | event_id, base_time_seconds, course (LCM/SCM), competition_year |
| `map_base_times` | Malaysia Age Points base times | event_id, age (12-18), base_time_seconds, competition_year |
| `podium_target_times` | SEA Games 3rd place times | event_id, target_time_seconds, sea_games_year |

**event_id Format:** `{COURSE}_{STROKE}_{DISTANCE}_{GENDER}`
- Example: `LCM_Free_100_M` = Long Course, Freestyle, 100m, Male
- Parse for display: `LCM_Free_100_M` -> "100 Free" + "M"

**Update Schedule:**
- AQUA: January (after World Aquatics publishes) - LCM and SCM tracked separately
- MAP: September (USA Swimming 100th all-time data) - ages 12, 14, 16, 18 manual; 13, 15, 17 interpolated
- Podium: After each SEA Games (3rd place times for odd years)

---

## 4. Global Utilities (Do Not Recreate)

| Function | Location | Purpose |
|----------|----------|---------|
| `find_athlete_ids()` | `src/web/utils/athlete_lookup.py` | Athlete search across both tables |
| `match_athlete_by_name()` | `src/web/utils/name_matcher.py` | Fuzzy name matching with Malaysian name patterns |
| `is_likely_foreign()` | `src/web/utils/foreign_detection.py` | Detect foreign athletes from club/nation data |
| `normalize_stroke()` | `src/web/utils/stroke_normalizer.py` | Standardize stroke names |
| `calculate_aqua_points()` | `src/web/utils/calculation_utils.py` | FINA points calculation |
| `parse_and_validate_date()` | `src/web/utils/date_validator.py` | ISO 8601 date handling |

---

## 5. Development History

### Phase 1: Database Foundation (Early Nov 2025)
- Consolidated 6 database files into single authoritative `malaysia_swimming.db`
- Established 47-field athlete schema from SportEngine registration data
- Created events catalog (LCM/SCM, individual/relay)
- Seeded clubs table from state-based registration

### Phase 2: Admin Panel Architecture (Mid Nov 2025)
- Migrated from monolithic `admin.tsx` (2,200+ lines) to modular feature architecture
- Created 5 feature modules under `src/admin/features/`
- Implemented shared components, hooks, and types
- Standardized UI styling (red buttons #cc0000, consistent layouts)

**Migration Completed:**
- Phase 2A: Tab reorganization (5 organized tabs)
- Phase 2B: Feature extraction (all features modularized)
- Phase 2C: UI standardization and authentication flow

### Phase 3: Name Matching System (Late Nov 2025)
- Built word-based name matching algorithm for Malaysian naming patterns
- Implemented weighted scoring (common names 0.3, identifier names 1.0)
- Added nickname expansion (Terance->Terence, MUHD->Muhammad, etc.)
- Created nation corrections table for results file errors

### Phase 4: Foreign Athlete Handling (Nov 26, 2025)
- Created `foreign_athletes` table for non-Malaysian competitors
- Added `foreign_athlete_id` column to results table
- Implemented 4-step search: athletes -> foreign_athletes -> corrections -> manual review
- Established policy: never auto-create, always manual review for unmatched

### Phase 5: SwimRankings Data Load (Nov 26-27, 2025)
- Loaded all 2025 SwimRankings data (55,701 results)
- Fixed duplicate detection bug (key format mismatch)
- Cleaned 8,011 duplicate rows
- Added 72 unique unmatched athletes
- Achieved 100% match rate on preview

### Phase 6: Main Page Results Table (Nov 28, 2025)
- Implemented results table with filtering, sorting, pagination
- Added MAP points calculation and display
- Created Year/Type/Scope filter system
- Added meet alias display, club codes, nation from athlete records
- Implemented sortable columns (Time, AQUA, MAP, Comp Place)

### Phase 7: Base Table Management (Nov 28, 2025)
- Renamed "Manual Entry" to "Base Table Management"
- Created export endpoints for MAP/MOT/AQUA/Podium tables
- Fixed meet_date NULL values
- Removed deprecated aqua_points from podium_target_times

### Phase 8: Schema Standardization & Update UIs (Nov 28, 2025)
- Migrated all base time tables to use `event_id` as primary lookup key
- event_id format: `{COURSE}_{STROKE}_{DISTANCE}_{GENDER}` (e.g., LCM_Free_100_M)
- Added 107 missing MAP base times (ages 13, 15, 17 via interpolation formula)
- Cleaned podium_target_times schema: now only id, event_id, target_time_seconds, sea_games_year
- Built Update Podium Target Times UI with SEA Games year dropdown (odd years 1959-2031)
- Added backend endpoints: /admin/podium-target-times, /admin/events-list
- Consolidated documentation: merged Handbook, cleaned WIP, deleted redundant strategy files

### Phase 9: Complete Base Table Update UIs (Nov 28, 2025)
- Built Update MAP Table UI:
  - Per-row age dropdown (12-18) for editing specific age group times
  - Year selector "100th All Time USA Year:" (2000-2029)
  - Added `competition_year` column to map_base_times table
  - Excludes 50m events (not used in MAP scoring)
  - Enter key navigation between input fields
- Built Update AQUA Table UI:
  - Per-row course dropdown (LCM/SCM) for editing specific course times
  - Year selector "AQUA Points Year:" (2025-2029, no historical data)
  - Added `course` and `competition_year` columns to aqua_base_times table
  - Enter key navigation between input fields
- All modals share consistent design: two-column Male/Female layout, red dropdown buttons
- Backend endpoints: GET/POST for /admin/map-base-times, /admin/aqua-base-times
- Time string to seconds conversion handled server-side (e.g., "2:17.65" -> 137.65)

---

## 6. Key Design Decisions

### Why Two Athlete Tables?
1. **Clean Malaysian database** - Development tracking only for eligible swimmers
2. **No ID collisions** - Separate ID sequences
3. **Different data needs** - Malaysian athletes have IC, registration data; foreign only basic info
4. **Query simplicity** - Easy to filter "all Malaysian results"

### Why Medley Not IM?
Standardization across all stroke references:
- Database stores: Free, Back, Breast, Fly, Medley
- Event IDs use: `LCM_Medley_200_F` (not `LCM_IM_200_F`)
- Single source of truth via `normalize_stroke()`

### Why Skip Relays?
Relay results lack age group data needed for proper results table entry:
- Individual results have athlete birthdate -> calculate day_age, year_age
- Relays have team names only, no individual athlete data
- Deferred until relay storage design is completed

### Why No Auto-Create Foreign Athletes?
Results file nation can be WRONG:
- Malaysian living abroad coded as "USA"
- Foreign residents coded as "MAS"
- Admin must manually verify before adding to correct table

---

## 7. Startup Protocol

### Launch Website
```
cd "C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics"
Double-click: WEBSITE_LOAD_START.bat
```
This starts backend (port 8000) and frontend (port 3000).

### Start Claude Session
```
/claude
Task: Read WORK_IN_PROGRESS.md and BLOCKERS.md.
Summarize where we left off (max 5 lines).
List next 5 actionable items.
```

### End Session
```
Task: Update WORK_IN_PROGRESS.md - mark finished tasks, add new incomplete tasks.
If blockers found, update BLOCKERS.md.
Git commit if work accomplished.
```

---

## 8. Documentation Map

| File | Purpose |
|------|---------|
| `WORK_IN_PROGRESS.md` | Current tasks, TODO items, personal reminders |
| `BLOCKERS.md` | Active issues blocking progress |
| `CLAUDE.md` | Development protocols and coding standards |
| `CODING_SESSION_START.md` | Startup/shutdown protocols |
| This Handbook | Project overview, architecture, history |

---

## 9. Resolved Blockers Summary (For Presentation)

| Issue | Resolution | Impact |
|-------|------------|--------|
| 6 database files | Consolidated to single authoritative DB | Clean data architecture |
| Athlete name matching | Word-based algorithm with Malaysian patterns | 92%+ match rate |
| Stroke format inconsistency | Global normalize_stroke() function | Zero format errors |
| Foreign athlete confusion | Two-table system with manual review | Clean separation |
| Duplicate results | Fixed key format, cleaned 8,011 rows | Accurate data |
| Admin panel monolith | Modular 5-feature architecture | Maintainable code |

---

## 10. Contact & Governance

- Database changes require validation against CLAUDE.md protocols
- All date fields must use ISO 8601 format: `YYYY-MM-DDTHH:MM:SSZ`
- No Unicode characters in Python code (Windows cp1252 encoding)
- Use global utilities - never recreate matching/detection logic

---
