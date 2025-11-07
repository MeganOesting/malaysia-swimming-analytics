# Malaysia Times Database Developer Handbook

**FOR AI ASSISTANTS: When starting a new session, IMMEDIATELY execute the "Streamlined Startup Protocol" (4 phases) without asking for permission. Do not ask "what would you like to do next" during startup.**

This document is a complete handoff for a fresh developer. With just this folder and this guide, you should be able to run, understand, and extend the project.

## Overview

One‑page Flask web app to analyze Malaysian swimming results:
- Compares meet results to AQUA targets (On Track Path Time, On Track AQUA, Track Gap)
- Computes Malaysia Age Points (MAP) from a base table
- Reads local Excel workbooks (no user uploads in the current UI)

Primary UI lives at `/` and renders a single page with filters, results table, and quick links to reference PDFs (MAP/MOT/LTAD).

## Tech Stack

- Python 3.9+ (tested on 3.13)
- Flask (server + templates)
- pandas (Excel IO and transforms)
- openpyxl (xlsx engine)
- xlrd==2.0.1 (xls engine)

## Repository Layout (top-level)

- `Malaysia_Times_Database/`
  - `Malaysia_Database.py` — App entry. Boots the On‑Track app at `/`.
  - `age_points_core.py` — MAP (Malaysia Age Points) computation from base table.
  - `age_points_blueprint.py` — Optional Age Points mini‑app UI (not mounted by default).
  - `Age_OnTrack_AQUA.xlsx` — Shared workbook:
    - Sheet `MOT Tables 25` — On Track Path Time targets
    - Sheet `AQUA POINTS` — AQUA base seconds (male/female)
  - `static/docs/` — Reference PDFs linked from the UI (MAP/MOT/LTAD)
  - `AthleteINFO.csv` — Optional overrides for athlete state codes
  - `Clubs_By_State.xlsx` — Club/state mapping
- `On_Track_Calculator/`
  - `On_Track_Code.py` — Core Flask app (routes, parsing, export, admin tools)
  - `templates/index.html` — Single page UI
  - `static/` — Images (logos)
- `Meets/` — Local Excel workbooks for meets (SUKMA, MIAG, MO, SEA Age, January State meets)
- `foreign_swimmers.txt` — One name per line; flags Non‑Malaysian swimmers in displays

Optional duplicate folder `On_Track_Calculator - Copy/` exists for experimentation; production uses `On_Track_Calculator/`.

## How to Run (Windows PowerShell)

From the project root (this folder):

1) Create and activate a virtual environment

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Install dependencies (pin xlrd to support .xls)

```powershell
python -m pip install --upgrade pip
pip install flask pandas openpyxl xlrd==2.0.1
```

3) Start the app

```powershell
python -m Malaysia_Times_Database.Malaysia_Database
```

You should see “Running on http://127.0.0.1:5000”. Open that URL in a browser.

If you prefer running the script directly:

```powershell
python "Malaysia_Times_Database\Malaysia_Database.py"
```

## Data Files the App Uses

- Shared workbook: `Malaysia_Times_Database/Age_OnTrack_AQUA.xlsx`
  - `MOT Tables 25` — Target times; columns A/B/C/M used (Gender, Event, Age, Target Time)
  - `AQUA POINTS` — Row 1 headers; Row 2 male base seconds; Row 3 female base seconds
- Meets: `Meets/`
  - `SUKMA_2024_Men.xls`, `SUKMA_2024_Women.xls`
  - `MIAG_2025_Men.xls`, `MIAG_2025_Women.xls`
  - `MO_2025_Men.xls`, `MO_2025_Women.xls`
  - `SEAG_2025_ALL.xlsx`
  - `January2024StateMeetsMen.xls`, `January2024StateMeetsWomen.xls`
- Reference docs: `Malaysia_Times_Database/static/docs/*.pdf` (auto‑linked by filename keywords)
- Optional mapping data:
  - `Malaysia_Times_Database/Clubs_By_State.xlsx`
  - `Malaysia_Times_Database/AthleteINFO.csv`
  - `foreign_swimmers.txt` in the project root

## App Entry and Routing

- Entry: `Malaysia_Times_Database/Malaysia_Database.py`
  - Imports and runs the On‑Track Flask app from `On_Track_Calculator/On_Track_Code.py` at root (`/`).
  - Host: `127.0.0.1`, Port: `5000`, `debug=True` for development.

- Core app: `On_Track_Calculator/On_Track_Code.py`
  - `GET /` — Render filters + table. On first load, warms caches in the background.
  - `POST /` — Apply filters (Meets, Gender, Events, State, Age Groups, Results mode, Include Foreign) and render results.
  - `POST /export` — Export current rows to `On_Track_Results.xlsx` (download).
  - Admin/diagnostics:
    - `GET /admin/reload-athleteinfo` — Soft-reload `AthleteINFO.csv`
    - `GET /admin/reload-clubs` — Reload `Clubs_By_State.xlsx`
    - `GET /admin/flush-cache` — Clear cached meet rows and LRU maps (AQUA/MOT)
    - `GET /admin/debug-q-scan` — Inspect Team/State (Q column) mapping issues for a workbook
    - `GET /admin/debug-club?name=...` — Inspect club/state mapping for a string
    - `GET /admin/debug-resolve?name=FILENAME` — Show resolved meet path
    - `GET /admin/reload-foreign` — Clear cached foreign names
    - `GET /admin/reload-sukma` — Rebuild SUKMA team lookup

## Data Flow (high‑level)

1) User selects meets, genders, events, state, age groups, and results mode.
2) For each selected meet workbook, pre‑parsed rows are pulled from cache (or parsed on first use).
3) For each row, the app enriches with:
   - On Track Path Time from `MOT Tables 25`
   - On Track AQUA from AQUA base + target time
   - Track Gap = AQUA − On Track AQUA
   - MAP Age Points (via `age_points_core.compute_age_points`) appended as last column
4) The table is rendered with fixed widths and client‑side sorting UI.
5) Export uses the same row building logic and writes `On_Track_Results.xlsx`.

## Parsing Notes (meets)

- Detect valid sheets and skip non‑result tabs (e.g., lap/top results/relays).
- Expected columns when `header=None`:
  - B (1): Gender; C (2): Distance; D (3): Stroke;
  - E (4): Name; F (5): Birthdate; G (6): Age;
  - I (8): Time; K (10): AQUA; M (12): Place; Q (16): Team/State; N (13): Meet date.
- Age is computed as of Dec 31 of meet year if not present in G.
- `foreign_swimmers.txt` flags names; UI annotates as “(Non‑Malaysian)”.
- Team/State resolution uses `Clubs_By_State.xlsx`, athlete overrides, and SUKMA cross‑lookups; see admin routes for debugging.

## Filters (UI)

- Meets: multi‑select
- Gender: M/F (multi‑select)
- Events: grid across Free/Back/Breast/Fly/IM
- State: optional 3‑letter code
- Age Groups: OPEN, 16‑18, 14‑15, 12‑13, 13U (mutual exclusivity rules enforced client‑side)
- Results Mode: all vs best (best reduces to best time per Gender/Event/Name)
- Include Non‑Malaysian Swimmers: toggle on/off

## Installation and Fresh Start Checklist

1) Ensure local Excel files exist in the expected places (see “Data Files”).
2) Python 3.9+ installed; create/activate venv.
3) Install: `flask pandas openpyxl xlrd==2.0.1`.
4) Run: `python -m Malaysia_Times_Database.Malaysia_Database`.
5) Open `http://127.0.0.1:5000`.

### First-time startup and cache warmup
- On the very first GET to `/`, the app warms several caches in the background (clubs map, athlete overrides, SUKMA lookups). This can take a few seconds.
- Before analyzing, either:
  - Wait ~3–5 seconds after the first page load, then apply filters, or
  - Click the small “reload” link next to the buttons (or call `/admin/reload-clubs`) to force-load `Clubs_By_State.xlsx` synchronously.
- If the State column shows blanks for known clubs on your first attempt, reload the page or use `/admin/reload-clubs` and try again.

### Developer environment quick-start (copy/paste)
```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install flask pandas openpyxl xlrd==2.0.1
python -m Malaysia_Times_Database.Malaysia_Database
```

Optional tools for profiling and debugging:
```powershell
pip install pyinstrument
```

### Quick verification steps
- Verify `.xls` support: `xlrd` must be 2.0.1 (run `python -c "import xlrd,sys; print(xlrd.__version__)"`).
- Visit `/admin/debug-resolve?name=January2024StateMeetsMen.xls` → `exists: True`.
- Visit `/admin/reload-clubs` → clubs map loaded; then apply meets/filters.

## Troubleshooting

- “ModuleNotFoundError: No module named 'Malaysia_Times_Database'”
  - Run from the project root and/or use module form: `python -m Malaysia_Times_Database.Malaysia_Database`.
- “This site can’t be reached / refused to connect”
  - Ensure the server printed “Running on http://127.0.0.1:5000”. Verify venv is active and port 5000 is free.
- Missing meets/AQUA files
  - UI will list missing paths at the top; populate the `Meets/` and `Malaysia_Times_Database/` workbooks accordingly.
- `.xls` files not readable
  - Ensure `xlrd==2.0.1` is installed. Newer xlrd removed xlsx support; we use openpyxl for xlsx.
- Wrong team/state mapping
  - Use `/admin/debug-q-scan` with `show_all=1` and `/admin/debug-club?name=...` to inspect mappings. Reload maps via `/admin/reload-clubs`.

## Performance and Maintainability

Current strengths:
- Caching of parsed meet rows and AQUA/MOT tables (LRU caches)
- Deferred/warm‑in‑background data loading to make first render responsive

Opportunities:
- Unify row‑building logic shared between index and export to a single helper (DRY); reduce code duplication.
- Persist a manifest of meets and precomputed per‑sheet metadata to avoid repeatedly scanning large workbooks.
- Consider pre‑parsing meets into compact CSV/Parquet for faster startup; load via pandas in milliseconds.
- Move state/team resolution to a dedicated module; pre‑index clubs and aliases in memory.
- Vectorize repeated lookups (e.g., AQUA base and MOT target) with dictionary maps and avoid per‑row try/except cost.
- Add profiling (e.g., `cProfile` or `pyinstrument`) to measure Excel IO vs. transform time; cache hot paths.
- Add pagination or virtualized table rendering for very large result sets.

## Extensibility

- Add a second page for Age Points UI by mounting `age_points_blueprint` at `/age-points` from `Malaysia_Database.py`.
- Add auto‑discovery of meets (scan `Meets/` and build `AVAILABLE_MEETS` dynamically with overrides).
- Embed PDF viewer modals for MAP/MOT/LTAD instead of linking to new tabs.
- Persist filter state in the URL (query string) to support shareable deep links.
- Add column show/hide toggles for mobile views.

## Future Feature Development

### MAP Button Enhancement
- **Current State**: Disabled reference button
- **Future Functionality**: 
  - Provide information on what MAP (Malaysia Age Points) is
  - Enable cluster calculations for selected athletes
  - Show MAP scoring methodology and calculations

### MOT Button Enhancement  
- **Current State**: Disabled reference button
- **Future Functionality**:
  - Provide information on what MOT (Malaysia On Track) points are
  - Generate MOT curves for selected athletes
  - Show target time progression and tracking

### Implementation Notes
- These buttons are currently disabled (`aria-disabled="true"`) in the UI
- Will require backend route development for MAP/MOT calculations
- Need to integrate with existing age points and target time systems

## Code Map (jump points)

- Entry/bootstrapping: `Malaysia_Times_Database/Malaysia_Database.py`
- Core app/routes: `On_Track_Calculator/On_Track_Code.py`
- UI template: `On_Track_Calculator/templates/index.html`
- Age Points: `Malaysia_Times_Database/age_points_core.py`
- Admin tooling: see routes under `On_Track_Code.py` (admin/*)

## Security and Environment

- App runs with Flask debug server for development; do not expose publicly.
- No file uploads; reads only local, curated workbooks.
- Windows‑first workflow; Linux/Mac should work with equivalent venv activation.

## Hand‑off Expectations

With this folder and this document, a new developer should be able to:
1) Create a venv, install dependencies, and start the app
2) Populate/adjust data files and verify parsing via admin tools
3) Analyze speed/efficiency and refactor duplicated logic
4) Extend UI/filters/export behavior and add new meets

For deeper context, also review:
- `Malaysia_Times_Database_README.md` (product README)
- `Malaysia_Times_Database_DEVELOPER.md` (developer guide)

## State Mapping Policy (current)

Order of resolution for the State column:
1) `Clubs_By_State.xlsx` exact/normalized mapping of the raw Q team name
2) If Q is a 3‑letter non‑MY code, pass it through
3) `AthleteINFO.csv` by normalized athlete name (state_code field)
4) Otherwise set to `UN` (Unassigned)

Note: SUKMA lookup is no longer used.

## Foreign Detection Policy (current)

- Authority: `AthleteINFO.csv` provides `foreign` (Y/N) per athlete.
- Behavior:
  - If `foreign=Y`, the app marks the swimmer as Non‑Malaysian and skips club‑to‑state mapping; state remains blank (or a nation code if added later).
  - The legacy `foreign_swimmers.txt` list is deprecated and ignored.
- Reload during sessions:
  - Reload AthleteINFO: [http://127.0.0.1:5000/admin/reload-athleteinfo](http://127.0.0.1:5000/admin/reload-athleteinfo)


## Working Session Protocol (for sessions with the AI assistant)

**CRITICAL: When starting a new session with the AI assistant, the assistant should IMMEDIATELY execute the startup commands without asking for permission. The assistant should follow the "Complete Fresh Session Startup Protocol" section below automatically.**

These steps are specific to interactive coding sessions with the assistant and are not required for normal usage.

1) Command execution
- The assistant will run terminal commands for you (venv activation, installs, server start) WITHOUT asking for permission.
- If a step requires a browser action, the assistant will provide a direct link to click.
- The assistant should NOT ask "what would you like to do next" during the startup process.

2) Browser links during sessions
- App root: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
- Reload clubs mapping: [http://127.0.0.1:5000/admin/reload-clubs](http://127.0.0.1:5000/admin/reload-clubs)
- Debug resolve path: [http://127.0.0.1:5000/admin/debug-resolve?name=January2024StateMeetsMen.xls](http://127.0.0.1:5000/admin/debug-resolve?name=January2024StateMeetsMen.xls)
- Debug Q column scan: [http://127.0.0.1:5000/admin/debug-q-scan?meet=January2024StateMeetsMen.xls&gender=M&limit=50](http://127.0.0.1:5000/admin/debug-q-scan?meet=January2024StateMeetsMen.xls&gender=M&limit=50)

3) Session startup checklist
```powershell
cd "C:\Users\megan\OneDrive\Documents\Malaysia Times Database"
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install flask pandas openpyxl xlrd==2.0.1
python -m Malaysia_Times_Database.Malaysia_Database
```
Then click: `http://127.0.0.1:5000/admin/reload-clubs` → back to `http://127.0.0.1:5000/` and apply filters.

4) Note for new developers
- The “Working Session Protocol” exists to streamline live collaboration with the assistant. Outside of these sessions, follow the regular Installation and Checklist sections.

### Quick start for the next session (copy/paste)
```powershell
cd "C:\Users\megan\OneDrive\Documents\Malaysia Times Database"
python -c "import flask, pandas, openpyxl, xlrd; print('Dependencies OK')" || pip install flask pandas openpyxl xlrd==2.0.1
python -m Malaysia_Times_Database.Malaysia_Database
Start-Sleep 3
Invoke-WebRequest -Uri "http://127.0.0.1:5000/admin/reload-athleteinfo" -UseBasicParsing
Invoke-WebRequest -Uri "http://127.0.0.1:5000/admin/reload-clubs" -UseBasicParsing
Start-Process "http://127.0.0.1:5000"
```

## Streamlined Startup Protocol

**This is the optimized startup sequence for any new session. Follow these steps exactly.**

### Phase 1: Environment Setup & Dependencies
```powershell
# Navigate to project directory
cd "C:\Users\megan\OneDrive\Documents\Malaysia Times Database"

# Check if port 5000 is available
netstat -an | findstr :5000

# Verify dependencies (install if missing)
python -c "import flask, pandas, openpyxl, xlrd; print('Dependencies OK')" || pip install flask pandas openpyxl xlrd==2.0.1

# Verify xlrd version (critical for .xls support)
python -c "import xlrd; print('xlrd version:', xlrd.__version__)"
```

**Expected output:** `xlrd version: 2.0.1`

### Phase 2: Start Application
```powershell
# Start the application
python -m Malaysia_Times_Database.Malaysia_Database
```

**Expected output:**
```
* Serving Flask app 'On_Track_Calculator.On_Track_Code'
* Debug mode: on
* Running on http://127.0.0.1:5000
```

### Phase 3: Automated Data Loading (NEW)
```powershell
# Wait for server to start
Start-Sleep 3

# Automatically load AthleteINFO data
Invoke-WebRequest -Uri "http://127.0.0.1:5000/admin/reload-athleteinfo" -UseBasicParsing

# Automatically load Clubs mapping
Invoke-WebRequest -Uri "http://127.0.0.1:5000/admin/reload-clubs" -UseBasicParsing

# Verify data loading with health check
Invoke-WebRequest -Uri "http://127.0.0.1:5000/admin/debug-resolve?name=January2024StateMeetsMen.xls" -UseBasicParsing
```

**Expected output:** "exists: True" message

### Phase 4: Application Testing
```powershell
# Open main application
Start-Process "http://127.0.0.1:5000"

# Test data parsing (verify xlrd is working)
Invoke-WebRequest -Uri "http://127.0.0.1:5000/admin/debug-q-scan?meet=January2024StateMeetsMen.xls&gender=M&limit=5" -UseBasicParsing
```

**Expected output:** Should show athlete data like "IBERLE, Felix Viktor" with team information

**Manual verification steps:**
1. **Go to main application:** [http://127.0.0.1:5000](http://127.0.0.1:5000)
2. **Select test data:**
   - Meets: Check "January2024StateMeetsMen.xls"
   - Gender: Check "M"
   - Events: Check "50 Free"
   - Age Groups: Check "OPEN"
3. **Click "Apply Selection"**
4. **Verify table populates with data**
5. **Check that State column shows proper state codes (not blank)**
6. **Test foreign athletes:** Check "Include Non-Malaysian Swimmers" and verify athletes like "KIL, Hyeonjoong" show "KOR" in State column

### Troubleshooting Common Issues

**Issue: "ModuleNotFoundError: No module named 'xlrd'"**
- **Solution:** Reinstall xlrd with `pip install xlrd==2.0.1 --no-cache-dir --force-reinstall`

**Issue: "no rows to show" in debug output**
- **Cause:** xlrd version incompatibility
- **Solution:** Ensure xlrd==2.0.1 is installed correctly

**Issue: Port 5000 already in use**
- **Solution:** Check for existing processes with `netstat -an | findstr :5000` and kill if necessary

**Issue: Table not populating**
- **Check:** Verify xlrd version with `python -c "import xlrd; print(xlrd.__version__)"`
- **Expected:** Should return `2.0.1`

**Issue: State column shows blanks**
- **Solution:** Ensure Phase 3 automated data loading completed successfully
- **Check:** Verify clubs mapping loaded with health check

**Issue: PowerShell web request errors**
- **Solution:** Use `curl` instead: `curl http://127.0.0.1:5000/admin/reload-athleteinfo`

**Alternative startup method (if system Python issues):**
```powershell
cd "C:\Users\megan\OneDrive\Documents\Malaysia Times Database\On_Track_Calculator"
python On_Track_Code.py
```

Then complete Phase 3 and 4 above.

### Quick Start from Fresh Environment

**Use this section when starting completely fresh or after environment issues.**

### Step 1: Clean Environment Setup
```powershell
# Navigate to project directory
cd "C:\Users\megan\OneDrive\Documents\Malaysia Times Database"

# Remove any existing virtual environment
Remove-Item -Recurse -Force .venv -ErrorAction SilentlyContinue

# Create fresh virtual environment
py -3 -m venv .venv

# Activate virtual environment (use .bat file to avoid PowerShell execution policy issues)
.venv\Scripts\activate.bat
```

### Step 2: Install Dependencies (Critical Order)
```powershell
# Upgrade pip first
python -m pip install --upgrade pip

# Install core dependencies
pip install flask pandas openpyxl

# Install xlrd with specific version and no cache (critical for .xls support)
pip install xlrd==2.0.1 --no-cache-dir

# Verify xlrd installation
python -c "import xlrd; print('xlrd version:', xlrd.__version__)"
```

**Expected output:** `xlrd version: 2.0.1`

### Step 3: Start Application
```powershell
# Start the application
python -m Malaysia_Times_Database.Malaysia_Database
```

**Expected output:**
```
* Serving Flask app 'On_Track_Calculator.On_Track_Code'
* Debug mode: on
* Running on http://127.0.0.1:5000
```

### Step 4: Verify Application Works
1. **Open browser:** [http://127.0.0.1:5000](http://127.0.0.1:5000)
2. **Reload data:** [http://127.0.0.1:5000/admin/reload-clubs](http://127.0.0.1:5000/admin/reload-clubs)
3. **Test parsing:** [http://127.0.0.1:5000/admin/debug-q-scan?meet=January2024StateMeetsMen.xls&gender=M&limit=5](http://127.0.0.1:5000/admin/debug-q-scan?meet=January2024StateMeetsMen.xls&gender=M&limit=5)

**Expected debug output:** Should show athlete data like "IBERLE, Felix Viktor" with team information.

### Step 5: Test Table Population
1. Go back to [http://127.0.0.1:5000](http://127.0.0.1:5000)
2. Select meets (e.g., January2024StateMeetsMen.xls)
3. Choose gender and events
4. Click "Apply Selection"
5. **Table should populate with data**

### Troubleshooting Common Issues

**Issue: "ModuleNotFoundError: No module named 'xlrd'"**
- **Solution:** Reinstall xlrd with `pip install xlrd==2.0.1 --no-cache-dir --force-reinstall`

**Issue: "no rows to show" in debug output**
- **Cause:** xlrd version incompatibility
- **Solution:** Ensure xlrd==2.0.1 is installed correctly

**Issue: PowerShell execution policy errors**
- **Solution:** Use `.venv\Scripts\activate.bat` instead of `.ps1` files

**Issue: Table not populating**
- **Check:** Verify xlrd version with `python -c "import xlrd; print(xlrd.__version__)"`
- **Expected:** Should return `2.0.1`

**Alternative startup method (if virtual environment issues):**
```powershell
cd "C:\Users\megan\OneDrive\Documents\Malaysia Times Database\On_Track_Calculator"
python On_Track_Code.py
```

Then open these links in order:
- Reload AthleteINFO (loads foreign=Y/N and country_code): [http://127.0.0.1:5000/admin/reload-athleteinfo](http://127.0.0.1:5000/admin/reload-athleteinfo)
- Reload Clubs (optional if club list changed): [http://127.0.0.1:5000/admin/reload-clubs](http://127.0.0.1:5000/admin/reload-clubs)
- App home: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

## Registration Protocol for Next Year

### AthleteINFO.csv Schema Requirements
The `AthleteINFO.csv` file now includes a `country_code` column for proper foreign athlete handling:

**Current columns in AthleteINFO.csv:**
- `name`: Athlete's full name
- `birthdate`: YYYYMMDD format
- `gender`: M/F
- `team_name`: Club/team name
- `team_code`: 3-letter team code
- `state_code`: 3-letter state code (for Malaysian athletes)
- `foreign`: Y/N flag
- `country_code`: 3-letter country code (for foreign athletes)
- `source_meet`: Source of the data
- `source_sheet`: Sheet name
- `source_date`: Date of source
- `aliases`: Alternative names
- `verified`: Verification status
- `notes`: Additional notes

**New columns needed for registration process:**
- `athlete_id`: Unique identifier for each athlete
- `assigned_club`: The athlete's current club name
- `assigned_club_state`: The state code of their assigned club
- `registration_status`: PENDING/COMPLETED/VERIFIED
- `payment_status`: PENDING/PAID/REFUNDED
- `registration_date`: When they registered
- `last_updated`: Last modification date

### Registration Process
1. **For Malaysian athletes**: Set `foreign=N`, `country_code=MAS`
2. **For foreign athletes**: Set `foreign=Y`, `country_code` to their country (e.g., KOR, USA, SGP)
3. **For dual-citizen athletes eligible for Malaysia**: Set `foreign=N`, `country_code=MAS`

### Current State Assignment Logic (Implemented)
The system now prioritizes AthleteINFO over meet data Nation column:

1. **PRIORITY 1: Check AthleteINFO first** (regardless of meet data Nation)
   - **If foreign=Y**: Use AthleteINFO country_code
   - **If foreign=N**: Use AthleteINFO state_code or fall back to club→state mapping
2. **FALLBACK: If not in AthleteINFO**: Use meet data Nation as fallback
   - **If Nation != MAS**: Use that country code as state
   - **If Nation = MAS**: Use club→state mapping

**Examples:**
- **KIL, Hyeonjoong**: Nation=MAS in meet data, but foreign=Y in AthleteINFO → Shows "KOR"
- **LEE, Elson**: Nation=USA in meet data, but foreign=N in AthleteINFO → Shows "MAS"
- **IBERLE, Felix Viktor**: Nation=INA in meet data → Shows "INA"
- **Regular Malaysian athletes**: Use club→state mapping

### Current Data Status (As of Latest Update)
**Foreign athletes properly configured:**
- All foreign athletes have `foreign=Y` and correct `country_code`
- Malaysian athletes have `foreign=N` and `country_code=MAS`
- State assignment logic prioritizes AthleteINFO over meet data

**Key foreign athletes in system:**
- KIL, Hyeonjoong: `foreign=Y`, `country_code=KOR` (should show KOR as state)
- LEE, Elson: `foreign=N`, `country_code=MAS` (eligible for Malaysian teams)
- IBERLE, Felix Viktor: `foreign=Y`, `country_code=INA` (should show INA as state)
- All other foreign athletes from AUS, GBR, HKG, IRL, MDV, SGP, UKR, USA

### Data Quality Checks
- Ensure all foreign athletes have country_code populated
- Verify dual-citizen athletes are marked foreign=N if eligible for Malaysia
- Cross-reference meet data Nation column with AthleteINFO foreign flags
- Test state assignment logic with known foreign athletes

## Athlete Registration Process (Next Year)

### Database Schema Updates Needed
The `AthleteINFO.csv` will need additional columns for the registration process:

**New columns to add:**
- `athlete_id`: Unique identifier for each athlete
- `assigned_club`: The athlete's current club name
- `assigned_club_state`: The state code of their assigned club
- `registration_status`: PENDING/COMPLETED/VERIFIED
- `payment_status`: PENDING/PAID/REFUNDED
- `registration_date`: When they registered
- `last_updated`: Last modification date

### Registration User Interface Requirements

#### 1. Athlete Access Methods
**Option A: Existing Athlete (Update Record)**
- Enter existing `athlete_id` to access their current record
- System displays current information for confirmation/editing
- Athlete can update any field except `athlete_id`

**Option B: New Athlete (Create Record)**
- System generates new `athlete_id` automatically
- Athlete fills out complete registration form

#### 2. Registration Form Fields
**Personal Information:**
- Full Name (required)
- Birth Date (required, format: DD/MM/YYYY)
- Gender (required, dropdown: Male/Female)
- Contact Information (email, phone)

**Athletic Information:**
- Foreign Status (required, dropdown: Malaysian/Non-Malaysian)
- If Non-Malaysian: Country Code (required, dropdown of countries)
- If Malaysian: State Selection (required, dropdown of Malaysian states)
- Club Selection (required, filtered by selected state)
- Previous Competition Experience (optional)

**System Fields (auto-populated):**
- Athlete ID (auto-generated or existing)
- Registration Date (auto-populated)
- Payment Status (auto-populated after payment)

#### 3. State and Club Selection Logic
**State Selection:**
- Dropdown populated from `Clubs_By_State.xlsx` sheet names
- Only Malaysian states shown for Malaysian athletes
- "Foreign" option for non-Malaysian athletes

**Club Selection:**
- Dropdown populated from `Clubs_By_State.xlsx` based on selected state
- Clubs filtered by selected state
- "Other" option with text field for clubs not in the list

#### 4. Payment Integration
**Payment Requirements:**
- Integration with payment gateway (Stripe/PayPal recommended)
- Secure payment processing
- Payment confirmation before registration completion
- Receipt generation and email delivery

**Payment Flow:**
1. Athlete completes registration form
2. System calculates registration fee
3. Payment gateway integration
4. Payment confirmation
5. Registration completion and email notification

#### 5. Data Validation and Quality Checks
**Pre-submission Validation:**
- Required fields completion check
- Email format validation
- Date format validation
- Duplicate athlete_id prevention
- Club-state consistency verification

**Post-submission Processing:**
- Automatic `assigned_club_state` population from club selection
- `country_code` population based on foreign status
- Email confirmation to athlete
- Admin notification for new registrations

### Registration System Architecture
**Frontend Requirements:**
- Responsive web form
- Real-time validation
- Payment gateway integration
- Email notification system

**Backend Requirements:**
- Secure data handling
- Payment processing
- Email service integration
- Data export capabilities for meet management

**Database Updates:**
- AthleteINFO.csv schema updates
- Clubs_By_State.xlsx integration
- Payment records tracking
- Registration audit trail


## Profiling and Performance Playbook

Use this checklist to identify bottlenecks and validate improvements.

1) Baseline timings
- Start the app and capture cold vs warm timings:
  - Cold load: first visit to `/` triggers background warmers
  - Warm load: refresh after caches populated
- Add temporary timing logs around hot paths in `On_Track_Code.py`:
  - `_preparse_meet_rows(...)`
  - `load_mot_targets_map(...)`, `load_aqua_points_maps(...)`
  - Export path (`/export`)

2) Python profilers
- `cProfile` minimal example:
  - Wrap `ontrack_app.run(...)` with `cProfile` or run a one-off script calling key functions.
- `pyinstrument` (friendly flamegraphs):
  - `pip install pyinstrument`
  - Run `pyinstrument -r html -o profile.html -m Malaysia_Times_Database.Malaysia_Database`
  - Hit `/` and filters; stop with Ctrl+C and review `profile.html`.

3) IO vs CPU breakdown
- Measure pandas Excel IO separately from post‑processing:
  - Time `pd.ExcelFile(...)`, `pd.read_excel(...)`
  - Time transformation loops and mapping/dictionary lookups

4) Caching strategy
- Confirm LRU caches are effective:
  - `load_mot_targets_map.cache_info()` and `load_aqua_points_maps.cache_info()`
- Consider persisting parsed meet rows to CSV/Parquet to avoid re‑reading large `.xls` files.

5) Hotspot remediation ideas
- Pre‑index frequently accessed maps once (AQUA/MOT/Clubs) and avoid repeated try/except in inner loops.
- Collapse duplicate logic between index and export into shared utilities.
- Consider chunked parsing or sheet whitelisting to reduce sheet scans.
- If meet files are very large, pilot pre‑processing scripts to normalize to a canonical schema once.

6) Client‑side table perf
- For very large row counts, add pagination or virtual scrolling.
- Defer DOM updates; minimize reflow by updating the table body in a single pass.

7) Regression guardrails
- Record row counts per selection and output file size.
- Track median time to “Apply Selection” across typical meet combinations.


## Data Validation Checklist

Pre‑run
- Verify presence of required files:
  - `Malaysia_Times_Database/Age_OnTrack_AQUA.xlsx`
  - Meets in `Meets/` as referenced in `AVAILABLE_MEETS`
- Confirm `Clubs_By_State.xlsx` loads (admin link: `/admin/reload-clubs`).

Schema/format sanity
- Shared workbook:
  - `MOT Tables 25` has Gender, Event, Age, and target time in expected columns (A/B/C/M)
  - `AQUA POINTS` has headers row + male/female base rows
- Meets:
  - Tabs contain result rows; non‑result sheets are skipped automatically
  - Gender in column B; Distance in C; Stroke in D; Name in E; Time in I; AQUA in K

Mapping and overrides
- `foreign_swimmers.txt` contains one name per line (plain text, UTF‑8)
- `AthleteINFO.csv` headers include name,state_code,team_name,verified (case‑insensitive)
- `Clubs_By_State.xlsx` sheet titles are state codes; column A has club/team names; column C optionally has a code

Functional checks
- Apply selection for SUKMA/MIAG/MO/SEAG; verify row counts and no unexpected “N/A” in On Track columns
- Toggle Results: best vs all; ensure row reduction and sorting are correct
- Export and open `On_Track_Results.xlsx`; header order matches the UI

Admin diagnostics
- `/admin/debug-resolve?name=SUKMA_2024_Men.xls` shows resolved path exists
- `/admin/debug-q-scan?meet=January2024StateMeetsMen.xls&gender=M&limit=50` highlights unmapped teams
- `/admin/debug-club?name=Selangor` shows mapping hits and known state codes


