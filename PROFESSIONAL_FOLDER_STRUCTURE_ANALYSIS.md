# Professional Folder Structure Analysis & Recommendations

> **Update (November 2025):**
> - Handoff docs refreshed — read `SESSION_START.md`, `Malaysia Swimming Analytics Handbook.md`, and `WHAT_S_NEXT.md` before making changes.
> - Athlete data now consolidates via `temp_scripts/rebuild_consolidated_athletes.py` → `data/manual_matching/consolidated_athlete_ID_rebuilt.xlsx`.
> - Alias management lives in the new `athlete_aliases` table (seed with `temp_scripts/setup_athlete_aliases.py`).

## Malaysia Swimming Analytics - National System Architecture

---

## Executive Summary

This document provides professional data management recommendations for restructuring the Malaysia Swimming Analytics project to support:
- **National-scale operations** (entire country's swimming data)
- **Long-term sustainability** (beyond original developer)
- **Non-technical user navigation** (board members, administrators, staff)
- **Multi-project scalability** (current + future Malaysia Aquatics projects)

**Key Recommendation**: Implement a **hybrid architecture** using SQL databases for operational data and CSV files as user-friendly exports, with clear separation between production systems and analytical projects.

---

## Critical Design Decisions Analysis

### 1. Reference Data: SQL Database vs. CSV Files?

#### ✅ **RECOMMENDATION: SQL Database as Primary + CSV as Export**

**Professional Justification:**

1. **Data Integrity**
   - SQL enforces referential integrity (e.g., event names must match canonical list)
   - Constraints prevent invalid data entry (e.g., negative times, invalid ages)
   - Primary keys prevent duplicate entries
   - Foreign keys maintain relationships between tables

2. **Query Performance**
   - Indexed lookups are 100-1000x faster than CSV file scanning
   - JOIN operations are efficient (e.g., joining results with MAP/MOT/AQUA targets)
   - Aggregations and filtering are optimized by the query engine

3. **Concurrent Access**
   - Multiple users can query simultaneously without file locking
   - Web application can serve hundreds of requests per second
   - Background processes can update data while users query

4. **Transaction Management**
   - Updates can be rolled back if errors occur
   - Ensures data consistency during bulk updates

5. **Scalability**
   - Databases handle millions of rows efficiently
   - Can partition data by year/meet for optimal performance
   - Supports future API integrations (e.g., automatic World Aquatics updates)

6. **Audit Trail**
   - SQL databases can log all changes (who, when, what)
   - Essential for national system compliance

**CSV Files Role:**
- **Export format** for non-technical users (Excel-compatible)
- **Backup format** for disaster recovery
- **Import format** for bulk updates from external sources (e.g., World Aquatics)
- **Documentation** (human-readable reference for board members)

**Implementation Strategy:**
```
reference_data/
├── database/
│   └── reference.db (SQLite) or reference schema (PostgreSQL)
│       ├── map_times (gender, event, age, time_seconds, time_text, base_points)
│       ├── mot_times (gender, event, age, track, time_seconds, time_text)
│       ├── aqua_base_times (gender, event, time_seconds, time_text)
│       └── sea_games_times (gender, event, medal_type, time_seconds, time_text)
├── exports/  (auto-generated from database)
│   ├── MAP_Times.csv
│   ├── MOT_Times.csv
│   ├── AQUA_Base_Times.csv
│   └── SEA_Games_Times.csv
└── imports/  (upload folder for new reference data)
    └── [new files to be loaded into database]
```

**For Non-Technical Users:**
- Provide a simple "Export to Excel" button in admin interface
- Documentation: "Reference times are stored in a database, but you can export them to Excel anytime"
- Visual guide showing how to view/update reference data via web interface

---

### 2. Times Database Project Clarification

#### ✅ **CONFIRMED: This is the MAIN PROJECT (React + FastAPI Web Application)**

**Current Status:**
- Frontend: React/Next.js (src/frontend/)
- Backend: FastAPI (src/web/)
- Database: SQLite (database/malaysia_swimming.db) → migrating to PostgreSQL
- Purpose: Public-facing web application for meet results, filtering, ranking by MAP/MOT/AQUA points

**Project Components:**
- Meet results upload (admin interface)
- Public results viewing with filters (gender, age, event, meet, state)
- Ranking calculations (MAP, MOT, AQUA points)
- Athlete profiles and performance tracking
- Reference data queries (looks up to parent reference_data/)

**Folder Location:** `times_database/` (contains all web application code)

---

### 3. Meet Data Location

#### ✅ **RECOMMENDATION: Shared Parent-Level Location**

**Justification:**
- **Times Database** needs meet data for:
  - Uploading new meet results via admin interface
  - Displaying meet results on public website
  - Calculating MAP/MOT/AQUA points for results

- **Meet Reports** needs meet data for:
  - Generating post-meet reports
  - Analyzing meet statistics
  - Creating performance summaries

**Structure:**
```
meets/
├── active/          # Current season meets (available to both projects)
│   ├── 2024-25/
│   │   ├── SUKMA_2024_Men.xls
│   │   ├── MO_2025_Men.xls
│   │   └── ...
│   └── 2023-24/
├── archive/         # Historical meets (reference only)
│   └── [organized by year]
└── uploads/         # Temporary folder for new meet uploads (Times Database admin)
```

**Access Pattern:**
- Times Database admin uploads → saves to `meets/active/YYYY-YY/`
- Both projects read from `meets/active/` (via scripts or direct file access)
- Archive old meets annually to `meets/archive/`

---

### 4. Statistical Analysis: USA/Canada Data

#### ✅ **RECOMMENDATION: SQL Database for Analytical Data**

**Justification:**
- **USA Age Deltas**: 84 statistical analyses (computed deltas between age transitions)
- **Canada On Track**: 504 reference times (Track 1/2/3 across ages)
- **Future Analysis**: Will need to query and join these datasets frequently
- **Performance**: SQL enables complex analytical queries (e.g., "Compare USA median deltas to Canada Track 2 deltas by event")

**Current Status:**
- Already implemented: SQLite database with `canada_on_track` and `usa_age_deltas` tables
- Location: `database/malaysia_swimming.db` (shared database, or separate statistical database)

**Recommendation:**
- Keep in SQLite for statistical analysis project (read-heavy, single-user analytical queries)
- CSV exports remain for documentation and backup
- Separate from main web application database (different use case, different update frequency)

**Structure:**
```
statistical_analysis/
├── database/
│   └── statistical.db (SQLite)
│       ├── canada_on_track
│       ├── usa_age_deltas
│       ├── usa_age_results (planned)
│       └── events (canonical event list)
├── data/
│   ├── Period Data/  (source files)
│   └── Delta Data/   (analysis results)
└── scripts/
    ├── load_canada_tracks.py
    ├── load_usa_deltas.py
    └── compare_deltas_canada.py
```

---

## Recommended Folder Structure (Final)

### Architecture Principles

1. **Separation of Concerns**: Each project is self-contained
2. **Shared Resources at Parent**: Reference data, meet data accessible to all
3. **Database-First**: SQL for operational data, CSV for exports/backups
4. **Scalability**: Easy to add new projects (Athlete Registration, Performance Tracking, etc.)
5. **Documentation Hierarchy**: Clear guides for non-technical users

### Proposed Structure

```
Malaysia Swimming Analytics/
│
├── 📊 reference_data/                    # SHARED: Lookup tables (all projects)
│   ├── database/
│   │   └── reference.db (SQLite)        # Primary storage (MAP, MOT, AQUA, SEA Games)
│   ├── exports/                         # Auto-generated CSV exports (for Excel users)
│   │   ├── MAP_Times.csv
│   │   ├── MOT_Times.csv
│   │   ├── AQUA_Base_Times.csv
│   │   └── SEA_Games_Times.csv
│   ├── imports/                         # Upload folder (new reference data)
│   └── README.md                        # "How to update reference data" guide
│
├── 📁 meets/                            # SHARED: Competition data (all projects)
│   ├── active/                          # Current season meets
│   │   ├── 2024-25/
│   │   │   ├── SUKMA_2024_Men.xls
│   │   │   ├── MO_2025_Men.xls
│   │   │   └── ...
│   │   └── 2023-24/
│   ├── archive/                         # Historical meets (by year)
│   └── uploads/                         # Temporary (Times Database admin uploads)
│
├── 📈 statistical_analysis/             # PROJECT: MOT Delta Analysis
│   ├── database/
│   │   └── statistical.db (SQLite)     # USA/Canada analytical data
│   ├── data/
│   │   ├── Period Data/                 # Source data (2,240 files)
│   │   └── Delta Data/                  # Analysis results (84 folders)
│   ├── reports/                         # Generated reports
│   │   ├── Delta_Comparison_USA_vs_Canada.html
│   │   └── MOT_Delta_Index.html
│   ├── scripts/                         # Production scripts
│   │   ├── run_mot_delta_analysis.py
│   │   ├── load_canada_tracks.py
│   │   ├── load_usa_deltas.py
│   │   └── compare_deltas_canada.py
│   ├── temp/                            # Temporary test scripts (can delete)
│   ├── PhD/                             # Dissertation materials
│   ├── README.md                        # Project overview
│   └── USER_GUIDE.md                    # "How to run analysis" (non-technical)
│
├── 🌐 times_database/                   # PROJECT: Main web application
│   ├── database/
│   │   └── malaysia_swimming.db         # Main PostgreSQL (production)
│   ├── src/
│   │   ├── web/                         # FastAPI backend
│   │   │   ├── main.py
│   │   │   ├── routers/
│   │   │   └── services/
│   │   └── frontend/                    # React/Next.js frontend
│   │       ├── pages/
│   │       └── components/
│   ├── scripts/                         # Data migration/utility scripts
│   │   ├── convert_meets_to_sqlite.py
│   │   └── load_reference_data.py       # Loads from ../reference_data/database/
│   ├── docker-compose.yml               # Docker services
│   ├── README.md                        # Developer setup guide
│   └── USER_GUIDE.md                    # "How to upload meets" (non-technical)
│
├── 📋 meet_reports/                     # PROJECT: Meet Results Reporting
│   ├── data/
│   │   └── [temporary processing files]
│   ├── reports/                         # Generated reports
│   ├── templates/                       # Report templates
│   ├── scripts/                         # Production scripts
│   │   ├── generate_report.py           # Queries ../meets/active/
│   │   └── query_reference_data.py      # Queries ../reference_data/database/
│   ├── temp/                            # Temporary scripts
│   └── README.md                        # Project overview
│
├── 🧪 temp_scripts/                     # SHARED: Global temporary scripts
│   └── [session-specific test files]
│
├── 📚 docs/                             # SHARED: Global documentation
│   ├── MAP_Methodology.md
│   ├── MOT_Methodology.md
│   ├── AQUA_Methodology.md
│   └── README.md
│
├── 📖 Malaysia Swimming Analytics Handbook.md  # Main project guide
└── 📖 SESSION_START.md                  # Session startup guide
```

---

## Data Flow Architecture

### Reference Data Updates
```
1. Administrator uploads new reference data → reference_data/imports/
2. Script loads data → reference_data/database/reference.db (SQL)
3. Script exports → reference_data/exports/*.csv (for Excel users)
4. Both Times Database and Meet Reports query → reference_data/database/reference.db
```

### Meet Data Flow
```
1. Administrator uploads meet → meets/uploads/ (via Times Database admin interface)
2. Times Database processes → saves to meets/active/YYYY-YY/
3. Times Database stores results → times_database/database/malaysia_swimming.db
4. Meet Reports reads → meets/active/ (for report generation)
```

### Statistical Analysis Flow
```
1. Statistical Analysis runs → generates Delta Data/
2. Statistical Analysis loads → statistical_analysis/database/statistical.db
3. Comparison reports generated → statistical_analysis/reports/
4. Results may update → reference_data/database/reference.db (MOT times)
```

---

## Non-Technical User Documentation Strategy

### Documentation Hierarchy

1. **Quick Start Guides** (One page, visual)
   - `reference_data/README.md`: "How to update MAP/MOT/AQUA times"
   - `times_database/USER_GUIDE.md`: "How to upload a meet"
   - `statistical_analysis/USER_GUIDE.md`: "How to run delta analysis"

2. **Process Documentation** (Step-by-step)
   - Visual screenshots of each step
   - "If you see X error, do Y" troubleshooting
   - Example workflows (e.g., "Annual MOT Update Process")

3. **Reference Documentation** (When you need details)
   - Methodology docs (MAP_Methodology.md, etc.)
   - Database schema documentation
   - API documentation (for developers)

### Documentation Format for Non-Technical Users

**Example: `reference_data/README.md`**

```markdown
# Updating Reference Times

## What are Reference Times?
Reference times (MAP, MOT, AQUA) are the target times used to calculate points for swimmers.

## When to Update
- **MAP**: Annually (ages 13, 15, 17)
- **MOT**: Every 2 years (or after statistical analysis)
- **AQUA**: Annually (World Aquatics updates)

## How to Update (3 Steps)

### Step 1: Prepare Your Data
1. Open the Excel template: `reference_data/exports/MAP_Times_Update_Template.xlsx`
2. Fill in the new times
3. Save as: `reference_data/imports/MAP_Times_YYYY-MM-DD.xlsx`

### Step 2: Upload to Database
1. Open the Times Database admin page
2. Click "Update Reference Data" → "MAP Times"
3. Select your file from `reference_data/imports/`
4. Click "Upload"

### Step 3: Verify
1. Click "View Reference Data" → "MAP Times"
2. Check that your new times appear
3. Export to Excel to verify: `reference_data/exports/MAP_Times.csv`

## Need Help?
Contact: [Technical Support Contact]
```

---

## Implementation Plan

### Phase 1: Database Setup (Priority 1)
1. ✅ Create `reference_data/database/` structure
2. ✅ Design SQL schema for MAP/MOT/AQUA/SEA Games tables
3. ✅ Create load scripts for existing Excel files
4. ✅ Generate CSV exports for non-technical users
5. ✅ Test database queries from Times Database and Meet Reports scripts

### Phase 2: Folder Reorganization (Priority 2)
1. ✅ Create new folder structure
2. ✅ Move Statistical Analysis files to `statistical_analysis/`
3. ✅ Move Times Database files to `times_database/`
4. ✅ Move meet files to `meets/active/`
5. ✅ Move reference Excel files to `reference_data/imports/` (for loading)
6. ✅ Create `meet_reports/` folder structure (empty, ready for development)

### Phase 3: Script Updates (Priority 3)
1. ✅ Update all scripts to use new paths (`../reference_data/database/`, `../meets/active/`)
2. ✅ Update Times Database to query reference_data database
3. ✅ Update Meet Reports scripts to query reference_data database
4. ✅ Test all scripts with new structure

### Phase 4: Documentation (Priority 4)
1. ✅ Create user guides for non-technical users
2. ✅ Update technical documentation (handbook, session guides)
3. ✅ Create visual guides (screenshots, flowcharts)
4. ✅ Create "Annual Update Process" documentation

### Phase 5: Cleanup & Testing (Priority 5)
1. ✅ Move temporary scripts to `temp_scripts/` or project `temp/` folders
2. ✅ Archive old/unused files
3. ✅ Test complete workflow (upload meet → calculate points → generate report)
4. ✅ Verify all projects can access shared resources

---

## Database Schema Design (Reference Data)

### `reference_data/database/reference.db` (SQLite)

```sql
-- MAP Times (Malaysia Age Points)
CREATE TABLE map_times (
    gender TEXT NOT NULL CHECK (gender IN ('M', 'F')),
    event TEXT NOT NULL,
    age INTEGER NOT NULL CHECK (age BETWEEN 12 AND 18),
    time_seconds REAL NOT NULL,
    time_text TEXT NOT NULL,
    base_points INTEGER NOT NULL DEFAULT 1000,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (gender, event, age)
);

-- MOT Times (Malaysia On Track)
CREATE TABLE mot_times (
    gender TEXT NOT NULL CHECK (gender IN ('M', 'F')),
    event TEXT NOT NULL,
    age INTEGER NOT NULL CHECK (age BETWEEN 15 AND 23),
    time_seconds REAL NOT NULL,
    time_text TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (gender, event, age)
);

-- AQUA Base Times (World Aquatics)
CREATE TABLE aqua_base_times (
    gender TEXT NOT NULL CHECK (gender IN ('M', 'F')),
    event TEXT NOT NULL,
    time_seconds REAL NOT NULL,
    time_text TEXT NOT NULL,
    year INTEGER NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (gender, event, year)
);

-- SEA Games Medal Times
CREATE TABLE sea_games_times (
    gender TEXT NOT NULL CHECK (gender IN ('M', 'F')),
    event TEXT NOT NULL,
    medal_type TEXT NOT NULL CHECK (medal_type IN ('Gold', 'Silver', 'Bronze')),
    time_seconds REAL NOT NULL,
    time_text TEXT NOT NULL,
    year INTEGER NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (gender, event, medal_type, year)
);

-- Clubs to State Mapping
CREATE TABLE club_state_mapping (
    club_name TEXT NOT NULL,
    state_code TEXT NOT NULL,
    PRIMARY KEY (club_name)
);

-- Indexes for performance
CREATE INDEX idx_map_times_lookup ON map_times(gender, event, age);
CREATE INDEX idx_mot_times_lookup ON mot_times(gender, event, age);
CREATE INDEX idx_aqua_base_times_lookup ON aqua_base_times(gender, event);
```

---

## Long-Term Sustainability Considerations

### 1. **Version Control**
- Use Git for all code (scripts, web application)
- Commit messages explain what and why
- Tag releases (e.g., "MOT_Update_2025")

### 2. **Backup Strategy**
- Daily automated backups of all databases
- Weekly exports of reference data to CSV (human-readable backup)
- Version history for reference data updates (who, when, what changed)

### 3. **Access Control**
- Admin interface requires authentication
- Log all reference data updates (audit trail)
- Role-based access (admin, viewer, analyst)

### 4. **Maintenance Windows**
- Document when updates occur (e.g., "MOT updates: January of even years")
- Automated reminders for scheduled updates
- Clear rollback procedures if updates fail

### 5. **Knowledge Transfer**
- Comprehensive documentation (this document + user guides)
- Video tutorials for complex processes
- Handover checklist when transitioning developers
- Code comments explain "why" not just "what"

---

## Professional Assessment: Are You Thinking Like a Data Management Professional?

### ✅ **YES - You're on the Right Track**

**Strengths:**
1. ✅ Recognizing need for shared resources (reference data, meet data)
2. ✅ Separating analytical data from operational data
3. ✅ Planning for scalability (multiple projects)
4. ✅ Considering non-technical users (board members, staff)
5. ✅ Thinking about long-term sustainability

**Professional Recommendations (Additional Considerations):**

1. **Data Governance**
   - Define data ownership (who approves MAP/MOT updates?)
   - Establish update schedules (calendar of annual updates)
   - Create data quality checks (validate times before loading)

2. **Performance Optimization**
   - Index frequently queried columns (gender, event, age)
   - Partition large tables by year (if database grows)
   - Cache frequently accessed reference data in web application

3. **Disaster Recovery**
   - Automated daily backups
   - Off-site backup storage
   - Recovery testing (quarterly restore tests)

4. **Monitoring & Alerting**
   - Monitor database size growth
   - Alert on failed data loads
   - Track query performance (slow query log)

5. **Integration Readiness**
   - Design APIs for future integrations (e.g., automatic World Aquatics updates)
   - Standardize data formats (ISO date formats, canonical event names)
   - Document data exchange protocols

---

## Next Steps Summary

### Immediate Actions (This Session)
1. ✅ Review and approve this folder structure proposal
2. ✅ Begin Phase 1: Database setup for reference_data
3. ✅ Begin Phase 2: Folder reorganization

### Short-Term (Next 1-2 Sessions)
1. Complete folder reorganization
2. Update all script paths
3. Test database integration

### Medium-Term (Next Month)
1. Complete user documentation
2. Create admin interface for reference data updates
3. Test complete workflows with non-technical users

---

## Conclusion

Your approach demonstrates professional data management thinking. The recommended structure balances:
- **Technical efficiency** (SQL databases for operational data)
- **User accessibility** (CSV exports for non-technical users)
- **Scalability** (clear separation of projects, shared resources)
- **Long-term sustainability** (comprehensive documentation, clear processes)

This architecture will support Malaysia Aquatics for years to come, even after you're no longer the primary developer.




