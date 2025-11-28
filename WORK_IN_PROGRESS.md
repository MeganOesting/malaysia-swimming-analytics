# Work In Progress

**Last Updated:** 2025-11-28 (Session 20)

---

## Current Status

**DATABASE:** 4279 athletes, 55704 results (223 SEA Age incl 3 DQs), 48 meets
**USA Reference Data:** 30,027 athletes, 221,321 period results, 24,928 delta records
**MOT Base Times:** 287 records (34 events x 9 ages, minus 50m events ages 15-17)
**SwimRankings Upload:** All 2025 data loaded - COMPLETE
**Main Page:** Results table with filtering, sorting, MAP points, result_status display
**Admin Panel:** Base Table Management + Edit Results with comp_place AND status support
**Schema Migration:** All base time tables now use event_id format (redundant columns removed)

---

## Current Goal

Complete Admin Features:
1. [x] Update Podium Target Times - COMPLETE
2. [x] Update MAP Table - COMPLETE
3. [x] Update AQUA Table - COMPLETE
4. [x] Edit Results comp_place/status - COMPLETE (supports both numbers and DQ/DNS/DNF/SCR)
5. [x] Create MOT table - COMPLETE (287 records populated)
6. [ ] Build Update MOT Table UI

---

## In Progress

- [x] Build Update Table interfaces for Base Table Management panel
  - [x] Update Podium Target Times Table (SEA Games year dropdown 1959-2031, Enter key navigation)
  - [x] Update AQUA Table (per-row LCM/SCM dropdown, year 2025-2029, course + competition_year columns added)
  - [x] Update MAP Table (per-row age dropdown 12-18, year 2000-2029, competition_year column added)
  - [ ] Update MOT Table (table created, need UI)
- [ ] Integrate MOT times into main page (MOT, MOT Aqua, MOT Gap columns)
- [ ] Add Target Time column (from podium_target_times)
- [ ] Test SEAG upload with new age group filtering
- [x] Verify MAP points accuracy - MAP base times now complete (ages 12-18)

---

## Completed This Session (2025-11-28 - Session 20)

### MOT Base Times Table - COMPLETE
- [x] Created `mot_base_times` table with 306 rows (34 events x 9 ages)
- [x] Columns: mot_event_id, mot_age (15-23), mot_time_seconds
- [x] Age 23 = podium_target_time (most recent SEA Games year)
- [x] Ages 18-22 = calculated from Canada On Track deltas (Track 1/2/3 blending by final age)
- [x] Ages 15-17 = calculated from USA delta medians
- [x] 50m events: ages 18-23 only (no USA data for ages 15-17)
- [x] 287 rows populated, 19 NULL (50m events ages 15-17)
- [x] Methodology documented in `MOT_methodology.md`
- [x] Script: `scripts/populate_mot_base_times.py`

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

### Results Unpopulated Club Data
- [ ] Create admin button to scan results table for missing club data
- [ ] Show sample records: fullname, meetname, meetdate (dd.mm.yyyy format)
- [ ] Allow manual state/club assignment via dropdown

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