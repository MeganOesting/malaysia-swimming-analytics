# Malaysia Swimming Analytics Handbook

**Last Updated:** 2025-12-03 (Session 29)

This handbook provides project context, architecture overview, and development history for stakeholder presentations and developer onboarding.

---

## 1. Project Overview

### Purpose
A web-based analytics platform for Malaysian swimming performance tracking, enabling:
- National team selection support via standardized point systems (AQUA, MAP, MOT)
- Athlete development tracking across age groups
- Meet results management and historical analysis
- Podium target time calculations for international competition benchmarks
- **Online athlete registration** (2026 and beyond)

### Key Metrics
| Metric | Description |
|--------|-------------|
| AQUA Points | FINA-based performance points for international comparison |
| MAP Points | Malaysia Age Points - rewards improvement within age cohorts |
| MOT (Malaysia On Track) | Development trajectory vs podium targets |

### Current Database (as of Dec 2025)
**Now hosted on Supabase (cloud PostgreSQL)** - migrated from local SQLite

- **7,647 athletes** (7,446 MAS + 201 foreign competitors) - 3 duplicates merged
- **55,703 results** (competition times)
- **48 meets** (from 2025 SwimRankings data)
- **193 clubs** (with state associations and aliases)
- **4 coaches** (Magnus, Clara, Mark, Albert with state assignments)
- **151 MOT base times** (34 events, ages 15-23 for non-50m, 18+ for 50m)
- **30,027 USA athletes** (reference data for MAP comparison)
- **221,321 USA period results** (2021-2025 rankings data)
- **24,928 USA delta records** (improvement tracking 15->16, 16->17, 17->18)
- **612 Canada On Track times** (Track 1/2/3 development benchmarks)
- **93.5% email coverage** (7,156 athletes have AcctEmail for registration contact)

---

## 2. Technical Architecture

### Stack
| Layer | Technology |
|-------|------------|
| Frontend | Next.js + React + TypeScript |
| Backend | FastAPI (Python) |
| Database | **Supabase (PostgreSQL)** - cloud hosted |
| Backup Database | SQLite (`malaysia_swimming.db` at project root) |
| Authentication | Password-based (MAS2025), no OAuth/JWT yet |
| Hosting (planned) | Vercel (registration portal), Exabytes (main WordPress site) |

### Infrastructure Overview
```
┌─────────────────────────────────────────────────────────────┐
│                     ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   malaysiaaquatics.org (Exabytes/WordPress) - Main site     │
│                                                              │
│   register.malaysiaaquatics.org (Vercel) - Registration     │
│           ↓                                                  │
│   analytics.malaysiaaquatics.org (Vercel) - Results/Stats   │
│           ↓                                                  │
│   Supabase (Database + API) - Shared by both apps           │
│           ↓                                                  │
│   RevenueMonster (Payments - planned)                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Vercel Deployment Configuration (Configured Dec 2025)

| Vercel Project | GitHub Repo | Root Directory | Live URL |
|----------------|-------------|----------------|----------|
| `mas-registration` | malaysia-swimming-analytics | `registration-portal` | register.malaysiaaquatics.org |
| `mas-analytics` | malaysia-swimming-analytics | (root) | analytics.malaysiaaquatics.org |

**Environment Variables (set in Vercel dashboard):**
- `NEXT_PUBLIC_SUPABASE_URL` = `https://bvmqstoeahseklvmvdlx.supabase.co`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` = `sb_publishable_-0n963Zy08gBMJPMse2V8A_xAyHgKZM`

### DNS Configuration (Exabytes)

**CNAME Records to add at Exabytes DNS for malaysiaaquatics.org:**

| Type | Name | Value | Purpose |
|------|------|-------|---------|
| CNAME | `register` | `703340cc0a6babe6.vercel-dns-017.com` | Registration portal |
| CNAME | `analytics` | `578dca52ee593a72.vercel-dns-017.com` | Analytics dashboard |

**DNS Propagation:** After adding records, allow 5-30 minutes for propagation. Vercel will show green checkmark when complete.

### Key Directories
```
project root/
  .env                     <- Credentials (DO NOT commit to git!)
  malaysia_swimming.db     <- Local SQLite backup
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
    supabase_migration.sql <- Database schema for Supabase
    import_to_supabase_api.py <- Data import script
  data/
    supabase_export/       <- CSV exports for Supabase import
  docs/
    2026_Registration_Strategy.md <- Registration system plan
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
| `athletes` | Malaysian registered swimmers | id, fullname, BIRTHDATE, Gender, nation, club_name, state_code, role, sport, msn_program |
| `foreign_athletes` | Non-Malaysian competitors | id, fullname, birthdate, gender, nation, club_name |
| `results` | Competition times | athlete_id, foreign_athlete_id, event_id, meet_id, time_seconds, aqua_points |
| `events` | Event catalog (LCM/SCM) | event_id, course, stroke, distance, gender |
| `meets` | Meet metadata | id, meet_type, meet_alias, meet_date, meet_year |
| `clubs` | Club registry | club_code, club_name, state_code, club_email, club_admin_name |
| `coaches` | Coaching staff | id, coach_name, birthdate, gender, nation, club_name, coach_role, state_code, msn_program |

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

### Phase 17: Athlete Panel UI & Data Cleanup (Dec 1, 2025)
- Athlete panel field enhancements:
  - Field data now shows as grey text inside input boxes (removed separate spans)
  - API call to fetch full athlete details on selection
  - Loading indicator while fetching
  - Clubs dropdown properly maps API response
  - "Update All Changes" button to save all modified fields at once
- IC Number field restructured to 5 boxes:
  - YY dropdown (00-99), MM dropdown (01-12), DD dropdown (dynamic 01-31)
  - PB dropdown (00-99) for place of birth code
  - Last 4+ digits input
  - Passport detection: shows "(Passport?)" for passport-like values
- Phone number fields with country code dropdown:
  - 28 country codes (MY, SG, US/CA, UK, AU, CN, KR, JP, etc.)
  - Malaysian numbers auto-formatted: XX XXX XXXX (9 digits) or XX XXXX XXXX (10 digits)
- Email validation: must contain @ and . with @ before last .
- Address section restructured:
  - Street, Line 2, City, Postal code (5 digits), State dropdown, Country dropdown
  - Added `postal_code` column to athletes table
- Passport/IC data migration:
  - Script: `scripts/migrate_ic_to_passport.py`
  - Migrated 208 athletes: passport numbers moved from IC to passport_number field
  - Nation detection from passport format (CHN, KOR, JPN, USA, AUS, SGP, etc.)
  - Updated 195 athletes with detected nation
- IC/Nation data cleanup:
  - Fixed 2 malformed ICs (transposed dates)
  - Cleaned 9 garbage IC values (postcodes)
  - Set all remaining athletes without nation to MAS
  - Final: 4,078 MAS + 201 foreign athletes, 0 without nation
- API fixes:
  - Added lowercase aliases to AthleteUpdateRequest (nation, club_code, club_name, state_code)
  - Added postal_code to model and field_name_map
  - State, club, nation fields now save correctly

### Phase 18: Supabase Migration & 2026 Registration Prep (Dec 1, 2025)

**What is Supabase?**
Supabase is a cloud-hosted PostgreSQL database with built-in REST API. It replaces our local SQLite database, allowing:
- Access from anywhere (not just the local computer)
- Multiple applications can share the same database (analytics + registration)
- Automatic backups and scaling
- No need to manage database servers

**Registration Data Preparation:**
- Audited contact data coverage:
  - Before: Only 76 athletes (1.9%) had email addresses
  - 29% of athletes had no contact information at all
- Loaded registration export `customexport (9).xlsx`:
  - Added new `AcctEmail` column to athletes table (parent/guardian email)
  - 3,777 existing athletes updated with AcctEmail
  - 3,393 new athletes inserted with full registration data
  - Total athletes increased from 4,279 to 7,650
- Merged 22 duplicate athlete pairs:
  - Duplicates occurred when same athlete existed in SwimRankings AND registration
  - Kept record with results, copied missing fields (email, IC, address, guardian info)
  - 52 total fields merged across 22 athletes
- Final result: **93.5% email coverage** (7,156 of 7,650 athletes have AcctEmail)

**Supabase Setup:**
- Created Supabase account at supabase.com
- Project name: MalaysiaAquatics
- Region: Singapore (closest to Malaysia)
- Created full database schema with 22 tables:
  - Schema file: `scripts/supabase_migration.sql`
  - Standardized column names to snake_case (PostgreSQL convention)
  - Added `registrations_2026` table for tracking registration status
- Exported all SQLite data to CSV files (18 tables)
  - Export location: `data/supabase_export/`
- Imported all data via Supabase REST API:
  - Import script: `scripts/import_to_supabase_api.py`
  - **341,054 total rows imported successfully**
  - Only `records` table (75 rows) failed due to foreign key constraint

**2026 Registration Strategy:**
- Created comprehensive strategy document: `docs/2026_Registration_Strategy.md`
- Recommended approach: Email personalized registration links to parents
- Email grouping analysis:
  - 4,527 unique AcctEmail addresses covering 7,156 athletes
  - 3,206 emails → 1 athlete (individual families)
  - 1,057 emails → 2 athletes (siblings)
  - Remaining emails → 3+ athletes (some are club emails)
- Implementation phases planned:
  1. Primary: Email campaign to 4,527 unique emails
  2. Secondary: Phone/SMS for athletes without email
  3. Catch-all: Public portal for new registrations

**Credentials Management:**
- Created `.env` file with all credentials (Supabase URL, API keys, passwords)
- File NOT committed to git (contains sensitive data)
- Credentials documented in `.env` with comments explaining each

**What's Next:**
- ~~Create Vercel account for hosting~~ (Done - Session 25)
- Build registration portal frontend (Next.js)
- Build analytics app frontend (migrate existing Next.js app)
- Deploy both apps to Vercel
- Configure subdomains in Exabytes DNS:
  - register.malaysiaaquatics.org
  - analytics.malaysiaaquatics.org
- Set up email sending (Gmail batched or SendGrid)
- Research RevenueMonster payment API

### Phase 19: Games Info Data & Coach Management (Dec 2, 2025)

**Games Info Excel Load:**
- Loaded `Additional Games Info (Passport,School, Sizes) (2).xlsx` from national team data collection
- 216 athletes updated via Supabase REST API:
  - Passport numbers for travel verification
  - School/university information
  - Medical conditions and dietary restrictions
  - Shirt and shoe sizes for team uniforms
  - Supporter information (family attending)
  - Acceptance intention (YES = confirmed for team)
- Name matching used word-based algorithm (2+ common words = match)
- 8 wrong matches identified and manually corrected

**New Database Columns:**
- Athletes table: role, sport, msn_program, medical_conditions, dietary_restrictions, supporters_info, acceptance_intention
- Coaches table: msn_program, birthdate, gender, nation, state_code
- SQL added via Supabase Dashboard (ALTER TABLE statements)

**Coaches Table Populated:**
| ID | Name | Role | Club | State | Program |
|----|------|------|------|-------|---------|
| 1 | Magnus Hoejby Andersen | Head Coach | NTC | - | Pelapis |
| 2 | Clara Chung Lai Sze | State Coach | - | PRK | - |
| 3 | Mark Chua Yu Foong | State Coach | PADE | SEL | - |
| 4 | Albert Yeap Jin Teik | State Coach | WAHOO | PEN | - |

**State Coach Tracking:**
- Added `state_code` column (TEXT) to coaches table
- State coaches have their state stored (PRK, SEL, PEN, etc.)
- Head coaches have NULL state_code (national level)
- Column `state_coach` uses integer (1 = yes) for compatibility

**Duplicate Athletes Resolved:**
- Jia Jia (TAN SHER LI): ID 3471 kept (had results), 7511 deleted, 14 fields merged
- Nishan (KESAVAN): ID 3376 kept (had results), 6072 deleted, 16 fields merged
- Deven (KESAVAN): ID 3374 kept (had results), 4707 deleted, 11 fields merged
- Merge strategy: keep record linked to results, copy AcctEmail/IC/address/guardian from duplicate

**Wrong Match Manual Corrections:**
| Excel Name | Correct ID | Note |
|------------|------------|------|
| Ho Wei Yan | 1771 | Word match found wrong athlete |
| Bryan Leong | 2102 | Added alias "Bryan Leong Xin Ren", DOB corrected |
| Elson Lee | 940 | |
| Isabelle Kam | 3042 | |
| Andrew Goh | 2534 | |
| Sophocles Ng | 2372 | |

**Scripts Created:**
- `scripts/match_games_info.py` - Name matching and DOB verification
- `scripts/load_games_info.py` - Data loading to Supabase
- `scripts/fix_wrong_matches.py` - Manual corrections for 6 athletes + 2 coaches
- `scripts/supabase_add_columns.sql` - SQL for new columns

### Phase 20: Backend Migration to Supabase (Planned)

**Problem:** Backend reads from local SQLite while data lives in Supabase cloud. Causes sync issues.

**Solution:** Migrate backend to use Supabase REST API directly.

**Tasks:**
1. Add Supabase Python client to backend
2. Create `get_supabase_client()` helper in `src/web/main.py`
3. Replace `get_database_connection()` calls with Supabase API
4. Start with coaches (proof of concept), then athletes, results, etc.
5. Keep SQLite as offline backup

### Phase 21: MOT Enhancements & Printable PDF (Dec 3, 2025)

**MOT Base Times - Age 23 Fix:**
- Discovered `mot_base_times` table had no age 23 records (showing 00:00.00)
- Root cause: Table was created without age 23 rows
- Fix: Ran `create_mot_base_times.py` then `populate_mot_base_times.py`
- Result: 42 age 23 records now populated (34 with calculated times)

**MOT Landing Page Enhancements:**
- Added "Malaysia On Track (MOT) Methodology" header at page top
- Added overview paragraph explaining MOT methodology:
  - Adapted from Swimming Canada's proven On Track Times system
  - Two data sources: USA Swimming median deltas (ages 15-18) + Canada On Track three-track system (ages 18+)
  - How MOT creates single unified development pathway
- Professional styling: grey background with red left border
- Added clickable link box to printable PDF

**MOT Printable PDF:**
- Created `/mot/MOT_On_Track_Times_2025.html` - 2-page landscape document
- Each gender page includes:
  - MAS logo in header
  - Two sections: "FREESTYLE & BACKSTROKE" (9 events) + "BREASTSTROKE, BUTTERFLY & IM" (8 events)
  - Ages 15-23 with grey cells for 50m events at ages 15-17
  - Data source footer
- **Dynamic generation from database:**
  - Script: `scripts/generate_mot_pdf.py`
  - Run after updating podium times: `python scripts/generate_mot_pdf.py`
  - Reads directly from `mot_base_times` table
  - No more hardcoded times

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
| `MOT_methodology.md` | MOT calculation methodology (data sources, formulas) |
| `docs/Supabase_Guide.md` | How to use Supabase (cloud database) |
| `docs/2026_Registration_Strategy.md` | Registration system implementation plan |
| `scripts/generate_mot_pdf.py` | Regenerate MOT printable PDF from database |
| `.env` | Credentials file (DO NOT commit to git!) |
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
| Only 1.9% email coverage | Loaded registration data, added AcctEmail | **93.5% email coverage** |
| Local-only database | Migrated to Supabase (cloud PostgreSQL) | Accessible from anywhere |

---

## 10. Future Features (Planned)

### Coach Certification Tracking
Track coach certifications, renewals, and continuing education. Requirements documented for future implementation:

**Certification Types:**
- **Safety Certifications** (with renewal reminders):
  - CPR certification (expiry date, renewal alerts)
  - Athlete Protection certification
  - International Games certifications
- **Sport-Specific Levels** (1, 2, 3):
  - Registration date
  - Theory test completion date
  - Log book completion date
  - Time limits: L1 = 6 months (12-week log book), L2 = 9 months (6-month log book), L3 = TBD
  - Status: Registered / Theory Passed / Log Book Complete / Certified
- **ISN Certification** (International Swimming Network)
- **Continuing Education**:
  - Course name, date attended, hours
  - Provider/organization
  - Certificate upload (future)

**Database Tables Needed:**
```sql
coach_certifications (
    id, coach_id, cert_type, cert_name,
    issued_date, expiry_date, status,
    theory_passed_date, logbook_completed_date,
    notes
)

coach_cpd (
    id, coach_id, course_name, provider,
    date_attended, hours, certificate_url
)
```

**Alerts/Reminders:**
- CPR expiring within 30/60/90 days
- Athlete Protection renewal due
- Log book deadline approaching

*Status: Documented for future implementation. Not started.*

---

### National Team Selection Panel
A timeline-driven admin panel for managing national team selections. The system ensures consistent processes regardless of who's leading, with the board approving final outputs rather than being involved in workflow details.

**Core Philosophy:**
- Enter key dates → System generates task timeline with deadlines
- Check off tasks as completed → Track progress visually
- Generate reports confirming completion → Board approves final output
- Swimmers and coaches have secure, consistent management support

**Timeline-Driven Workflow:**
1. **Create Selection** - Enter key dates:
   - Competition date (e.g., SEA Games Dec 15, 2025)
   - Short List due date (final team submission deadline)
   - Long List due date (initial selection deadline)
   - System auto-generates all task deadlines working backwards

2. **Selection Phase** - Choose athletes based on:
   - Time standards / AQUA points threshold
   - Qualifying times per event
   - Rankings within selection criteria

3. **Long List Phase** - Collect all required information:
   - Passport expiration dates (must be valid 6+ months beyond competition)
   - Uniform/equipment sizes (suit, jacket, shoes, etc.)
   - School information (for age-group athletes)
   - Travel documents
   - Medical/dietary requirements
   - Tasks auto-prompted based on timeline

4. **Short List Phase** - Finalize team:
   - Payment confirmation (team fees, travel costs)
   - Participation confirmation from athlete/parent
   - All documents collected and verified
   - Final roster locked

5. **Completion Reports** - Generate for board approval:
   - All tasks completed checklist
   - Payment summary
   - Document verification status
   - Final roster with all data

**Key Features:**
- Timeline visualization with task deadlines
- Automatic reminders/prompts for upcoming tasks
- Passport expiry alerts (flag if expires within 6 months of competition)
- Progress tracking dashboard (X of Y tasks complete)
- Report generation for board review
- Email notifications to selected athletes/parents

**Data Storage:**
```sql
team_selections (
    id, competition_name, competition_date,
    long_list_due, short_list_due,
    status, created_at, created_by
)

selection_tasks (
    id, selection_id, task_name, due_date,
    completed_at, completed_by, notes
)

selection_athletes (
    id, selection_id, athlete_id,
    list_status,  -- 'long_list', 'short_list', 'removed'
    passport_verified, passport_expiry,
    sizes_collected, payment_status, confirmed,
    notes
)
```

*Status: Documented for future implementation. Not started.*

---

## 11. Contact & Governance

- Database changes require validation against CLAUDE.md protocols
- All date fields must use ISO 8601 format: `YYYY-MM-DDTHH:MM:SSZ`
- No Unicode characters in Python code (Windows cp1252 encoding)
- Use global utilities - never recreate matching/detection logic

---
