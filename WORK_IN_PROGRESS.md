# Work In Progress

**Last Updated:** 2025-11-28

---

## Current Status

**DATABASE:** 4279 athletes, 55701 results, 48 meets
**SwimRankings Upload:** All 2025 data loaded - COMPLETE
**Main Page:** Results table fully functional with filtering, sorting, MAP points
**Admin Panel:** Base Table Management with export and update functionality
**Schema Migration:** All base time tables now use event_id format

---

## Current Goal

Complete the Base Table Management Update interfaces:
1. [x] Update Podium Target Times - COMPLETE (tested, time string conversion working)
2. [x] Update MAP Table - COMPLETE (per-row age dropdown 12-18, year selector 2000-2029)
3. [x] Update AQUA Table - COMPLETE (per-row course dropdown LCM/SCM, year selector 2025-2029)
4. [ ] Create MOT table and build Update MOT Table UI

---

## In Progress

- [x] Build Update Table interfaces for Base Table Management panel
  - [x] Update Podium Target Times Table (SEA Games year dropdown 1959-2031, Enter key navigation)
  - [x] Update AQUA Table (per-row LCM/SCM dropdown, year 2025-2029, course + competition_year columns added)
  - [x] Update MAP Table (per-row age dropdown 12-18, year 2000-2029, competition_year column added)
  - [ ] Update MOT Table (MOT table doesn't exist yet - create first)
- [ ] Populate On Track and Track Gap columns (MOT table integration)
- [ ] Add Target Time column (from podium_target_times)
- [ ] Test SEAG upload with new age group filtering
- [x] Verify MAP points accuracy - MAP base times now complete (ages 12-18)

---

## Completed This Session (2025-11-28)

- [x] Consolidated documentation (WIP, Handbook, deleted redundant strategy files)
- [x] Added 107 missing MAP base times (ages 13, 15, 17 + missing events)
- [x] Migrated all base time tables to event_id schema:
  - aqua_base_times: now uses event_id (LCM_Free_100_M format) + course + competition_year
  - map_base_times: now uses event_id + age + competition_year
  - podium_target_times: now uses event_id + sea_games_year
- [x] Cleaned up podium_target_times schema (removed redundant gender/event/distance/stroke columns)
- [x] Set existing podium data to sea_games_year = 2023
- [x] Built Update Podium Target Times UI (modal with SEA Games year dropdown 1959-2031)
- [x] Added backend endpoints: /admin/podium-target-times, /admin/events-list
- [x] Updated Handbook with new event_id schema documentation
- [x] Built Update MAP Table UI:
  - Per-row age dropdown (12-18) to edit specific age's time
  - Year selector "100th All Time USA Year:" (2000-2029)
  - Added competition_year column to map_base_times
  - Excludes 50m events (MAP doesn't use them)
  - Enter key navigation between inputs
- [x] Built Update AQUA Table UI:
  - Per-row course dropdown (LCM/SCM) to edit specific course's time
  - Year selector "AQUA Points Year:" (2025-2029, no historical data)
  - Added course and competition_year columns to aqua_base_times
  - Enter key navigation between inputs
- [x] Added backend endpoints: /admin/map-base-times, /admin/aqua-base-times (GET and POST)

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
