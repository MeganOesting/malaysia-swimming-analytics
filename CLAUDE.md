# CLAUDE.md - Development Protocols & Standards

## **NO UNICODE CHARACTERS IN CODE** - CRITICAL

**This is a Windows environment using cp1252 encoding.**

**DO NOT** add Unicode symbols to Python code, including:
- Checkmarks: (check symbols)
- X marks: (x symbols)
- Warning signs: (warning symbols)
- Emojis of any kind
- Any non-ASCII characters in print statements or string literals

**USE ASCII alternatives instead:**
- `[OK]` or `OK` instead of checkmarks
- `[ERROR]` or `ERROR` instead of X marks
- `[WARNING]` or `WARNING` instead of warning symbols
- Plain text descriptions, no decorative symbols

**Why:** Windows console cp1252 encoding cannot display these characters, causing `UnicodeEncodeError` crashes. Adding them and then removing them wastes time and tokens.

---

## **DATABASE DATE HANDLING PROTOCOL** � CRITICAL

### **Standard Date Format: ISO 8601 with UTC Timezone**

```
YYYY-MM-DDTHH:MM:SSZ
Example: 2025-02-20T00:00:00Z
```

### **Date Fields in Database:**
- `meets.meet_date`
- `athletes.BIRTHDATE`
- `athletes.passport_expiry_date`
- `records.record_date`
- `aqua_base_times.effective_date`
- Any future date fields MUST follow this protocol

### **Date Normalization**

Dates are normalized using `normalize_birthdate()` in `scripts/convert_meets_to_sqlite_simple.py`:
- This function handles ALL input formats (Excel datetime, ISO 8601, dot-separated, etc.)
- Output is always ISO 8601 format
- **Normalize dates AT THE SOURCE** when reading from Excel, not downstream

---

## **GLOBAL UTILITIES - DO NOT REWRITE**

These utilities are the **SINGLE SOURCE OF TRUTH**. Use them everywhere - DO NOT create duplicate logic.

### **Name Matching**
- **File:** `src/web/utils/name_matcher.py`
- **Function:** `match_athlete_by_name(conn, fullname, gender, birthdate)`
- Handles: word-based matching, nickname expansion, birthdate swapping, single-word identifiers

### **Foreign Athlete Detection**
- **File:** `src/web/utils/foreign_detection.py`
- **Function:** `is_likely_foreign(excel_nation, club_name, full_name)`
- Handles: international school patterns, foreign club patterns, nation checking

### **Athlete Lookup (combines both)**
- **File:** `src/web/utils/athlete_lookup.py`
- **Function:** `find_athlete_ids(conn, fullname, birthdate, gender, nation, club_name)`
- Searches both `athletes` and `foreign_athletes` tables using the global name matcher

**RULE:** If you need matching or foreign detection logic, IMPORT from these files. Never rewrite.

---

## **POOL COURSE & EVENT TRACKING**

### **Course Types:**
- **LCM** (Long Course Meters) - 50m pool - Default for most meets
- **SCM** (Short Course Meters) - 25m pool - Splash meets, some indoor meets

### **SCM Meets:**
Splash series meets are held in 25m pools (SCM):
- Meet alias pattern: `SPL*` (e.g., SPLSEL25, SPLPRK25)
- Results must have `meet_course = 'SCM'`
- Event IDs must use `SCM_` prefix (e.g., `SCM_Free_100_M`)

### **25m Events - NOT TRACKED:**
We do **NOT** track 25m distance events (25 Free, 25 Back, etc.):
- These are training/development events, not standard competition events
- No base times exist for MAP/AQUA/MOT calculations
- If encountered in uploads, skip these events

### **Event ID Format:**
```
{COURSE}_{STROKE}_{DISTANCE}_{GENDER}
Examples:
- LCM_Free_100_M (Long Course, 100m Freestyle, Male)
- SCM_Back_200_F (Short Course, 200m Backstroke, Female)
```

---

## **Other Standards**

### **Meet Codes:**
- Meet codes are stored in `meets.meet_type` column in database
- DO NOT hardcode meet code mappings in Python
- Query the database directly: `SELECT meet_type FROM meets WHERE id = ?`

### **Database Health:**
- Date format violations = **DATA QUALITY ALERT**
- If you see `[DATE FORMAT VIOLATION]` in logs, find and fix the process that loaded those dates
- Database consistency is PRIMARY

---

## **UI/UX STYLING STANDARDS**

### **Admin Panel Styling - Match Main Page Design**

All admin panel components MUST use consistent styling from the main page filter interface. Reference: `src/pages/index.tsx` filter section.

#### **1. Radio Button Groups (Type Selector)**
**Appearance:** "Results: ○ Show all times ○ Show best times only" style
**Use for:** Binary/multi-choice selections (e.g., file upload type selector)
```
File Type Selection:
○ SwimRankings.net Download
○ SEA Age Group Championships

Implementation:
- Display as horizontal radio button row
- Label with bold text before the options
- Use default HTML radio buttons (styled)
- Gray text, no special styling
```

#### **2. Checkbox Grids**
**Appearance:** Multi-column grid of checkboxes (like Meets: ☐ SEAG25 ☐ MALAYS ☐ VIRTUS...)
**Use for:** Multi-select lists (e.g., filter meets, select events)
```
Meets:
☐ SEAG25  ☐ MALAYS  ☐ VIRTUS  ☐ WORLD
☐ AP RAC  ☐ 53_IN   ☐ 4TH SP  ☐ SPORTE

Implementation:
- Wrap in flexbox grid (2-4 columns)
- Use standard checkboxes
- Compact spacing
```

#### **3. Action Buttons**
**Appearance:** Red boxes at bottom (Apply Selection, Download XLSX, Reset Filters)
**Use for:** Primary actions (upload, apply filters, submit)
```
Style Reference:
- backgroundColor: #cc0000 (red)
- color: white
- padding: ~10px 20px
- border: none
- borderRadius: 4px
- fontWeight: bold
- fontSize: 14px
- cursor: pointer

Disabled state: backgroundColor: #9ca3af (gray)
```

#### **Important Notes:**
- DO NOT use custom styled components for these elements
- Keep styling consistent across ALL admin tabs
- When creating new admin features, reference this standard
- Update this section if adding NEW standard UI patterns

---

## **ADMIN COMPONENT ARCHITECTURE**

### **Overview**
The admin panel uses a **modular feature-based architecture** instead of a monolithic component.

### **Directory Structure**
```
src/admin/
├── admin.tsx                          # Main orchestrator component
├── shared/                            # Code shared across features
│   ├── components/
│   │   ├── Button.tsx
│   │   ├── SearchBox.tsx
│   │   ├── AlertBox.tsx
│   │   └── Modal.tsx
│   ├── hooks/
│   │   ├── useAdminAuth.ts           # Authentication
│   │   ├── useNotification.ts        # Notifications/alerts
│   │   └── [other shared hooks]
│   └── types/
│       └── admin.ts                  # Shared TypeScript types
├── features/
│   ├── athlete-management/
│   │   ├── athlete-management.tsx    # Main component
│   │   ├── api.ts                    # API calls
│   │   ├── types.ts                  # Feature-specific types
│   │   └── index.ts                  # Exports
│   ├── meet-management/
│   ├── manual-entry/
│   ├── club-management/
│   ├── coach-management/
│   └── file-upload/
└── pages/
    └── admin.tsx                     # Next.js page (re-exports admin.tsx)
```

### **Creating a New Admin Feature**

**Step 1: Create Feature Directory**
```bash
mkdir -p src/admin/features/your-feature-name
```

**Step 2: Create Core Files**

**your-feature.tsx** (Main component)
```typescript
import React, { useState } from 'react';
import { Button, AlertBox } from '../../shared/components';
import { useNotification } from '../../shared/hooks';
import * as api from './api';

export interface YourFeatureProps {
  isAuthenticated: boolean;
}

export const YourFeature: React.FC<YourFeatureProps> = ({ isAuthenticated }) => {
  const { notifications, success, error, clear } = useNotification();
  const [loading, setLoading] = useState(false);

  // Component logic here...

  return (
    <div>
      {/* Render notifications */}
      {notifications.map(notification => (
        <AlertBox
          key={notification.id}
          type={notification.type}
          message={notification.message}
          onClose={() => clear(notification.id)}
        />
      ))}

      {/* Feature UI here */}
    </div>
  );
};
```

**api.ts** (API calls)
```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

export async function fetchData(query: string): Promise<any[]> {
  const response = await fetch(`${API_BASE}/api/your-endpoint?q=${query}`);
  if (!response.ok) throw new Error('Failed to fetch data');
  return response.json();
}
```

**types.ts** (TypeScript types)
```typescript
export interface YourFeatureData {
  id: string;
  name: string;
  // ... other fields
}
```

**index.ts** (Exports)
```typescript
export { YourFeature } from './your-feature';
export * from './types';
```

**Step 3: Register in Orchestrator**

Update `src/admin/admin.tsx`:
```typescript
import { YourFeature } from './features/your-feature-name';

const TABS: TabConfig[] = [
  // ... existing tabs
  {
    id: 'yourfeature',
    label: 'Your Feature',
    icon: '🎯',
    component: YourFeature,
  },
];
```

### **Best Practices**

1. **Keep Features Self-Contained**
   - All feature code lives in `features/[feature-name]/`
   - Use shared components from `shared/` for UI
   - Don't import from other features

2. **Use Shared Utilities**
   - Always import hooks from `shared/hooks/`
   - Always import components from `shared/components/`
   - Always use shared types from `shared/types/`

3. **Error Handling**
   - Use `useNotification()` hook for all errors
   - Catch API errors and display via `error(message)`
   - Log errors to console for debugging

4. **Styling**
   - Use Tailwind CSS for styling
   - Red buttons: `backgroundColor: #cc0000` (via Button component)
   - Match the UI/UX standards in this document

5. **Authentication**
   - All features receive `isAuthenticated` prop
   - Check prop before rendering sensitive data
   - Authentication is handled in `admin.tsx`

6. **API Integration**
   - Isolate all API calls in `api.ts`
   - Use TypeScript types for all API responses
   - Handle errors gracefully

---

## **FOREIGN ATHLETE HANDLING** — CRITICAL

### **Overview**
Foreign athletes (non-Malaysian swimmers competing at local meets) are stored in a **separate table** from Malaysian athletes. This keeps the Malaysian athlete database clean for development tracking and national team selection purposes.

### **Two-Table System**

| Table | Purpose | Who Goes Here |
|-------|---------|---------------|
| `athletes` | Malaysian registered swimmers | nation = 'MAS', tracked for development |
| `foreign_athletes` | Foreign competitors | nation != 'MAS', compete at local meets |

### **Results Table Linkage**

The `results` table has **two athlete ID columns**:

```sql
results.athlete_id          -- References athletes.id (Malaysian swimmers)
results.foreign_athlete_id  -- References foreign_athletes.id (Foreign swimmers)
results.nation              -- 'MAS' or foreign country code (MGL, SGP, INA, etc.)
```

**Rules:**
- If `nation = 'MAS'`: Use `athlete_id`, leave `foreign_athlete_id` NULL
- If `nation != 'MAS'`: Use `foreign_athlete_id`, leave `athlete_id` NULL
- **NEVER** put a foreign athlete ID in `athlete_id` column
- **NEVER** put a Malaysian athlete ID in `foreign_athlete_id` column

### **Result Status Field**

The `results` table has a `result_status` column for tracking non-OK results:

```sql
results.result_status  -- TEXT, values: 'OK', 'DQ', 'DNS', 'DNF', 'SCR'
results.comp_place     -- INTEGER, competition placing (1, 2, 3...)
```

**Status Values:**
| Status | Meaning | Time | Place | Points |
|--------|---------|------|-------|--------|
| OK | Normal result | Required | Optional | Calculated |
| DQ | Disqualified | NULL | NULL | NULL |
| DNS | Did Not Start | NULL | NULL | NULL |
| DNF | Did Not Finish | NULL | NULL | NULL |
| SCR | Scratched | NULL | NULL | NULL |

**Rules:**
- DQ/DNS/DNF/SCR results have NULL time_string, time_seconds, aqua_points, rudolph_points
- Main page displays result_status in Place column when comp_place is NULL and status != OK
- Sort order: numeric places (1,2,3...) first, then DQ, DNS, DNF, SCR at bottom
- SwimRankings "Place" column is RANKING (not comp_place) - do NOT import to comp_place
- SEA Age/SEAG results have real comp_place values from competition

**Edit Results Modal:**
- Enter number (1, 2, 3...) -> saves to comp_place, sets status to OK
- Enter text (DQ, DNS, DNF, SCR) -> saves to result_status, clears comp_place and time

### **Foreign Athletes Table Schema**

```sql
CREATE TABLE foreign_athletes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fullname TEXT NOT NULL,
    birthdate TEXT,           -- ISO format YYYY-MM-DDTHH:MM:SSZ
    gender TEXT,              -- M/F
    nation TEXT,              -- 3-letter code (MGL, SGP, INA, HKG, etc.)
    club_code TEXT,           -- if known
    club_name TEXT,           -- from results file
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### **Upload Function Logic — IMPORTANT**

When processing results files, use `find_athlete_ids()` from `src/web/utils/athlete_lookup.py`:

```python
from src.web.utils.athlete_lookup import find_athlete_ids, AthleteMatch

# For each result row:
match = find_athlete_ids(conn, fullname, birthdate, gender, nation_from_results, club_name)

# Use the returned values:
result.athlete_id = match.athlete_id
result.foreign_athlete_id = match.foreign_athlete_id
result.nation = match.nation  # IMPORTANT: Use this, not results file nation!

# Check match.source to understand what happened:
# - 'athletes': Found in athletes table (registered swimmer)
# - 'foreign_athletes': Found in foreign_athletes table (known foreign competitor)
# - 'unmatched': Not found - requires manual review before adding
```

**SEARCH ORDER (Critical!):**

```
Step 1: Search athletes table FIRST
        (includes registered foreign residents like SGP kid at ISKL)
        ↓
        Found? → Use athlete_id, nation from athletes.nation
        ↓
        Not found → Continue to Step 2

Step 2: Search foreign_athletes table
        ↓
        Found? → Use foreign_athlete_id, nation from foreign_athletes.nation
        ↓
        Not found → Continue to Step 3

Step 3: Check nation_corrections table
        (for athletes with known incorrect nation in results files)
        ↓
        Correction found? → Use correct_nation, flag needs_review=True
        ↓
        Not found → Continue to Step 4

Step 4: Not found anywhere → FLAG FOR MANUAL REVIEW
        ↓
        DO NOT auto-create! Results file nation may be wrong.
        Return needs_review=True for admin to decide correct table.
```

**Key Rules:**
1. Nation in results comes from the **athlete record**, not the results file
2. **NO auto-create** of foreign athletes - all unmatched require manual review
3. Results file nation can be WRONG (e.g., Malaysian living in USA coded as "USA")

### **Nation Corrections Table**

For athletes whose results file nation is consistently wrong:

```sql
CREATE TABLE nation_corrections (
    id INTEGER PRIMARY KEY,
    fullname TEXT NOT NULL,           -- Name as it appears in results
    birthdate TEXT,                   -- For more specific matching
    results_nation TEXT,              -- What results file says (USA, INA, etc.)
    correct_nation TEXT NOT NULL,     -- What it should be (MAS)
    correct_table TEXT NOT NULL,      -- 'athletes' or 'foreign_athletes'
    notes TEXT,                       -- "Malaysian living in USA"
    created_at TEXT
);
```

**Use `add_nation_correction()` when you discover wrong nation:**
```python
from src.web.utils.athlete_lookup import add_nation_correction

# Elson Lee is Malaysian but coded as USA in results
add_nation_correction(
    conn,
    fullname="LEE, Elson C",
    results_nation="USA",
    correct_nation="MAS",
    correct_table="athletes",
    birthdate="2006-08-24",
    notes="Malaysian living in USA"
)
```

### **Identifying Foreign Athletes**

Foreign status is determined by **athlete record**, not results file:
- Registered athlete with `athletes.nation = 'SGP'` → foreign for results, even if club is Malaysian
- Unregistered athlete → requires manual review (use preview Excel sheets to categorize)

**Club names are NOT authoritative** — International school students may be Malaysian citizens. Always use the nation from the athlete's registration record.

### **Registration Process Note**

When asking athletes for their "nation" during registration, clarify:
> "This is your **sporting nation** — the country you are eligible to represent in international competition."

This determines whether they go into `athletes` (MAS) or `foreign_athletes` (other) table.

### **Why Two Tables?**

1. **Clean Malaysian database** — Development tracking, MAP points, national selection only for eligible swimmers
2. **No ID collisions** — Separate ID sequences prevent confusion
3. **Different data requirements** — Malaysian athletes have IC, registration data; foreign athletes only need basic info
4. **Query simplicity** — Easy to filter "all Malaysian results" vs "all results including foreign"

---

**Last Updated:** 2025-11-28
**Author:** Claude Code
