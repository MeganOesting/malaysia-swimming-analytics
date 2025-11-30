# Work In Progress

**Last Updated:** 2025-11-30 (Session 23)

---

## Current Status

**DATABASE:** 4281 athletes, 55729 results (223 SEA Age incl 3 DQs), 48 meets, 193 clubs
**USA Reference Data:** 30,027 athletes, 221,321 period results, 24,928 delta records
**MOT Base Times:** 287 records (34 events x 9 ages, minus 50m events ages 15-17)
**SwimRankings Upload:** All 2025 data loaded - COMPLETE
**Main Page:** Results table with filtering, sorting, MAP points, MOT columns, Team from athlete record
**Admin Panel:** Base Table Management + Edit Results + Enhanced Athlete Management
**Clubs:** 193 clubs with matching utility for state/national detection
**Name Matching:** Core search function with spelling/nickname expansion

---

## Current Goal

Athlete Management & Data Uploads:
1. [x] Fix Team column to use athlete's club from athletes table
2. [x] Add club filtering (State -> Club dropdown)
3. [x] Create SXL GF export (top 100 per event)
4. [x] Fix state names stored as clubs in results
5. [x] Populate athlete club_code from results
6. [x] Enhance athlete panel field edit process
7. [x] Refactor name matching to single source of truth
8. [x] Standardize all table exports to use all columns
9. [ ] Upload SEAG_2025_ALL.xlsx to database
10. [ ] Upload 2024/2025 SEA Age and AYG results

---

## In Progress

- [x] Main page Team column uses athlete's club_code (not results club)
- [x] Club matcher utility for imports (`src/web/utils/club_matcher.py`)
- [x] State/Club dropdown filtering on main page
- [x] Core name matching function (single source of truth)
- [ ] Add Target Time column (from podium_target_times)
- [ ] Test SEAG upload with new age group filtering

---

## Completed This Session (2025-11-30 - Session 23)

### MOT Landing Page Enhancements
- [x] Renamed "Understanding the Data" to "Understanding the USA Data"
- [x] Added "Understanding the Canadian Data" section with:
  - Canada On Track Times purpose and methodology
  - History: 2013 introduction, 2017 Version 2, current version
  - Canadian Tire/Own The Podium analytics partnership (2M+ results analyzed)
  - Stats grid: key milestones (2013, 2017, 2M+, 3 tracks)
  - Key evolution points and links to Swimming Canada resources
- [x] Moved Reference Links box from top to bottom (after USA Swimming data section)
- [x] Simplified MOT Methodology table:
  - Removed stroke category tiles (Freestyle, Backstroke, etc.)
  - Changed to 2 columns: "50 Free Female" | "50 Free Male" format
  - Single header row "MOT Methodology"
- [x] Generated ALL 34 MOT methodology HTML pages (17 events x 2 genders)
  - Script: `scripts/generate_mot_methodology_pages.py`
  - Each page includes: Canada tracks, USA deltas, Canada deltas, calculation steps, MOT times
  - 50m events show warning about age 18+ only limitation
- [x] Updated MOT landing page - all methodology links now working (no more "Coming Soon")

### Landing Pages Created
- [x] AQUA Points landing page (`public/aqua/index.html`)
  - Formula explanation, base times, cubic curve rationale
  - Links to World Aquatics
- [x] MAP Points landing page (`public/map/index.html`)
  - Age-adjusted scoring explanation
  - MAP vs AQUA comparison
  - USA All-Time Top 100 base times
  - Practical applications and examples

### Data Fixes
- [x] Fixed Splash meets course: SPLSEL25 changed from LCM to SCM
  - Updated 5,694 results: meet_course = SCM, event_id prefix LCM_ to SCM_
  - Updated meets table: meet_course = SCM
- [x] Added CLAUDE.md documentation for pool course and 25m event tracking

### Main Page Filter Enhancements
- [x] Year filter changed from checkboxes to dropdown
  - Dynamic: fetches available years from database via `/api/available-years`
  - Shows years that have meets (currently 2024, 2025)
- [x] Added Start/Finish date range filters
  - Three dropdowns each: dd, mmm, yyyy
  - Filters meets by date range
  - "Clear" button appears when any date field is set
- [x] Reorganized filter layout:
  - Row 1: Year dropdown + Start date + Finish date + Clear button
  - Row 2: Type checkboxes + Scope checkboxes
- [x] All dropdowns use `fontSize: 'inherit'` to match surrounding text
- [x] Meets section now shows when Type and Scope are selected (year optional)

---

## Completed Previous Session (2025-11-30 - Session 22)

### Athlete Panel Field Edit Enhancements
- [x] Field labels now black (#111), current data values grey (#888)
- [x] All dropdowns show current value in grey, turn black when changed
- [x] Added State Code dropdown (16 Malaysian states)
- [x] Club dropdown keyed off state_code - shows "Club Name (CODE)"
- [x] Selecting club auto-populates both club_code and club_name
- [x] Nation dropdown: MAS first, then alphabetical IOC codes
- [x] Gender dropdown: only M/F options (removed "-" placeholder)
- [x] Birthdate year dropdown extended to 1925 (100 years)
- [x] Passport expiry date now uses dd/MMM/yyyy dropdowns like birthdate
- [x] Typing in search box clears selected athlete (shows results again)

### Core Name Matching Refactor
- [x] Created `search_athletes_by_name()` in `src/web/utils/name_matcher.py`
  - Single source of truth for name-based athlete search
  - Searches FULLNAME + athlete_alias_1 + athlete_alias_2
  - Spelling variation expansion (muhd->muhammad, li->lee, etc.)
  - Nickname expansion (steve->steven/stephen, mike->michael)
  - Word splitting with comma/space handling
- [x] Admin athlete search now calls core function
  - Reduced from ~60 lines to ~15 lines
  - Automatically benefits from any name matcher improvements

### Export Standardization
- [x] All table exports now use `SELECT *` + `cursor.description`
- [x] Athletes export updated: exports ALL columns (was only 3)
- [x] Events export updated: exports ALL columns (was only 7)
- [x] Consistent pattern across all 6 export functions:
  - athletes, foreign-athletes, coaches, clubs, events, results

---

## Completed Previous Session (2025-11-30 - Session 21)

### Main Page Enhancements
- [x] Team column now pulls from `athletes.club_code` (not results table)
- [x] Added "17+" age group filter (ages 17 and older)
- [x] Added "Show best times only" filter - keeps only fastest result per athlete per event
- [x] Added "SXL GF" export button - Excel workbook with top 100 per event per sheet
- [x] Added Club dropdown filter (appears after selecting State)
- [x] `/api/clubs?state_code=XXX` endpoint to get clubs by state

### Club Matching System (`src/web/utils/club_matcher.py`)
- [x] `is_state_name()` - detects if club_name is actually a state (returns state_code)
- [x] `is_national_team()` - detects MAS/Malaysia entries (international meets)
- [x] `process_results_club()` - full processing for results import:
  - State name → set state_code, clear club
  - National team → clear both (international meet)
  - Club name → match to clubs table, get club_code
- [x] Fuzzy matching: handles commas, state suffixes, aliases
- [x] Tracks unmatched clubs for reporting

### Data Quality Fixes
- [x] Reloaded clubs table from corrected spreadsheet (193 clubs)
  - Fixed duplicates: AMAT (PRK) → PRAP, TITAN (SEL) → CYBER
- [x] Fixed 5,540 results where state names were stored as clubs
  - Selangor, Johor, Sabah, etc. → state_code set, club cleared
- [x] Fixed 1,376 results with "WP"/"WILAYAH PERSEKUTUAN" → state_code=KUL
- [x] Populated club_code for 3,364 athletes from their results
- [x] Fixed 3 "Dive Buddy Swim School" athletes → BUDDY club
- [x] Fixed 3 "WP Kuala Lumpur"/"WP Putrajaya" athletes → state only
- [x] Re-linked 25 orphaned results to TAN, Melissa (foreign_athlete_id=53 deleted)

### Admin Panel Improvements
- [x] Improved athlete search - splits query into words, matches all
  - "NG, ter" now finds both "NG, Terance W" AND "NG SHIN JIAN, Terence"

---

## Completed Session 20 (2025-11-28)

### MOT Base Times Table - COMPLETE (Updated 2025-11-30)
- [x] Created `mot_base_times` table with entries for 34 events
- [x] Columns: mot_event_id, mot_age, mot_time_seconds
- [x] **Methodology (corrected):**
  - Ages 15-18 transitions: USA Swimming median deltas
  - If USA median is negative: Fall back to Canada On Track average delta
  - Ages 18+ transitions: Canada On Track average deltas (averaged across all tracks with that transition)
  - Anchor point: Canada Track 1 final time, work backwards applying deltas
- [x] **50m events:** Start at age 18 only (not valid predictors before age 18, insufficient USA data)
- [x] **Non-50m events:** Start at age 15
- [x] All progression errors fixed (older ages always faster)
- [x] Methodology documented in `MOT_methodology.md` and HTML pages per event
- [x] Script: `scripts/populate_mot_base_times.py`

### MOT Admin UI - COMPLETE
- [x] Export MOT Table button (Excel download)
- [x] Update MOT Table modal with:
  - Male/Female columns side by side
  - Per-row age dropdown (15-23 for 100m+, 18-23 for 50m events)
  - Enter key navigation between rows
  - Events sorted: Free → Back → Breast → Fly → Medley, then by distance
- [x] Backend API: GET/POST `/api/admin/mot-base-times`
- [x] Fixed stroke order sorting for both MOT and Canada On Track modals

### MOT Main Page Integration - COMPLETE
- [x] Added `calculate_mot_data()` function in `calculation_utils.py`
  - Looks up MOT time for event + age (capped at 23 for swimmers 23+)
  - Calculates AQUA points for MOT time
  - Calculates gap: swimmer's AQUA - MOT AQUA
- [x] MOT columns now populated on main page:
  - **MOT**: Target time for swimmer's age (e.g., "1:03.71")
  - **MOT Aqua**: AQUA points for MOT time
  - **MOT Gap**: Difference with color coding (green = ahead, red = behind)
- [x] Swimmers 23+ use age 23 MOT targets (podium time)
- [x] Default sort changed to AQUA descending (highest first)
- [x] MOT Gap sorting: swimmers with MOT first (by gap), then without (by MAP desc)

### USA Data Tables - COMPLETE
- [x] Created `usa_raw_period_data` table with 221,321 records
- [x] Columns: usa_raw_event_id, usa_raw_year, usa_athlete_id, usa_raw_time_seconds
- [x] Parsed 448 text files, 0 unmatched athletes
- [x] Script: `scripts/create_usa_raw_period_data.py`
- [x] Created `usa_delta_data` table with 24,928 records
- [x] Columns: usa_delta_event_id, usa_athlete_id, usa_delta_age_start/end, usa_delta_time_start/end
- [x] Added: usa_delta_improvement_seconds, usa_delta_improvement_percentage
- [x] Added: usa_delta_median, usa_delta_mean, usa_delta_sd, usa_delta_min, usa_delta_max, usa_delta_q25, usa_delta_q75, usa_delta_iqr
- [x] 3,848 unique athletes with delta records
- [x] Script: `scripts/create_usa_delta_data.py`

---

## Completed Previous Session (2025-11-28 - Session 19)

### Canada On Track Table
- [x] Created `canada_on_track` table with 612 records (Track 1, 2, 3 times)
- [x] Columns: event_id, canada_track (1/2/3), canada_track_age, canada_track_time_seconds, canada_track_year
- [x] Added Export Canada On Track Table button to Base Table Management
- [x] Added Update Canada On Track Table button with modal UI
- [x] Modal features: Event | Age dropdown | Track dropdown (filtered by age) | Time input
- [x] Track dropdown dynamically filters based on selected age (e.g., age 15 = Track 1 only)

### USA Athlete Reference Table
- [x] Created `usa_athlete` table with 30,027 athletes from USA Swimming data
- [x] Columns: usa_athlete_id, usa_name, usa_gender (F/M), usa_birthyear
- [x] Birth year calculated from latest period appearance (period_end_year - age)
- [x] Parsed 448 text files across 4 time periods (9.1.21-8.31.22 through 9.1.24-8.31.25)
- [x] Gender extracted from filename (F/M prefix); keyed by (name, gender) so same name different gender = different athletes
- [x] Distribution: 14,736 Female, 15,291 Male (more males in top 500 rankings across events/years)
- [x] Script: `scripts/create_usa_athlete_table.py`

---

## Completed Previous Session (2025-11-28 - Session 18)

### Result Status & Edit Results Enhancements
- [x] Added `result_status` column to results table (OK, DQ, DNS, DNF, SCR)
- [x] Fixed Edit Results modal to open directly (removed intermediate dropdown)
- [x] Fixed UUID handling in save - was incorrectly using parseInt on UUID strings
- [x] Edit modal now accepts BOTH numbers (comp_place) AND status codes (DQ, DNS, DNF, SCR)
  - Enter number → saves to comp_place, sets status to OK
  - Enter DQ/DNS/DNF/SCR → saves to result_status, clears comp_place and time
- [x] Main page Place column shows result_status when comp_place is null and status != OK
- [x] Results sort: numeric places first (1,2,3...), then DQ, DNS, DNF, SCR at bottom
- [x] AQUA/Rudolph points auto-cleared when status set to DQ/DNS/DNF/SCR

### SEA Age Data Fixes
- [x] Added 3 DQ results: LEE Xue Wen (200 Breast), LEE Dominic (200 Breast), MANUEL Nishan (50 Back)
- [x] Cleared time/points for DQ results (DQ = no time, no points)
- [x] SEA Age results now total 223 (220 OK + 3 DQ)

### SwimRankings Upload Fixes
- [x] SwimRankings "Place" column is RANKING, not comp_place - stopped populating comp_place
- [x] Cleared comp_place for all 55,480 non-SEA Age results (was incorrectly showing rankings)

### SEAG Upload Enhancements
- [x] Added STATUS column support (between PLACE and MEETDATE)
- [x] DQ/DNS/DNF/SCR results: time not required, stored with blank time and appropriate status
- [x] Duplicate detection handles status results correctly

### Schema Cleanup
- [x] Removed redundant columns from aqua_base_times (gender, event, distance, stroke)
- [x] Removed redundant columns from map_base_times (gender, event)
- [x] All base tables now use event_id only (no duplicate columns)

### Main Page UI Updates
- [x] Renamed column headers: "On Track Target Time" → "MOT", "On Track AQUA" → "MOT Aqua", "Track Gap" → "MOT Gap"
- [x] Made MOT Gap column sortable (click header to sort)
- [x] Default sort for multiple events changed: now sorts by AQUA points (desc) instead of place
- [x] Updated Result interface: place can be number or string (DQ, DNS, etc.), added sort_place field

### Previous Session Items (kept for reference)
- [x] Consolidated documentation (WIP, Handbook, deleted redundant strategy files)
- [x] Added 107 missing MAP base times (ages 13, 15, 17 + missing events)
- [x] Built Update Podium/MAP/AQUA Table UIs with Enter key navigation
- [x] Backend endpoints for all base table management

---

## TODO (Not Started)

### High Priority
- [ ] Upload SEAG_2025_ALL.xlsx to database (B003 - now unblocked)
- [ ] Upload 2024 results including SEA Age results (manual upload)
- [ ] Upload 2025 AYG results (manual upload)
- [ ] Add passport type information to athletes table (user has spreadsheets to read)
- [ ] RevenueMonster payment integration research (B002)

### Athlete Club Data
- [x] Populate athlete club_code from results - COMPLETE (3,364 athletes updated)
- [x] Fix state names stored as clubs - COMPLETE (5,540 results fixed)
- [ ] 166 athletes still without club (only competed at state/national level)
- [ ] Script to update athlete clubs from new results (`scripts/update_athlete_clubs.py` - ready to run)

### Athlete Management UI
- [ ] Add ability to ADD aliases (not just edit existing)
- [ ] Make athlete edit UI cleaner and more compact (like main page style)

### Future Uploads
- [ ] Add time_string_prelims and time_string_finals columns for prelim/final format meets
- [ ] Test with SUKMA results PDFs

---

## Deferred Tasks

### Relay Events
**STATUS:** Relays intentionally SKIPPED in all uploads
- Relay results lack age group data needed for proper results table entry
- Sheets skipped: LAP, TOP, 4X, 5000
- **TODO LATER:** Design relay storage (team-based? linked to athletes?)

### TypeScript Error
- [ ] Fix compilation error in meet-management.tsx (extra closing div) - not blocking

---

## Known Data Quality Notes

### Athletes with Birthdate Discrepancies
These athletes have different birthdates in different SwimRankings files:
- LOO, Jhe Yee
- Muhammad Irish D
- KOEK GELACIO, Amanda M
Will be corrected during 2026 registration.

### Athletes to Watch
| Name | Note |
|------|------|
| MU ZI LONG, Lewis | DSA Swimming Club, registered MAS but NOT eligible - confirm nation |
| Sarah Ignasaki | Female, NOT eligible to represent MAS - alert when found |

### Future Enhancement
Add `athlete_type` field to athletes/foreign_athletes tables for:
- Pool Open, Pool Masters, Pool Para, Open Water
Athletes can have multiple types. Defer implementation.

---

## Post-Upload Reminders

After loading results:
1. Run `python scripts/check_duplicate_results.py`
2. Run `python scripts/check_duplicate_athletes.py`

---

## Personal Reminders (Non-Code)

### Malaysia TD Work
- Course letter review - adjust if needed
- MUST TELL everyone: Foundations required before Level 1 (check skip requirements)
- Schedule through states: KL end of Jan Foundations, Feb Level 1 (Feb 10-13)
- MIAG meet: Feb 5-8th

### SEA Age Selection Criteria
- Remind SEA Age this is their only qualifying opportunity
- If changing criteria, announce before Jan 1st
- Proposed: A qualifiers ranked 1-3, then remaining B qualifiers ranked 1-3
- Ask athletes for confirmation FIRST, then fill event programs
- Open events go to top MAP point scorers (development priority)
- Run proposal by Marylin and Nurul

### Courses
- Need: teaching instructor manual, student course material, good slides
- Check slides for duplicates (long axis has duplicate)
- Make sure slides match course outline

---
NOTE i asked eric and Magnus to give me comp place for Worlds world jrs adn WUGS, also i can note lead off times for relays from these meets, will be a manual entry