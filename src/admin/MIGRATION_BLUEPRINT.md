# Admin Panel Reorganization - Migration Blueprint

**Status**: Phase 1 - Backend Complete ✓ | Phase 2A - Frontend Reorganization Complete ✓ | Phase 2B - Feature Extraction In Progress
**Date**: 2025-11-19 (Latest Update)
**Risk Level**: LOW - All changes made to existing monolithic admin.tsx without breaking functionality

---

## CURRENT STATE (2025-11-19 - Tab Reorganization Complete)

### Admin Panel Tabs (Updated)
The admin panel now has **5 organized tabs** in `src/pages/admin.tsx`:

1. **Manual Entry** - 3-step wizard for adding swimming results manually
2. **Meet Management** - Upload meet files + manage existing meets (File Upload integrated)
3. **Athlete Management** - Export athletes, search athletes, upload/analyze athlete info
4. **Club Management** - Manage clubs by state
5. **Coach Management** - Manage coaching staff

### Key Changes Made Today
- ✅ Renamed tabs: "Athlete Info" → "Athlete Management", "Club Info" → "Club Management", "Manage Existing Meets" → "Meet Management"
- ✅ Integrated File Upload into Meet Management tab (no longer standalone)
- ✅ Added Coach Management as 5th tab
- ✅ Reorganized Athlete Management to include: Export Athletes, Search Athlete, Upload Workbook, Analysis Results

### Tab-to-Folder Mapping (Target Structure)
```
src/pages/admin.tsx (Orchestrator - stays here for now)
    ↓
src/admin/
├── features/
│   ├── manual-entry/
│   ├── meet-management/
│   │   └── Includes file upload functionality
│   ├── athlete-management/
│   ├── club-management/
│   └── coach-management/
├── shared/
│   ├── hooks/
│   ├── types/
│   ├── components/
│   └── styles/
└── MIGRATION_BLUEPRINT.md (this file)
```

---

## PHASE 1 COMPLETION SUMMARY (2025-11-19)

### What Was Done
✓ Created 7 compatibility router files in `src/admin/api-routers/`:
  - `auth_router.py`, `athlete_router.py`, `club_router.py`, `coach_router.py`
  - `meet_router.py`, `upload_router.py`, `manual_entry_router.py`

✓ Resolved critical missing endpoint issue:
  - Created `POST /admin/manual-results` endpoint (admin.py lines 2318-2421)
  - Added ManualResult and ManualResultsSubmission Pydantic models
  - Endpoint tested and working - successfully creates meets and inserts results

✓ Created Python package structure:
  - `src/__init__.py`, `src/web/__init__.py`, `src/admin/__init__.py`
  - `src/admin/api-routers/__init__.py`

✓ Verified all endpoints working:
  - Health check: `GET /health` ✓
  - Meets: `GET /api/admin/meets` ✓
  - Athletes: `GET /api/admin/athletes/search` ✓
  - Manual results: `POST /api/admin/manual-results` ✓

### Implementation Approach (Deviated from Original Plan)
**Original Plan**: Use separate routers in api-routers/ folder registered individually
**Actual Implementation**: Kept original admin.router structure
- **Reason**: Module import issues with uvicorn's reload mechanism
- **Benefit**: Simplicity - all endpoints work without importing separate modules
- **Compatibility routers**: Created as planned for future incremental extraction
- **No regression**: All existing functionality preserved

### Files Created/Modified
**Created**:
- 7 router compatibility files (can be used for future extraction)
- 4 __init__.py files for package structure
- Updated MIGRATION_BLUEPRINT.md with progress

**Modified**:
- `src/web/routers/admin.py`: Added manual-results endpoint and models
- `src/web/main.py`: Updated to latest version (imports admin router)

---

## CRITICAL FINDINGS FROM CODE ANALYSIS

### ✓ RESOLVED: Missing Backend Endpoint
**Status**: COMPLETED - `POST /api/admin/manual-results` endpoint created and tested
- Added to `src/web/routers/admin.py` (Lines 2318-2421)
- Pydantic models added (ManualResult, ManualResultsSubmission)
- Tested successfully: Creates meets, validates athletes, inserts results
- Returns: success, meet_id, results_inserted, error list

### ⚠️ TIGHT COUPLING ISSUES
1. **Club-Coach Relationship**: Coach management depends on club selection (must load coaches after club selected)
2. **State-Club Relationship**: Club list depends on state being selected first
3. **Auth Required Everywhere**: All tabs require authentication state from parent

### ✓ SHAREABLE STATE
These can be safely isolated in feature components:
- manualStep, selectedAthletes, athleteSearchQuery (manual-entry)
- meets, editingAlias (meet-management)
- states, clubs, selectedClub (club-management)
- coaches, selectedCoach (coach-management)
- coachFormData, clubFormData (separate feature state)

### ✓ MUST STAY IN ORCHESTRATOR (admin.tsx)
These must remain because all tabs need them:
- isAuthenticated, password, error (authentication shared across all)
- API_BASE (used by all features)
- useRouter from Next.js

---

## FEATURE EXTRACTION PLAN

### How to Use This Guide When Extracting Features

**When working on a specific tab/feature:**
1. Find the feature section below (e.g., "FEATURE 1: ATHLETE-MANAGEMENT")
2. Look at "Source Code Locations" - this tells you what code in admin.tsx belongs to this feature
3. Look at "Files to Create" - this tells you what to create in the feature folder
4. Move/extract the code from admin.tsx to the feature folder files
5. Update imports in admin.tsx to import from the feature component instead

---

### FEATURE 1: ATHLETE-MANAGEMENT

**Current Tab Implementation**: `src/pages/admin.tsx` lines 2048-2222 (activeTab === 'athleteinfo')

**What's in This Feature**:
- 🔍 Export All Athletes section - Download Excel with athlete ID, name, birthdate
- 🔍 Search Athlete section - Search by name with live results display
- 📤 Upload Athlete Info Workbook - Upload Excel file for analysis
- 📊 Workbook Analysis Results - Display analysis of uploaded files

**Code to Extract from admin.tsx:**
```
Frontend State Variables (lines ~108-107):
- athleteSearchQuery
- athleteSearchResults
- searchingAthletes
- athleteInfoUploading
- athleteInfoAnalysis
- athleteInfoMessage

Frontend Functions (lines ~127-143):
- searchAthletes() - Fetches athletes from API
- handleAthleteInfoUpload() - Uploads athlete workbook
- useEffect for athleteinfo tab

Frontend JSX (lines 2048-2222):
- Export All Athletes button with fetch logic
- Search input and results display
- File upload input and upload button
- Workbook analysis results display
```

**Files to Create in `src/admin/features/athlete-management/`:**
- `athlete-management.tsx` - Main component combining all 4 sections
- `api.ts` - Wrap API calls:
  - `fetchAthletesExcel()` - GET /api/admin/athletes/export-excel
  - `searchAthletes(query)` - GET /api/admin/athletes/search
  - `uploadAthleteWorkbook(file)` - POST with file upload
- `types.ts` - TypeScript interfaces if needed
- `README.md` - Feature documentation
- `index.ts` - Export main component

**Backend Endpoints Already Available:**
- ✅ GET /api/admin/athletes/search
- ✅ GET /api/admin/athletes/export-excel
- ✅ POST /api/admin/analyze-athlete-info (for workbook analysis)
- ✅ GET /api/admin/athletes/{athlete_id}
- ✅ PATCH /api/admin/athletes/{athlete_id}

**Next Steps When Extracting**:
1. Create folder: `src/admin/features/athlete-management/`
2. Create the files listed above
3. Copy the JSX from lines 2048-2222 into `athlete-management.tsx`
4. Extract state variables and functions into their own hooks/files
5. Create API wrapper functions in `api.ts`
6. Import component in admin.tsx instead of inline JSX

---

### FEATURE 2: MEET-MANAGEMENT (Includes File Upload)

**Current Tab Implementation**: `src/pages/admin.tsx` lines 1467-2047 (activeTab === 'manage')

**What's in This Feature**:
- 📤 Upload Meet Files - File selection and upload form
- 📊 Recent Uploads section - Shows upload status and metrics
- 🗂️ Manage Existing Meets - Table with edit alias, delete, view PDF

**Code to Extract from admin.tsx:**
```
Frontend State Variables (lines ~92-97):
- uploading, uploadedFiles, conversionResult
- uploadSummaries, expandedIssueKeys
- meets, loadingMeets, editingAlias

Frontend Functions (lines ~various):
- handleFileSelect() - File selection
- handleUpload() - Submit file upload
- handleRemoveFile() - Remove from upload list
- fetchMeets() - Load meets table
- handleUpdateAlias() - Edit meet alias
- handleDeleteMeet() - Delete meet
- useEffect hooks for meet tab

Frontend JSX (lines 1467-2047):
- File upload section with form
- Upload summaries display
- Existing meets table with actions
```

**Files to Create in `src/admin/features/meet-management/`:**
- `meet-management.tsx` - Main component
- `upload-section.tsx` - File upload form sub-component
- `upload-summaries.tsx` - Upload status display sub-component
- `meets-table.tsx` - Existing meets table sub-component
- `api.ts` - API calls:
  - `uploadMeetFiles(files)` - POST /api/admin/convert-excel
  - `fetchMeets()` - GET /api/admin/meets
  - `updateMeetAlias(meetId, alias)` - PUT /api/admin/meets/{id}/alias
  - `deleteMeet(meetId)` - DELETE /api/admin/meets/{id}
  - `getMeetPDF(meetId)` - GET /api/admin/meets/{id}/pdf
- `types.ts` - TypeScript interfaces
- `README.md` - Feature documentation
- `index.ts` - Export main component

**Backend Endpoints Already Available:**
- ✅ GET /api/admin/meets
- ✅ POST /api/admin/convert-excel (for meet file upload)
- ✅ PUT /api/admin/meets/{meet_id}/alias
- ✅ DELETE /api/admin/meets/{meet_id}
- ✅ GET /api/admin/meets/{meet_id}/pdf

**Next Steps When Extracting**:
1. Create folder: `src/admin/features/meet-management/`
2. Create the files listed above
3. Copy the JSX from lines 1467-2047 into main component
4. Break into sub-components (upload, summaries, table)
5. Extract state and functions
6. Create API wrapper in `api.ts`
7. Import component in admin.tsx

---

### FEATURE 3: CLUB-MANAGEMENT

**Current Tab Implementation**: `src/pages/admin.tsx` lines 2224-2289 (activeTab === 'clubinfo')

**What's in This Feature**:
- 🏢 State/Club Selection - Dropdown to select state, then clubs
- 📝 Club Upload Form - Upload Clubs_By_State.xlsx file
- 📊 Upload Results - Show analysis of uploaded clubs

**Code to Extract from admin.tsx:**
```
Frontend State Variables (lines ~102-107):
- clubUploading, clubResult, clubUploadMessage

Frontend Functions (lines ~various):
- handleClubUpload() - Upload club file
- useEffect for clubinfo tab

Frontend JSX (lines 2224-2289):
- Club upload section
- File input and upload button
- Upload results display
```

**Files to Create in `src/admin/features/club-management/`:**
- `club-management.tsx` - Main component
- `upload-section.tsx` - Club file upload sub-component
- `api.ts` - API calls:
  - `uploadClubsFile(file)` - POST /api/admin/convert-clubs
  - `getStates()` - GET /api/admin/clubs/states
  - `getClubs(state)` - GET /api/admin/clubs?state=
- `types.ts` - TypeScript interfaces
- `README.md` - Feature documentation
- `index.ts` - Export main component

**Backend Endpoints Already Available:**
- ✅ POST /api/admin/convert-clubs (for club file upload)
- ✅ GET /api/admin/clubs/states
- ✅ GET /api/admin/clubs
- ✅ POST /api/admin/clubs
- ✅ PUT /api/admin/clubs/{club_name}

**Next Steps When Extracting**:
1. Create folder: `src/admin/features/club-management/`
2. Create the files listed above
3. Copy the JSX from lines 2224-2289 into main component
4. Extract state and functions
5. Create API wrapper in `api.ts`
6. Import component in admin.tsx

---

### FEATURE 4: COACH-MANAGEMENT (NEW TAB)

**Current Tab Implementation**: `src/pages/admin.tsx` lines 2291-2300 (activeTab === 'coachmanagement')

**What's in This Feature**:
- 👨‍🏫 Coach Management - Placeholder for future coach management features
- Currently displays: "Coach management interface coming soon"
- Ready for expansion with coach CRUD operations

**Code to Extract from admin.tsx:**
```
Frontend State Variables (will need to add):
- coaches (list of coaches)
- selectedCoach
- coachFormData (for create/edit)
- coachFormMode ('view', 'create', 'edit')

Frontend Functions (will need to add):
- fetchCoaches() - Get list of coaches
- handleCoachSubmit() - Create/update coach
- handleCoachDelete() - Delete coach
- handleCoachSearch() - Search coaches

Frontend JSX (lines 2291-2300):
- Currently just placeholder text
```

**Files to Create in `src/admin/features/coach-management/`:**
- `coach-management.tsx` - Main component (can expand from placeholder)
- `coach-list.tsx` - List of coaches sub-component
- `coach-form.tsx` - Add/Edit coach form sub-component
- `api.ts` - API calls:
  - `fetchCoaches(filters)` - GET /api/admin/coaches
  - `createCoach(data)` - POST /api/admin/coaches
  - `updateCoach(id, data)` - PUT /api/admin/coaches/{id}
  - `deleteCoach(id)` - DELETE /api/admin/coaches/{id}
- `types.ts` - TypeScript interfaces
- `README.md` - Feature documentation
- `index.ts` - Export main component

**Backend Endpoints Already Available:**
- ✅ GET /api/admin/coaches
- ✅ POST /api/admin/coaches
- ✅ PUT /api/admin/coaches/{coach_id}
- ✅ DELETE /api/admin/coaches/{coach_id}

**Next Steps When Extracting**:
1. Create folder: `src/admin/features/coach-management/`
2. Create the files listed above
3. Replace placeholder text in lines 2291-2300 with actual coach UI
4. Implement coach list, create/edit form
5. Create API wrapper in `api.ts`
6. Import component in admin.tsx

---

### FEATURE 5: MANUAL-ENTRY (Standalone Tab)

**Current Tab Implementation**: `src/pages/admin.tsx` lines 1093-1466 (activeTab === 'manual')

**What's in This Feature**:
- 📝 Step 1 - Select Athletes - Search and add athletes to the entry
- 📝 Step 2 - Meet Information - Enter meet name, date, location
- 📝 Step 3 - Enter Times - Input results for selected athletes
- ✅ Full 3-step wizard for manual result entry

**Code to Extract from admin.tsx:**
```
Frontend State Variables (lines ~86-99):
- manualStep (1, 2, or 3)
- selectedAthletes, athleteSearchQuery, athleteSearchResults, searchingAthletes
- meetName, meetDate, meetCity, meetCourse, meetAlias
- selectedEvents, manualResults

Frontend Functions (lines ~various):
- searchAthletes() - Shared pattern with athlete-management
- handleAddAthlete() - Add athlete to selection
- handleRemoveAthlete() - Remove athlete
- handleEventChange() - Track selected events
- handleResultChange() - Update result times
- handleNextToStep2() - Move to step 2
- handleNextToStep3() - Move to step 3
- handleSubmitManualResults() - Submit all data
- handleRestart() - Reset wizard

Frontend JSX (lines 1093-1466):
- Step 1: Athlete search and selection list
- Step 2: Meet info form (name, date, city, course, alias)
- Step 3: Event selection and result time entry
```

**Files to Create in `src/admin/features/manual-entry/`:**
- `manual-entry.tsx` - Main component orchestrating 3 steps
- `step1-athletes.tsx` - Athlete selection step sub-component
- `step2-meet-info.tsx` - Meet information step sub-component
- `step3-results.tsx` - Result entry step sub-component
- `api.ts` - API calls:
  - `searchAthletes(query)` - GET /api/admin/athletes/search
  - `submitManualResults(data)` - POST /api/admin/manual-results
- `types.ts` - TypeScript interfaces (ManualResult, ManualResultsSubmission)
- `README.md` - Feature documentation
- `index.ts` - Export main component

**Backend Endpoints Already Available:**
- ✅ GET /api/admin/athletes/search (for athlete selection)
- ✅ POST /api/admin/manual-results (added in Phase 1 - lines 2318-2421 in admin.py)
- ✅ Returns: success, meet_id, results_inserted, error list

**Next Steps When Extracting**:
1. Create folder: `src/admin/features/manual-entry/`
2. Create the files listed above
3. Copy the JSX from lines 1093-1466 into main component
4. Break into 3 step sub-components
5. Extract state variables and step navigation functions
6. Create API wrapper in `api.ts`
7. Update import in admin.tsx to use component instead of inline JSX
8. Test 3-step wizard thoroughly

---

### FEATURE 6: AUTHENTICATION (Stays in Orchestrator)

**Current Implementation**: `src/pages/admin.tsx` lines 1-100 (login screen + shared state)

**What's in This Feature**:
- 🔐 Login Form - Password authentication
- 🔐 Error Display - Authentication error messages
- 🔐 Auth State Management - isAuthenticated flag used by all tabs
- 🔐 Logout Button - Clear auth session

**Why This Stays in admin.tsx**:
Authentication is required by ALL features - it cannot be extracted to a feature folder because:
1. All 5 feature tabs depend on the `isAuthenticated` state
2. The orchestrator itself needs authentication to show/hide content
3. Authentication affects the entire app's visibility

**Code to Keep in admin.tsx:**
```
Frontend State (keeps these):
- isAuthenticated (boolean)
- password (string from login form)
- error (authentication error message)

Frontend Functions (keep these):
- handleLogin() - POST to /api/admin/authenticate
- handleLogout() - Clear auth state

Frontend JSX (keep this):
- Login screen when not authenticated
- Logout button in header when authenticated
```

**Backend Endpoint Already Available:**
- ✅ POST /api/admin/authenticate (expects password, returns success boolean)

**Next Steps**:
- Do NOT extract authentication - leave in orchestrator
- All other features will receive `isAuthenticated` prop from parent
- Each feature can independently validate auth status

---

## SHARED CODE (NEW FILES)

### Shared Hooks
```
src/admin/shared/hooks/
├── useAdminAuth.ts - Manage isAuthenticated, password, error
├── useFetch.ts - Wrapper around fetch with error handling
└── useNotification.ts - Handle success/error messages
```

### Shared Types
```
src/admin/shared/types/
├── admin.ts - All TypeScript interfaces (Athlete, Club, Coach, Meet, etc.)
└── api.ts - API response types
```

### Shared Components
```
src/admin/shared/components/
├── Button.tsx - Reusable button
├── Modal.tsx - Reusable modal
├── SearchBox.tsx - Reusable search input
├── DataTable.tsx - Reusable data table
├── AlertBox.tsx - Success/error alerts
└── LoadingSpinner.tsx - Loading indicator
```

### Shared Styles
```
src/admin/shared/styles/
├── theme.ts - Colors (#cc0000), spacing, button styles
└── colors.ts - Color definitions
```

---

## IMPORT DEPENDENCY GRAPH (Current + Target)

**CURRENT STATE (Monolithic)**:
```
src/pages/admin.tsx
├── Imports: React, useState, useEffect
├── Imports: Next.js router (for query params)
└── Contains: All 5 tabs + login logic (2,206 lines)
    ├── Manual Entry (lines 1093-1466)
    ├── Meet Management (lines 1467-2047)
    ├── Athlete Management (lines 2048-2222)
    ├── Club Management (lines 2224-2289)
    └── Coach Management (lines 2291-2300)

src/web/routers/admin.py
└── Contains: All backend endpoints (POST /api/admin/manual-results added)
```

**TARGET STATE (Modular)**:
```
src/pages/admin.tsx (Orchestrator - stays but shrinks)
├── Imports: ManualEntry from features/manual-entry
├── Imports: MeetManagement from features/meet-management
├── Imports: AthleteManagement from features/athlete-management
├── Imports: ClubManagement from features/club-management
├── Imports: CoachManagement from features/coach-management
└── Renders: Tab UI + passes isAuthenticated to features

Each Feature Component (e.g., src/admin/features/manual-entry/manual-entry.tsx)
├── Imports: API functions from ./api.ts
├── Imports: Types from src/admin/shared/types/admin.ts
├── Imports: Hooks from src/admin/shared/hooks/
├── Imports: Components from src/admin/shared/components/
├── Manages: Own feature state (manualStep, selectedAthletes, etc.)
├── Props: { isAuthenticated: boolean }
└── Does NOT import other features

Shared Code (src/admin/shared/*)
├── hooks/ - useAdminAuth, useFetch, useNotification
├── types/ - Athlete, Club, Coach, Meet, Result interfaces
├── components/ - Button, Modal, SearchBox, AlertBox, DataTable
└── styles/ - Colors, theme definitions

Backend Routing (src/web/routers/admin.py - STAYS MONOLITHIC)
├── All endpoints remain in one file
├── No routing extraction needed (works well)
└── Each feature component calls endpoints via fetch()
```

---

## FILES TO DELETE (After Extraction)

```
OPTIONAL - These can be deleted after feature extraction complete:
- Inline JSX from src/pages/admin.tsx (once moved to feature files)
- Old state variables from main admin.tsx (once moved to feature hooks)

DO NOT DELETE:
- src/pages/admin.tsx itself (becomes smaller but stays)
- src/web/routers/admin.py (backend is fine here)
```

---

## TESTING CHECKLIST

After each feature extraction, verify:

**Authentication**:
- [ ] Login screen appears and accepts password
- [ ] Invalid password shows error message
- [ ] Logout button appears in header when authenticated
- [ ] Logout clears authentication and shows login screen

**Manual Entry Tab**:
- [ ] Step 1: Athlete search works and results display
- [ ] Step 1: Can add/remove athletes from selection
- [ ] Step 2: Can enter meet name, date, city, course, alias
- [ ] Step 3: Event selection and time entry work
- [ ] Step 3: Submit creates meet and inserts results

**Meet Management Tab**:
- [ ] File upload form displays
- [ ] Can select and upload meet files
- [ ] Upload shows success/error status
- [ ] Existing meets table loads with all columns
- [ ] Edit alias, delete, and PDF download buttons work

**Athlete Management Tab**:
- [ ] Export All Athletes button downloads Excel file
- [ ] Athlete search works with live results
- [ ] Upload Workbook file input and submit button work
- [ ] Analysis results display after upload

**Club Management Tab**:
- [ ] States dropdown loads all states
- [ ] Club list updates when state selected
- [ ] Club file upload works

**Coach Management Tab**:
- [ ] Tab loads without errors
- [ ] (Will implement CRUD when building feature)

**General**:
- [ ] No console errors in browser DevTools
- [ ] No API error responses (check Network tab)
- [ ] All /api/admin/* endpoints return expected data

---

## EXECUTION ORDER & PROGRESS

### Phase 1: Backend Setup (COMPLETE ✓)
1. ✓ Create folder structure (`src/admin/features/`, `shared/`, `api-routers/`)
2. ✓ Create compatibility layer routers (7 files in `src/admin/api-routers/`)
3. ✓ Add missing `/admin/manual-results` endpoint to `admin.py` (lines 2318-2421)
4. ✓ Create Python package `__init__.py` files (src/, src/web/, src/admin/, api-routers/)
5. ✓ Test all backend endpoints - all working

**NOTE**: Attempted to use separate `manual_entry_router.py` but encountered module import issues in uvicorn. Solution: Added endpoint directly to existing admin.py instead. The compatibility layer routers remain for future incremental extraction.

### Phase 2A: Frontend Tab Reorganization (COMPLETE ✓)
6. ✓ Renamed tabs: "Athlete Info" → "Athlete Management", "Club Info" → "Club Management", "Manage Existing Meets" → "Meet Management"
7. ✓ Integrated File Upload into Meet Management tab (removed standalone upload tab)
8. ✓ Added Coach Management as 5th tab
9. ✓ Reorganized Athlete Management to include 4 sections: Export Athletes, Search Athlete, Upload Workbook, Analysis Results
10. ✓ Updated MIGRATION_BLUEPRINT.md with accurate feature extraction guides

**RESULT**: Admin panel now has 5 organized tabs with clear feature boundaries, ready for incremental extraction.

### Phase 2B: Feature Extraction (NOT YET STARTED)
11. → Create shared infrastructure (`src/admin/shared/types/admin.ts`, hooks/, components/)
12. → Extract FEATURE 1: Athlete Management (lines 2048-2222 → src/admin/features/athlete-management/)
13. → Extract FEATURE 2: Meet Management (lines 1467-2047 → src/admin/features/meet-management/)
14. → Extract FEATURE 3: Club Management (lines 2224-2289 → src/admin/features/club-management/)
15. → Extract FEATURE 4: Coach Management (lines 2291-2300 → src/admin/features/coach-management/)
16. → Extract FEATURE 5: Manual Entry (lines 1093-1466 → src/admin/features/manual-entry/)
17. → Update src/pages/admin.tsx to import features instead of inline JSX
18. → Test each feature thoroughly using TESTING CHECKLIST
19. → Consider deleting extracted code from admin.tsx once features are stable

### Phase 3: Incremental Router Extraction (FUTURE - Optional)
- Extract router code from compatibility layer wrappers into individual feature routers (non-blocking)
- Keep src/web/routers/admin.py as-is for now (simpler, works well)

---

## KNOWN RISKS

1. **Large refactoring** - Many import paths will change (but files are well-organized now)
2. **Tight coupling** - Some state shared between tabs:
   - Club selection affects coach list
   - State selection affects club list
   - Athlete search used by multiple tabs
3. **File paths** - Python relative imports must be updated carefully
4. **No existing tests** - Can't run automated tests to verify changes
5. **Manual Entry** - Relies on POST /api/admin/manual-results which exists and is tested ✓

---

## ROLLBACK PLAN

If something breaks:
1. Use `git diff` to see all changes
2. Restore from git if needed
3. Extract features incrementally instead of all at once

