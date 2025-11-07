# Proposed Folder Structure - Malaysia Swimming Analytics

## 🎯 Design Principles

1. **Separation of Concerns**: Each project folder is self-contained
2. **Shared Resources**: Reference data (MAP, MOT, AQUA) at parent level
3. **Scalability**: Easy to add new projects (e.g., Athlete Registration, Performance Tracking)
4. **Maintainability**: Clear organization, no clutter
5. **Data Flow**: Clear hierarchy (shared → projects → outputs)

## 📁 Proposed Structure

```
Malaysia Swimming Analytics/
├── 📊 reference_data/              # Shared lookup tables (used by all projects)
│   ├── MAP_Times.csv               # Malaysia Age Points reference
│   ├── MOT_Times.csv               # Malaysia On Track reference (rebuilt from analysis)
│   ├── AQUA_Base_Times.csv         # World Aquatics base times
│   ├── SEA_Games_Times.csv         # SEA Games medal times
│   └── Clubs_By_State.csv          # Club-to-state mapping
│
├── 📈 statistical_analysis/        # MOT Delta Analysis Project
│   ├── Period Data/                # Source data (2,240 files)
│   ├── Delta Data/                 # Analysis results (84 folders)
│   ├── reports/                    # Generated reports
│   │   ├── Delta_Comparison_USA_vs_Canada.html
│   │   └── Delta_Comparison_USA_vs_Canada.csv
│   ├── PhD/                        # Dissertation materials
│   │   ├── Chapter 3 - Data Collection and Validation Methodology.txt
│   │   └── ...
│   ├── scripts/                    # Production scripts
│   │   ├── run_mot_delta_analysis.py
│   │   ├── load_canada_tracks.py
│   │   ├── load_usa_deltas.py
│   │   ├── compare_deltas_canada.py
│   │   ├── build_delta_html.py
│   │   ├── db_schema.py
│   │   └── events_catalog.py
│   ├── temp/                       # Temporary test scripts (can be deleted)
│   │   ├── debug_f100back_1516.py
│   │   ├── peek_track_start.py
│   │   └── create_delta_folders.py
│   ├── MOT_Delta_Index.html        # Main index page
│   ├── MOT_Delta_Index.csv         # Results database
│   ├── MOT_Delta_Analysis_Results.csv
│   ├── READ_ME_FIRST.txt           # Quick start guide
│   ├── DATABASE_DOCUMENTATION.md   # Database docs
│   └── Statistical Session Startup Guide!!!!!!!!!.txt
│
├── 📋 meet_reports/                # NEW: Meet Results Reporting Project
│   ├── data/                       # Meet data files
│   │   ├── meets/                  # Competition Excel files
│   │   └── athletes/               # Athlete databases
│   ├── reports/                    # Generated reports
│   ├── templates/                  # Report templates
│   ├── scripts/                    # Production scripts
│   │   ├── generate_report.py
│   │   ├── export_to_excel.py
│   │   └── query_reference_data.py  # Looks up to ../reference_data/
│   ├── temp/                       # Temporary test scripts
│   └── README.md                   # Project documentation
│
├── 🗄️ times_database/              # NEW: Times Database Project (old system migration)
│   ├── database/                   # SQLite database
│   │   └── malaysia_swimming.db    # Main database
│   ├── data/                       # Data files
│   │   ├── meets/                  # Meet files
│   │   ├── athletes/               # Athlete data
│   │   └── reference/              # Local reference copies (if needed)
│   ├── scripts/                    # Production scripts
│   │   ├── convert_meets_to_sqlite.py
│   │   ├── migrate_data.py
│   │   └── query_reference_data.py  # Looks up to ../reference_data/
│   ├── temp/                       # Temporary test scripts
│   ├── archive_old_build/          # Legacy Flask system (for reference)
│   └── README.md                   # Project documentation
│
├── 🧪 temp_scripts/                # NEW: Global temporary/testing folder
│   └── [session-specific test files]
│
├── 📚 docs/                        # Global documentation
│   ├── MAP_Methodology.md
│   ├── MOT_Methodology.md
│   ├── AQUA_Methodology.md
│   └── README.md
│
├── 🗃️ database/                    # Shared database location
│   └── malaysia_swimming.db        # SQLite (if shared across projects)
│
├── 📖 Malaysia Swimming Analytics Handbook.md  # Main project guide
├── 📖 SESSION_START.md             # Session startup guide
│
└── [Future Projects]
    ├── athlete_registration/
    ├── performance_tracking/
    └── coaching_tools/
```

## 🔄 Data Flow Architecture

### Reference Data (Parent Level)
- **Location**: `reference_data/`
- **Used By**: All projects (Statistical Analysis, Meet Reports, Times Database)
- **Format**: CSV/Excel for easy access
- **Updates**: 
  - MOT_Times.csv updated from Statistical Analysis results
  - MAP/AQUA updated periodically by administrator

### Project-Specific Data
- **Location**: Each project folder (`statistical_analysis/`, `meet_reports/`, `times_database/`)
- **Scope**: Project-specific input/output data
- **Isolation**: Projects don't directly access each other's data

### Shared Database (Optional)
- **Location**: `database/` (or within `times_database/database/`)
- **Content**: SQLite database with all structured data
- **Access**: Projects query via scripts

## 📦 Project Folder Structure Template

Each project folder follows this pattern:

```
project_name/
├── data/              # Input data specific to this project
├── reports/           # Generated outputs
├── scripts/           # Production code (version controlled)
├── temp/              # Temporary test scripts (can be deleted)
├── docs/              # Project-specific documentation (optional)
└── README.md          # Project overview and quick start
```

## 🎯 Benefits of This Structure

### 1. **Clear Separation**
- Each project is self-contained
- Easy to understand what belongs where
- No confusion about file ownership

### 2. **Shared Resources**
- Reference data accessible to all projects
- No duplication of lookup tables
- Single source of truth for MAP/MOT/AQUA

### 3. **Scalability**
- Easy to add new projects (copy template structure)
- Each project can evolve independently
- No conflicts between project scripts

### 4. **Maintainability**
- `temp/` folders can be cleaned regularly
- Production scripts clearly separated
- Documentation co-located with projects

### 5. **Data Flow Clarity**
```
Reference Data (parent)
    ↓
Projects (query reference_data/)
    ↓
Outputs (reports/, Delta Data/, etc.)
    ↓
Update Reference Data (MOT_Times.csv)
```

## 🔧 Implementation Plan

### Phase 1: Reorganize Current Structure
1. Create `reference_data/` folder
2. Move lookup tables from current locations
3. Create `statistical_analysis/` project folder
4. Move Statistical Analysis files into folder
5. Create `temp/` folder within statistical_analysis/
6. Move temporary scripts to temp/

### Phase 2: Create New Project Folders
1. Create `meet_reports/` folder with template structure
2. Create `times_database/` folder with template structure
3. Move relevant files from root to appropriate folders

### Phase 3: Update Scripts
1. Update all scripts to use `../reference_data/` paths
2. Update database paths if needed
3. Update documentation with new paths

### Phase 4: Clean Up
1. Remove duplicate files
2. Archive old structures if needed
3. Update all documentation

## 📋 Migration Checklist

- [ ] Create `reference_data/` folder
- [ ] Move MAP/MOT/AQUA lookup tables to `reference_data/`
- [ ] Create `statistical_analysis/` folder structure
- [ ] Move Statistical Analysis files (Period Data, Delta Data, scripts, etc.)
- [ ] Create `meet_reports/` folder structure
- [ ] Create `times_database/` folder structure
- [ ] Move database to appropriate location
- [ ] Create `temp_scripts/` global folder (optional)
- [ ] Update all script paths
- [ ] Update documentation references
- [ ] Test all scripts with new paths
- [ ] Update handbook and guides

## 🚀 Future Project Scalability

When adding new projects (e.g., Athlete Registration):

```
athlete_registration/
├── data/
│   ├── registration_forms/
│   └── payment_records/
├── reports/
│   └── registration_summary.xlsx
├── scripts/
│   ├── process_registration.py
│   └── generate_reports.py
├── temp/
└── README.md
```

Scripts query reference data: `../reference_data/MOT_Times.csv`

## 💡 Additional Suggestions

### 1. **Version Control Strategy**
- Each project folder could have its own `.gitignore` if needed
- Common patterns: Ignore `temp/`, `*.pyc`, `__pycache__/`

### 2. **Shared Utilities**
```
utils/                    # NEW: Shared Python utilities
├── database_helpers.py   # Common database functions
├── reference_data_loader.py  # Load MAP/MOT/AQUA tables
└── time_parsers.py       # Time format parsing
```

### 3. **Configuration Management**
```
config/                   # NEW: Configuration files
├── database_config.json  # Database connection settings
├── reference_paths.json  # Paths to reference data
└── project_settings.json # Project-specific settings
```

### 4. **Documentation Hierarchy**
- **Parent Level**: `Malaysia Swimming Analytics Handbook.md` (overview)
- **Project Level**: Each project has `README.md` or `docs/`
- **Script Level**: Docstrings in Python files

## 🎯 Recommended Folder Names (Final)

```
Malaysia Swimming Analytics/
├── reference_data/          # Shared lookup tables
├── statistical_analysis/    # MOT Delta Analysis Project
├── meet_reports/            # Meet Results Reporting
├── times_database/          # Times Database System
├── database/                # Shared SQLite database (optional)
├── docs/                    # Global methodology docs
├── temp_scripts/            # Global temporary scripts (optional)
└── [Main documentation files at root]
```

This structure supports:
- ✅ Clear organization
- ✅ Easy scaling to new projects
- ✅ Shared reference data
- ✅ Isolated project development
- ✅ Clean separation of production vs. test code
- ✅ Future Malaysia Aquatics projects




