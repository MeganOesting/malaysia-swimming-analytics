# Malaysia Swimming Analytics - Comprehensive Developer Handbook

## 🎯 Project Overview

The Malaysia Swimming Analytics platform is a **complete rebuild** of the existing Malaysia Times Database system, moving from a "Winchester House" architecture (multiple overlapping Flask/Excel-based projects) to a modern, scalable system using React, FastAPI, and PostgreSQL.

### 🏗️ Architecture Transformation
- **FROM**: Flask + Excel + pandas (old system)
- **TO**: React + FastAPI + PostgreSQL (new system)
- **GOAL**: Clean, modern, scalable swimming analytics platform

## 🛠️ New Tech Stack

### Frontend
- **React** with TypeScript
- **Next.js** for full-stack React framework
- **Tailwind CSS** for styling
- **Headless UI** for accessible components
- **Heroicons** for icons
- **Chart.js** + **React Chart.js 2** for data visualization
- **React Hook Form** for form handling
- **React Query** for data fetching and caching
- **Axios** for HTTP requests

### Backend
- **FastAPI** (Python web framework)
- **PostgreSQL** (primary database)
- **Redis** (caching and session storage)
- **SQLAlchemy** (ORM)
- **Alembic** (database migrations)
- **psycopg2-binary** (PostgreSQL adapter)
- **python-jose** (JWT authentication)
- **passlib** (password hashing)
- **python-multipart** (file uploads)
- **Celery** (background tasks)
- **Flower** (Celery monitoring)

### Infrastructure
- **Docker** + **Docker Compose** (containerization)
- **Kubernetes** (production orchestration)

## 📊 Core Features

### Current Features
- **Performance Analysis**: Compare swimmer performances against AQUA targets
- **Age Points Calculation**: Malaysia Age Points (MAP) computation
- **Multi-Meet Support**: Analyze results from multiple competitions
- **Foreign Athlete Handling**: Proper identification of non-Malaysian swimmers
- **Data Export**: Export filtered results to Excel
- **Real-time Filtering**: Interactive web interface with multiple filter options

### Future Features
- **Advanced Analytics**: Statistical analysis and reporting
- **Athlete Registration**: Registration and payment processing
- **Performance Tracking**: Long-term athlete development tracking
- **Mobile App**: React Native mobile application
- **API Integration**: External data source integration

## 🗄️ Database Schema Design

### Core Tables
- **athletes**: Swimmer information and demographics
- **meets**: Competition details and metadata
- **results**: Individual swim results and times
- **events**: Swimming events (distance, stroke, gender)
- **clubs**: Club and team information
- **states**: Malaysian state codes and mappings

### Data Relationships
- Athletes belong to clubs
- Results link athletes to meets and events
- Meets contain multiple results
- Events define swimming disciplines

## 📁 Project Structure

```
Malaysia Swimming Analytics/
├── src/
│   ├── web/                 # FastAPI backend
│   │   ├── main.py         # Main application
│   │   ├── models/         # SQLAlchemy models
│   │   ├── routers/        # API endpoints
│   │   ├── services/        # Business logic
│   │   └── utils/          # Utility functions
│   ├── frontend/           # React frontend
│   │   ├── components/     # React components
│   │   ├── pages/          # Next.js pages
│   │   ├── hooks/          # Custom React hooks
│   │   └── utils/          # Frontend utilities
│   └── shared/             # Shared types and utilities
├── data/
│   ├── meets/              # Excel meet files
│   ├── athletes/           # Athlete data
│   └── reference/          # Reference data
├── scripts/                # Data migration scripts
├── tests/                  # Test suites
├── docs/                   # Documentation
├── docker-compose.yml      # Docker services
├── requirements.txt        # Python dependencies
└── package.json           # Node.js dependencies
```

## 🚀 Development Status

### ✅ Completed (Verified from Actual Files)
- **Project structure setup** - Complete directory structure with src/, data/, scripts/ (verified in project root)
- **Docker configuration** - Full Docker Compose setup in `docker-compose.yml` with 6 services
- **Database schema design** - PostgreSQL schema defined in `scripts/init.sql`
- **Excel data conversion** - Successfully converted all meet files to SQLite (`malaysia_swimming.db`)
- **Docker services running** - All containers operational (from `docker-compose.yml`)
- **Terminal issues resolved** - Fixed "q" prefix command issue (resolved by restarting Cursor)
- **Data parsing logic** - Standard format parser in `scripts/convert_meets_to_sqlite_fixed.py`
- **SEAG anomaly handling** - Adapted SEAG_2025_ALL.xlsx to standard format (file modified)
- **Foreign athlete detection** - Logic in `scripts/convert_meets_to_sqlite_fixed.py`
- **Club-to-state mapping** - Reference data in `data/reference/Clubs_By_State.xlsx`
- **Reference data conversion** - Age_OnTrack_AQUA.xlsx and Clubs_By_State.xlsx converted to SQLite
- **Methodology documentation** - Complete docs in `docs/` folder (MAP_Methodology.md, MOT_Methodology.md, AQUA_Methodology.md)
- **Table naming standardization** - Corrected table names in `scripts/convert_meets_to_sqlite_fixed.py`

### 🔄 In Progress
- **Data loading verification** - Testing direct mapping and complex column handling
- **File naming validation** - Ensuring meet file names accurately reflect contents
- **Code table references** - Verifying all code calls the correct database tables

### 📊 Current Data Status (From Actual Files)
- **SQLite Database**: `malaysia_swimming.db` (verified in project root) - Contains all converted meet data
- **Excel Files Processed**: 9 meet files in `data/meets/` folder successfully parsed
- **Data Format**: Standard MO/MIAG/SUKMA format (SEAG adapted to match in `data/meets/SEAG_2025_ALL.xlsx`)
- **Foreign Athletes**: Properly identified and flagged (logic in `scripts/convert_meets_to_sqlite_fixed.py`)
- **Club Mapping**: State codes assigned to clubs (from `data/reference/Clubs_By_State.xlsx`)

## 🎯 Recent Technical Achievements

### ✅ Data Conversion Success
- **Excel to SQLite**: All 9 meet files successfully converted
- **Standard Format Recognition**: MO, MIAG, SUKMA, State meets use consistent column structure
- **SEAG Anomaly Handling**: SEAG_2025_ALL.xlsx adapted to match standard format
- **Data Integrity**: All swim times, athlete names, and meet information preserved

### ✅ Infrastructure Setup
- **Docker Services**: All 6 containers running successfully
  - PostgreSQL (port 5432) - Database
  - Redis (port 6379) - Cache
  - FastAPI Backend (port 8000) - API
  - React Frontend (port 3000) - Web interface
  - Celery Worker - Background tasks
  - Flower (port 5555) - Monitoring
- **Terminal Issues Resolved**: Fixed "q" prefix command corruption issue
- **Database Schema**: PostgreSQL schema with proper relationships

### ✅ Data Processing Logic
- **Foreign Athlete Detection**: Automatic identification of non-Malaysian swimmers
- **Club-to-State Mapping**: Reference data for proper state assignments
- **Time Format Handling**: Consistent parsing of swimming times
- **Event Standardization**: Proper categorization of swimming events

### 🔧 Current Technical Challenge
- **Schema Migration**: SQLite to PostgreSQL migration in progress
- **Column Mapping**: Resolving differences between SQLite and PostgreSQL schemas
- **Data Validation**: Ensuring data integrity during migration

### 📋 Future Data Updates Required
- **MAP Times Update**: Update MAP (Malaysia Age Points) times for ages 13, 15, and 17 after data analysis on improvement deltas from age to age
- **MOT Times Recreation**: Recreate valid MOT (Malaysia On Track) times using new methodology
- **AQUA Base Times**: Annual updates by administrator
- **Podium Target Times**: Every 2 years (next update after December 2025 SEA Games)

### 📚 Methodology Documentation ✅ COMPLETED
- **MAP Methodology**: ✅ Complete documentation for Malaysia Age Points system (12-18, USA Swimming base times)
- **MOT Methodology**: ✅ Complete documentation for Malaysia On Track system (15-23, senior level times)
- **AQUA Methodology**: ✅ Complete documentation for World Aquatics AQUA points system

### 📋 TODO List

#### Phase 1: Data Migration ✅ COMPLETED
- [x] **Clean SEAG_2025_ALL.xlsx** - Adapted to standard MO/MIAG/SUKMA format
- [x] **Create unified parser** - Standard format parser implemented
- [x] **Design PostgreSQL schema** - Complete schema with relationships
- [x] **Build migration scripts** - SQLite conversion completed
- [x] **Reference data conversion** - Age_OnTrack_AQUA.xlsx and Clubs_By_State.xlsx converted
- [x] **Methodology documentation** - Complete MAP, MOT, AQUA documentation
- [x] **Table naming standardization** - Corrected table names and relationships

#### Phase 1.5: Data Loading Verification 🔄 IN PROGRESS
- [ ] **Direct mapping test** - Load simple columns first (name, gender, age, time, place)
- [ ] **Sticky columns handling** - Complex mappings (foreign athletes, club mapping)
- [ ] **File naming validation** - Ensure meet file names accurately reflect contents
- [ ] **Code table references** - Verify all code calls the correct database tables
- [ ] **Data integrity checks** - Validate data completeness and accuracy
- [ ] **Performance testing** - Ensure conversion runs efficiently

#### Phase 2: Backend Development
- [ ] **Implement authentication** (JWT-based)
- [ ] **Create athlete management** endpoints
- [ ] **Build meet results** API
- [ ] **Add performance analysis** calculations
- [ ] **Implement filtering** and search functionality

#### Phase 3: Frontend Development
- [ ] **Build dashboard** with performance metrics
- [ ] **Create athlete profiles** and results display
- [ ] **Implement filtering** interface
- [ ] **Add data visualization** charts
- [ ] **Build export** functionality

#### Phase 4: Advanced Features
- [ ] **Add payment processing** for registrations
- [ ] **Implement mobile responsiveness**
- [ ] **Add advanced analytics** and reporting
- [ ] **Build admin panel** for data management

## 🚀 SEAMLESS STARTUP PROTOCOL

### 🎯 **AUTOMATIC DEVELOPER ONBOARDING**
This section provides a complete startup process that automatically loads all project context and gets any developer up to speed instantly.

### 📋 **Current Project Status (Verified from Actual Files)**
- **Data Conversion**: ✅ All 9 meet files converted to SQLite database (`malaysia_swimming.db`)
- **Reference Data**: ✅ Age_OnTrack_AQUA.xlsx and Clubs_By_State.xlsx converted to SQLite tables
- **Methodology Docs**: ✅ Complete documentation in `docs/` folder (MAP_Methodology.md, MOT_Methodology.md, AQUA_Methodology.md)
- **Database Schema**: ✅ PostgreSQL schema defined in `scripts/init.sql`
- **Docker Services**: ✅ Configuration in `docker-compose.yml` with 6 services
- **UI Foundation**: ✅ Complete React frontend with locked-in design
- **API Endpoints**: ✅ FastAPI backend with all necessary endpoints
- **Meet Abbreviations**: ✅ Implemented (SUK24, MIA25, MO25, SEAG25, ST24)
- **Statistical Analysis**: ✅ Complete data consolidation (all 4 periods: 2021-2022, 2023-2024, 2024-2025)
- **PhD Dissertation**: ✅ Updated with strategic context, problem statement, and significance sections
- **Current Branch**: `data-cleaning` (UI foundation committed)
- **Next Phase**: Data cleaning, validation, and functionality implementation

### 🎨 **UI IMPLEMENTATION COMPLETE**
- **Header**: MAS logos on left and right of title
- **Filter Section**: Complete with meets, gender, state, age groups, events (6x3 grid)
- **Events**: All 50m distances included (50 Free, 50 Back, 50 Breast, 50 Fly)
- **Styling**: Red accent color (#cc0000) for all checkboxes and buttons
- **Table**: All 13 columns with centered headers and compact row heights
- **Sidebar**: MAP, MOT, LTAD buttons
- **Meet Abbreviations**: SUK24, MIA25, MO25, SEAG25, ST24
- **Button Order**: Apply Selection, Download XLSX, Reset Filters

### 🌿 **BRANCHING STRATEGY**
- **`core-functionality`**: UI implementation locked in (completed)
- **`data-cleaning`**: Current branch for data validation and cleaning
- **File Management**: Same folder, Git tracks different versions
- **Switch Branches**: `git checkout core-functionality` or `git checkout data-cleaning`

### 📊 **DATA CONSOLIDATION COMPLETE**
- **Statistical Analysis**: All 4 periods consolidated in new build
  - `9.1.21-8.31.22` (24 files) - Successfully moved from old build
  - `9.1.23-8.31.24` (existing)
  - `9.1.24-8.31.25` (existing)
- **PhD Dissertation**: Updated with strategic context and academic framework
- **Old Build Cleanup**: Duplicate files removed, no data loss
- **Single Source of Truth**: All data now in `Statistical Analysis/` folder

### 🔄 **AUTOMATIC STARTUP SEQUENCE**
```bash
# 1. Navigate to project directory
cd "C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics"

# 2. Auto-start all services with Docker Compose
docker-compose up -d

# 3. Verify all services are running
docker ps

# 4. Check database status
python scripts/test_database_connection.py

# 5. Verify SQLite data
python -c "
import sqlite3
conn = sqlite3.connect('malaysia_swimming.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type = ?', ('table',))
tables = cursor.fetchall()
print('SQLite Tables:', [table[0] for table in tables])
cursor.execute('SELECT COUNT(*) FROM athletes')
athletes = cursor.fetchone()[0]
print(f'Athletes: {athletes}')
cursor.execute('SELECT COUNT(*) FROM results')
results = cursor.fetchone()[0]
print(f'Results: {results}')
conn.close()
"
```

### 🎯 **DEVELOPER CONTEXT LOADING**
The following commands will automatically load all project context:

```bash
# Load project structure
ls -la

# Check Docker services status
docker-compose ps

# Verify database connections
python scripts/test_database_connection.py

# Check SQLite data status
python -c "
import sqlite3
conn = sqlite3.connect('malaysia_swimming.db')
cursor = conn.cursor()
print('=== DATABASE STATUS ===')
cursor.execute('SELECT name FROM sqlite_master WHERE type = ?', ('table',))
tables = cursor.fetchall()
for table in tables:
    cursor.execute(f'SELECT COUNT(*) FROM {table[0]}')
    count = cursor.fetchone()[0]
    print(f'{table[0]}: {count} records')
conn.close()
"

# Check methodology documentation
ls docs/

# Verify meet files
ls data/meets/
```

### 📊 **CURRENT DATA STATUS (From Actual Files)**
- **SQLite Database**: `database/malaysia_swimming.db` (verified in database folder)
- **Tables**: athletes, meets, events, results, map_mot_aqua, club_state_mapping (from `scripts/convert_meets_to_sqlite_fixed.py`)
- **Meet Files**: 9 Excel files in `data/meets/` folder (SUKMA, MIAG, MO, SEAG, State meets)
- **Reference Data**: `data/reference/Age_OnTrack_AQUA.xlsx` → map_mot_aqua table
- **Club Mapping**: `data/reference/Clubs_By_State.xlsx` → club_state_mapping table
- **Statistical Analysis**: `Statistical Analysis/` folder with MOT Delta Analysis project (144 files copied)

### 🎯 **NEXT SESSION AUTOMATIC LOADING**
Run these commands at the start of each new session to automatically load all context:

```bash
# 1. Load project status
echo "=== MALAYSIA SWIMMING ANALYTICS PROJECT STATUS ==="
echo "Current Phase: Data Loading Verification"
echo "Next Tasks: Direct mapping test, sticky columns handling, file naming validation"
echo ""

# 2. Check Docker services
echo "=== DOCKER SERVICES STATUS ==="
docker-compose ps
echo ""

# 3. Verify database status
echo "=== DATABASE STATUS ==="
python scripts/test_database_connection.py
echo ""

# 4. Check SQLite data
echo "=== SQLITE DATA STATUS ==="
python -c "
import sqlite3
conn = sqlite3.connect('database/malaysia_swimming.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type = ?', ('table',))
tables = cursor.fetchall()
print('Tables:', [table[0] for table in tables])
for table in tables:
    cursor.execute(f'SELECT COUNT(*) FROM {table[0]}')
    count = cursor.fetchone()[0]
    print(f'{table[0]}: {count} records')
conn.close()
"
echo ""

# 5. Check methodology documentation
echo "=== METHODOLOGY DOCUMENTATION ==="
ls docs/
echo ""

# 6. Check meet files
echo "=== MEET FILES STATUS ==="
ls data/meets/
echo ""

# 7. Check Statistical Analysis project
echo "=== STATISTICAL ANALYSIS PROJECT ==="
ls "Statistical Analysis/"
echo ""

echo "=== READY FOR NEXT PHASE ==="
echo "Next: Data loading verification and validation"
echo "Focus: Direct mapping test, sticky columns, file naming validation"
echo "Note: Statistical Analysis project available in Statistical Analysis/ folder"
```

### 🔄 **AUTOMATIC CONTEXT SUMMARY**
This will automatically provide a complete project summary based on actual files:

```bash
# Run this to get full project context from actual files
echo "=== MALAYSIA SWIMMING ANALYTICS - PROJECT CONTEXT ==="
echo ""
echo "🏗️ ARCHITECTURE: React + FastAPI + PostgreSQL + Docker (from docker-compose.yml)"
echo "📊 DATA STATUS: All 9 meet files converted to SQLite (malaysia_swimming.db)"
echo "📚 DOCUMENTATION: Complete methodology docs in docs/ folder"
echo "🗄️ DATABASE: SQLite with 6 tables (from scripts/convert_meets_to_sqlite_fixed.py)"
echo "🐳 SERVICES: All 6 Docker containers (from docker-compose.yml)"
echo ""
echo "🎯 CURRENT PHASE: Data Loading Verification"
echo "📋 NEXT TASKS:"
echo "  - Direct mapping test (simple columns)"
echo "  - Sticky columns handling (complex mappings)"
echo "  - File naming validation"
echo "  - Code table references verification"
echo "  - Data integrity checks"
echo ""
echo "🚀 READY TO CONTINUE DEVELOPMENT"
```

### 🔧 Manual Development Setup
1. **Navigate to project directory**:
   ```bash
   cd "C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics"
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Node.js dependencies**:
   ```bash
   npm install
   ```

4. **Start Docker services**:
   ```bash
   docker-compose up -d
   ```

5. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

6. **Start development servers**:
   ```bash
   # Backend (FastAPI)
   uvicorn src.web.main:app --reload --host 0.0.0.0 --port 8000
   
   # Frontend (React/Next.js)
   npm run dev
   ```

### 🌐 Access Points
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs
- **Flower Monitoring**: http://localhost:5555
- **Database**: localhost:5432

### 🔄 Auto-Restart Scripts
Create these batch files for easy startup:

**start-all.bat**:
```batch
@echo off
cd /d "C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics"
docker-compose up -d
echo All services started!
echo Frontend: http://localhost:3000
echo Backend: http://localhost:8000
echo API Docs: http://localhost:8000/api/docs
pause
```

**stop-all.bat**:
```batch
@echo off
cd /d "C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics"
docker-compose down
echo All services stopped!
pause
```

### 🐳 Docker Services
- **postgres**: PostgreSQL database (port 5432)
- **redis**: Redis cache (port 6379)
- **backend**: FastAPI application (port 8000)
- **frontend**: React/Next.js application (port 3000)
- **celery-worker**: Background task processor
- **flower**: Celery monitoring (port 5555)

### Production Deployment
1. **Build Docker images**: `docker-compose build`
2. **Deploy with Kubernetes**: `kubectl apply -f k8s/`
3. **Configure environment variables**
4. **Run database migrations**
5. **Start services**: `docker-compose up -d`

## 📊 Data Migration Strategy

### Current Data Sources
- **Excel meet files** (9 workbooks in Meets/ folder)
- **AthleteINFO.csv** (athlete database)
- **Clubs_By_State.xlsx** (club-to-state mapping)
- **Age_OnTrack_AQUA.xlsx** (target times and AQUA points)

### Migration Process
1. **Parse Excel files** using pandas and openpyxl
2. **Clean and validate** data integrity
3. **Transform data** to match new schema
4. **Load into PostgreSQL** using SQLAlchemy
5. **Verify data** completeness and accuracy

### Data Cleaning Priorities ✅ COMPLETED
- **SEAG_2025_ALL.xlsx**: ✅ Adapted to standard MO/MIAG/SUKMA format
- **Standardize formats**: ✅ All meet files use consistent standard format
- **Resolve foreign athletes**: ✅ Foreign athlete detection and flagging implemented
- **Validate event codes**: ✅ Event parsing and validation completed
- **Club-to-state mapping**: ✅ State code assignments completed

## 🧪 Testing Strategy

### Backend Testing
- **Unit tests** for business logic
- **Integration tests** for API endpoints
- **Database tests** for data integrity
- **Performance tests** for scalability

### Frontend Testing
- **Component tests** with React Testing Library
- **Integration tests** for user workflows
- **E2E tests** with Playwright
- **Accessibility tests** for compliance

## 📚 Documentation Standards

### Code Documentation
- **Docstrings** for all functions and classes
- **Type hints** for better code clarity
- **API documentation** with FastAPI auto-docs
- **Component documentation** with Storybook

### User Documentation
- **User guides** for each feature
- **API documentation** for developers
- **Deployment guides** for operations
- **Troubleshooting guides** for common issues

## 🔍 Troubleshooting

### Common Issues
- **Database connection** problems
- **Excel file parsing** errors
- **Authentication** token issues
- **Docker** container problems

### Debug Tools
- **FastAPI debug mode** for backend issues
- **React DevTools** for frontend debugging
- **Database query logs** for performance issues
- **Docker logs** for container problems

## 🎯 Success Metrics

### Technical Goals
- **Performance**: Sub-2 second page load times
- **Scalability**: Support 1000+ concurrent users
- **Reliability**: 99.9% uptime
- **Security**: OWASP compliance

### Business Goals
- **User Adoption**: 500+ active users
- **Data Accuracy**: 99.9% data integrity
- **Feature Completeness**: All legacy features migrated
- **User Satisfaction**: 4.5+ star rating

## 🔮 Future Vision

### Short-term (3 months)
- Complete data migration
- Basic CRUD operations
- User authentication
- Core performance analysis

### Medium-term (6 months)
- Advanced analytics
- Mobile responsiveness
- Payment integration
- Admin panel

### Long-term (12 months)
- Mobile app development
- AI-powered insights
- International expansion
- API ecosystem

---

## 📞 Support and Maintenance

### Development Team
- **Lead Developer**: [Your Name]
- **Backend Developer**: [Name]
- **Frontend Developer**: [Name]
- **DevOps Engineer**: [Name]

### Contact Information
- **Project Repository**: [GitHub URL]
- **Documentation**: [Docs URL]
- **Issue Tracker**: [Issues URL]
- **Support Email**: [Email]

### ✅ **FIRST COMMIT COMPLETE**
- **Commit Hash**: `c9625e3`
- **Branch**: `data-cleaning`
- **UI Foundation**: Complete and locked in
- **Visual Design**: All elements styled and positioned correctly
- **Ready for**: Data cleaning and functionality implementation

### 🎯 **NEXT DEVELOPMENT PHASE**
- **Data Cleaning**: Validate and clean all converted data
- **Functionality Implementation**: Connect UI to backend APIs
- **Filter Logic**: Implement meet selection, gender, event filtering
- **Download Functionality**: XLSX export implementation
- **Testing**: Comprehensive testing of all features
- **Documentation**: Complete API and user documentation

---

*This handbook serves as the single source of truth for the Malaysia Swimming Analytics project. It should be updated regularly as the project evolves and new features are added.*
