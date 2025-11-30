# Malaysia Swimming Analytics Handbook

**Last Updated:** 2025-11-30 (Session 23)

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
- **4,281 athletes** (Malaysian + foreign competitors)
- **55,729 results** (competition times)
- **48 meets** (from 2025 SwimRankings data)
- **193 clubs** (with state associations and aliases)
- **151 MOT base times** (34 events, ages 15-23 for non-50m, 18+ for 50m)
- **30,027 USA athletes** (reference data for MAP comparison)
- **221,321 USA period results** (2021-2025 rankings data)
- **24,928 USA delta records** (improvement tracking 15→16, 16→17, 17→18)
- **612 Canada On Track times** (Track 1/2/3 development benchmarks)

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
1. **Base Table Management** - Export/Update MAP/MOT/AQUA/Podium/Canada tables
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
| `mot_base_times` | Malaysia On Track target times | mot_event_id, mot_age (15-23), mot_time_seconds |
| `canada_on_track` | Canada Swimming development tracks | event_id, canada_track (1/2/3), canada_track_age, canada_track_time_seconds, canada_track_year |

**event_id Format:** `{COURSE}_{STROKE}_{DISTANCE}_{GENDER}`
- Example: `LCM_Free_100_M` = Long Course, Freestyle, 100m, Male
- Parse for display: `LCM_Free_100_M` -> "100 Free" + "M"

**Update Schedule:**
- AQUA: January (after World Aquatics publishes) - LCM and SCM tracked separately
- MAP: September (USA Swimming 100th all-time data) - ages 12, 14, 16, 18 manual; 13, 15, 17 interpolated
- MOT: After podium_target_times update - auto-cascades from podium using Canada/USA deltas
- Podium: After each SEA Games (3rd place times for odd years)
- Canada On Track: Annual (3 development tracks with age-specific targets)

**MOT Calculation (see MOT_methodology.md):**
- Anchor point: Canada Track 1 final time, work backwards applying deltas
- Ages 15-18 transitions: USA Swimming median deltas
- If USA median is negative: Fall back to Canada On Track average delta
- Ages 18+ transitions: Canada On Track average deltas (averaged across all tracks)
- 50m events: ages 18+ only (not valid predictors before age 18, insufficient USA data)

### Reference Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `usa_athlete` | USA Swimming athletes for MAP comparison | usa_athlete_id, usa_name, usa_gender (F/M), usa_birthyear |
| `usa_raw_period_data` | USA Swimming period results | usa_raw_event_id, usa_raw_year, usa_athlete_id, usa_raw_time_seconds |
| `usa_delta_data` | USA Swimming improvement data | usa_delta_event_id, usa_athlete_id, usa_delta_age_start/end, usa_delta_median/mean/sd |

**usa_athlete Table:**
- 30,027 athletes parsed from USA Swimming Period Data (2021-2025)
- Birth year calculated from latest period appearance: period_end_year - age
- Keyed by (name, gender) - same name with different gender = separate athletes
- Distribution: 14,736 Female, 15,291 Male (more males in top 500 rankings)

**usa_raw_period_data Table:**
- 221,321 period results linked to usa_athlete_id
- 28 events across 4 years (2022-2025)
- Script: `scripts/create_usa_raw_period_data.py`

**usa_delta_data Table:**
- 24,928 improvement records tracking 15→16, 16→17, 17→18 age transitions
- 3,848 unique athletes with delta records
- Includes statistical columns: median, mean, sd, min, max, q25, q75, iqr
- Script: `scripts/create_usa_delta_data.py`
- Used for MOT ages 15-17 calculations

---

## 4. Global Utilities (Do Not Recreate)

| Function | Location | Purpose |
|----------|----------|---------|
| `find_athlete_ids()` | `src/web/utils/athlete_lookup.py` | Athlete search across both tables |
| `search_athletes_by_name()` | `src/web/utils/name_matcher.py` | Core search function - single source of truth for name matching |
| `match_athlete_by_name()` | `src/web/utils/name_matcher.py` | Fuzzy name matching with Malaysian name patterns |
| `expand_word_variants()` | `src/web/utils/name_matcher.py` | Expand word to spelling variants and nicknames |
| `is_likely_foreign()` | `src/web/utils/foreign_detection.py` | Detect foreign athletes from club/nation data |
| `normalize_stroke()` | `src/web/utils/stroke_normalizer.py` | Standardize stroke names |
| `calculate_aqua_points()` | `src/web/utils/calculation_utils.py` | FINA points calculation |
| `parse_and_validate_date()` | `src/web/utils/date_validator.py` | ISO 8601 date handling |
| `process_results_club()` | `src/web/utils/club_matcher.py` | Club name processing for results import |
| `is_state_name()` | `src/web/utils/club_matcher.py` | Detect if club_name is a state (returns state_code) |
| `is_national_team()` | `src/web/utils/club_matcher.py` | Detect MAS/Malaysia entries |
| `match_club_name()` | `src/web/utils/club_matcher.py` | Fuzzy club name matching with aliases |

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

### Phase 10: Edit Results Feature (Nov 28, 2025)
- Added Edit button to Results column in Meet Management table
- Edit button triggers dropdown menu (currently: comp_place option)
- comp_place modal displays all results for selected meet:
  - Columns: Athlete Name, Event (e.g., "50 Free"), Gender, Time, Place
  - Sorted by stroke order (Free, Back, Breast, Fly, Medley), distance, gender, time
  - Editable Place field with Enter key navigation
- Backend endpoints:
  - GET /admin/meet-results/{meet_id} - fetches results with athlete/event lookups
  - POST /admin/meet-results/update-comp-place - batch update comp_place values
- Extensible dropdown design for future result editing options

### Phase 11: Canada On Track & USA Athlete Tables (Nov 28, 2025)
- Created `canada_on_track` table with 612 development benchmark times
  - 3 tracks (1, 2, 3) representing different development pathways
  - Age-specific times per track (not all ages have all tracks)
  - Script: `scripts/create_canada_on_track.py`
- Built Update Canada On Track modal:
  - Event | Age dropdown | Track dropdown | Time input
  - Track dropdown filters based on selected age (dynamic)
  - Example: F 50 Back age 15 = Track 1 only; age 17 = Tracks 1, 2, 3
- Created `usa_athlete` reference table with 30,027 athletes
  - Parsed from 448 USA Swimming Period Data text files (2021-2025)
  - Birth year calculated: latest_period_end_year - age_at_that_time
  - Keyed by (name, gender) - 14,736 F / 15,291 M
  - Script: `scripts/create_usa_athlete_table.py`
- Added Export/Update buttons for Canada On Track to Base Table Management

### Phase 12: MOT Base Times & USA Delta Data (Nov 28, 2025)
- Created `usa_raw_period_data` table with 221,321 records
  - All USA Swimming period results linked to usa_athlete_id
  - 28 events x 4 years, 0 unmatched athletes
  - Script: `scripts/create_usa_raw_period_data.py`
- Created `usa_delta_data` table with 24,928 improvement records
  - Tracks 15→16, 16→17, 17→18 age transitions
  - 3,848 unique athletes with delta records
  - Added statistical columns (median, mean, sd, min, max, q25, q75, iqr)
  - Script: `scripts/create_usa_delta_data.py`
- Created `mot_base_times` table with 151 records (34 events)
  - Non-50m events: ages 15-23
  - 50m events: ages 18+ only (not valid predictors before age 18)
  - **Methodology (corrected Nov 30):**
    - Anchor point: Canada Track 1 final time, work backwards applying deltas
    - Ages 15-18 transitions: USA Swimming median deltas
    - If USA median is negative: Fall back to Canada On Track average delta
    - Ages 18+ transitions: Canada On Track average deltas
  - All progression errors fixed (older ages always faster)
  - Full methodology documented in `MOT_methodology.md`
  - Script: `scripts/populate_mot_base_times.py`
- Built MOT Admin UI:
  - Export MOT Table button (Excel download)
  - Update MOT Table modal with Male/Female columns
  - Per-row age dropdown (15-23 for 100m+, 18-23 for 50m events)
  - Enter key navigation between rows
  - Backend API: GET/POST `/api/admin/mot-base-times`
- Fixed stroke order sorting for MOT and Canada On Track modals:
  - Order: Free -> Back -> Breast -> Fly -> Medley
  - Then by distance (50, 100, 200, 400, 800, 1500)

### Phase 13: Club Matching & Data Quality (Nov 30, 2025)
- Created `src/web/utils/club_matcher.py` for club name processing:
  - `is_state_name()` - detects 14 state names/codes, returns standard state_code
  - `is_national_team()` - detects MAS/Malaysia entries for international meets
  - `process_results_club()` - full pipeline for results import
  - `match_club_name()` - fuzzy matching with alias support
- Main page enhancements:
  - Team column now uses athlete's `club_code` from athletes table (not results)
  - Added "17+" age group filter (ages 17 and older)
  - Added "Show best times only" filter (keeps fastest per athlete per event)
  - Added "SXL GF" export button (top 100 per event to Excel workbook)
  - Added Club dropdown filter (appears after selecting State)
- Data quality fixes:
  - Reloaded clubs table from corrected spreadsheet (193 clubs)
  - Fixed 5,540 results where state names were stored as clubs
  - Fixed 1,376 "WP"/"WILAYAH PERSEKUTUAN" entries → state_code=KUL
  - Populated club_code for 3,364 athletes from their results
  - Re-linked 25 orphaned results to TAN, Melissa
- Admin panel improvements:
  - Improved athlete search - splits query into words, matches all
  - "NG, ter" now finds "NG, Terance W" AND "NG SHIN JIAN, Terence"

### Phase 14: Athlete Management & Name Matching Refactor (Nov 30, 2025)
- Athlete panel field edit enhancements:
  - Field labels black (#111), current values grey (#888)
  - Dropdowns show current value in grey, turn black when changed
  - State Code dropdown (16 Malaysian states)
  - Club dropdown keyed off state - auto-populates club_code and club_name
  - Nation dropdown: MAS first, then alphabetical IOC codes
  - Gender: M/F only (no placeholder)
  - Birthdate year extended to 1925, passport expiry uses same date format
  - Typing in search clears selected athlete to show results
- Core name matching refactor:
  - Created `search_athletes_by_name()` as single source of truth
  - Searches FULLNAME + aliases
  - Spelling variation expansion (muhd->muhammad, li->lee)
  - Nickname expansion (steve->steven/stephen, mike->michael)
  - Admin search reduced from ~60 lines to ~15 lines
- Export standardization:
  - All 6 exports now use `SELECT *` + `cursor.description`
  - Athletes and Events exports now include ALL columns
  - Consistent pattern: athletes, foreign-athletes, coaches, clubs, events, results

### Phase 15: MOT Landing Page Enhancements (Nov 30, 2025)
- Enhanced MOT landing page (`public/mot/index.html`):
  - Renamed "Understanding the Data" to "Understanding the USA Data"
  - Added "Understanding the Canadian Data" section:
    - Canada On Track Times purpose and methodology from Swimming Canada
    - History: 2013 introduction, 2017 Version 2, current annual updates
    - Canadian Tire/Own The Podium analytics partnership (2M+ results analyzed)
    - Stats grid: 2013, 2017, 2M+, 3 tracks per event
    - Key evolution: World Aquatics A standards integration
  - Moved Reference Links box to after USA Swimming data section
  - Simplified MOT Methodology table:
    - Removed stroke category tiles (Freestyle, Backstroke, etc.)
    - Changed to 2 columns: "50 Free Female" | "50 Free Male" format
    - Single header row "MOT Methodology"
    - All 34 methodology links now working
- Landing page structure now:
  1. Understanding the USA Data (stats grid, key assumptions)
  2. Understanding the Canadian Data (methodology, history, evolution)
  3. MOT Methodology by Event (2-column table)
  4. USA Swimming Raw Results and Improvement Data
  5. Reference Links (Canada On Track)
  6. Footer
- Generated 34 MOT methodology HTML pages (17 events x 2 genders):
  - Script: `scripts/generate_mot_methodology_pages.py`
  - Location: `public/statistical_analysis/reports/`
  - Each page includes: Canada tracks, USA deltas, Canada avg deltas, calculation steps, final MOT times
  - 50m events include warning about age 18+ only limitation

### Phase 16: Landing Pages & Filter Enhancements (Nov 30, 2025)
- Created AQUA Points landing page (`public/aqua/index.html`):
  - Formula explanation: P = 1000 x (B/T)^3
  - Base times from World Records, updated annually
  - Why cubic curve (non-linear rewards excellence)
  - Point scale interpretation (1000=WR, 900+=World Class, etc.)
  - Link to World Aquatics Points System
- Created MAP Points landing page (`public/map/index.html`):
  - Age-adjusted scoring explanation (similar to Hy-Tek Power Points)
  - MAP vs AQUA comparison table
  - Base times from USA All-Time Top 100 per age
  - Why age points matter for development tracking
  - Practical applications with examples
- Main page reference buttons now link to static HTML pages:
  - MAP -> `/map/index.html`
  - MOT -> `/mot/index.html`
  - AQUA -> `/aqua/index.html`
- Data fix: Splash meets course correction
  - SPLSEL25 changed from LCM to SCM (5,694 results)
  - Updated meets.meet_course and results.event_id prefix
- Main page filter enhancements:
  - Year filter: checkbox -> dropdown (dynamic from `/api/available-years`)
  - Added Start/Finish date range filters (dd/mmm/yyyy dropdowns)
  - Layout reorganized: Row 1 = Year + Dates, Row 2 = Type + Scope
  - All dropdowns use `fontSize: 'inherit'` for consistent styling
- Added CLAUDE.md documentation for pool course types and 25m event tracking

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
