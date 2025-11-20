# Manual Entry Feature

## Overview

The Manual Entry feature provides a 3-step wizard for manually entering swimming meet results without requiring an Excel file upload. This is useful for:
- Small meets with few results
- Quick time entry for individual athletes
- Correcting or adding missing results
- Testing and development

## Components

### ManualEntry (Main Component)

A wizard-style component that guides users through manual result entry.

**Props:**
```typescript
interface ManualEntryProps {
  isAuthenticated: boolean;
}
```

**Usage:**
```typescript
import { ManualEntry } from '@/admin/features/manual-entry';

<ManualEntry isAuthenticated={true} />
```

## Wizard Steps

### Step 1: Select Athletes

Users search for and select athletes to enter results for:

**Features:**
- Real-time athlete search (debounced 300ms)
- Click to add/remove athletes from selection
- Visual indication of selected athletes
- Display athlete details (name, gender, DOB, club)
- Minimum 1 athlete required to proceed

**UI Elements:**
- Search box with auto-search
- Search results list (clickable cards)
- Selected athletes list (with remove buttons)
- "Next" button (disabled if no athletes selected)

### Step 2: Enter Meet Information

Users provide meet details and select events:

**Required Fields:**
- Meet Name (text)
- Meet Date (date picker)
- Course (LCM or SCM dropdown)
- Events (checkbox list)

**Optional Fields:**
- City (text)
- Alias/Code (text)

**Event Selection:**
- Checkboxes for all standard swimming events
- Distances: 50, 100, 200, 400, 800, 1500m
- Strokes: FR (Freestyle), BK (Backstroke), BR (Breaststroke), BU (Butterfly), IM (Individual Medley)
- Genders: M (Male), F (Female)
- Scrollable list with selection highlighting

**Validation:**
- Meet name required
- Meet date required
- At least 1 event required

### Step 3: Enter Times

Users enter times for each athlete-event combination:

**Features:**
- Auto-generated table (athletes × events)
- Time input (accepts MM:SS.ss or SS.ss format)
- Place input (optional, numeric)
- Scrollable table for many results
- Real-time validation (all times required)

**Table Columns:**
- Athlete name
- Event (gender, distance, stroke)
- Time (required text input)
- Place (optional number input)

**Submission:**
- "Submit" button disabled until all times entered
- Loading state during submission
- Success message with meet ID
- Auto-reset wizard after successful submission

## API Functions

Located in `api.ts`:

```typescript
// Submit manual results
submitManualResults(
  submission: ManualResultsSubmission
): Promise<ManualResultsResponse>
```

**Request Structure:**
```typescript
interface ManualResultsSubmission {
  meet_name: string;
  meet_date: string;
  meet_city: string;
  meet_course: string; // 'LCM' or 'SCM'
  meet_alias: string;
  results: ManualResultPayload[];
}

interface ManualResultPayload {
  athlete_id: string;
  distance: number;
  stroke: string;
  event_gender: string;
  time_string: string;
  place?: number | null;
}
```

**Response Structure:**
```typescript
interface ManualResultsResponse {
  success: boolean;
  meet_id: string;
  results_inserted: number;
  total_results_submitted: number;
  message: string;
  errors?: string[];
}
```

## State Management

The component uses React hooks for comprehensive wizard state:

```typescript
// Step navigation
const [currentStep, setCurrentStep] = useState<1 | 2 | 3>(1);

// Step 1: Athletes
const [athleteSearchQuery, setAthleteSearchQuery] = useState('');
const [athleteSearchResults, setAthleteSearchResults] = useState<Athlete[]>([]);
const [searchingAthletes, setSearchingAthletes] = useState(false);
const [selectedAthletes, setSelectedAthletes] = useState<SelectedAthlete[]>([]);

// Step 2: Meet info
const [meetName, setMeetName] = useState('');
const [meetDate, setMeetDate] = useState('');
const [meetCity, setMeetCity] = useState('');
const [meetCourse, setMeetCourse] = useState<'LCM' | 'SCM'>('LCM');
const [meetAlias, setMeetAlias] = useState('');
const [selectedEvents, setSelectedEvents] = useState<Event[]>([]);

// Step 3: Times
const [manualResults, setManualResults] = useState<ManualResult[]>([]);
const [submitting, setSubmitting] = useState(false);
```

## User Flow

1. **Start Wizard** → Step 1 active, others disabled
2. **Search Athletes** → Type name, results appear
3. **Select Athletes** → Click to toggle selection
4. **Click "Next"** → Move to Step 2
5. **Enter Meet Info** → Fill required fields
6. **Select Events** → Check events to include
7. **Click "Next"** → Move to Step 3, table generated
8. **Enter Times** → Fill time for each result
9. **Click "Submit"** → POST to API
10. **Success** → Notification + Auto-reset wizard

## Styling

Uses Tailwind CSS for consistent, responsive design:

**Step Indicator:**
- Red background for active/completed steps
- Gray background for pending steps
- Bold font for current step

**Form Elements:**
- Consistent input styling with focus rings
- Required field indicators (red asterisk)
- Disabled state for buttons
- Hover effects on clickable items

**Color Coding:**
- Red (#CC0000) - Primary actions, active steps
- Green (#059669) - Submit button, selected items
- Gray - Disabled states, pending steps
- Blue - Event selection highlights

## Shared Dependencies

This feature uses shared utilities from the admin panel:

### Components
- `Button` - Action buttons with variants and loading states
- `SearchBox` - Athlete search input
- `AlertBox` - Success/error notifications

### Hooks
- `useNotification()` - Toast-style notifications

### API Functions
- `searchAthletes()` - From athlete-management feature

### Types
```typescript
import {
  Athlete,
  SelectedAthlete,
  ManualResult,
  ManualResultPayload,
  ManualResultsSubmission,
  ManualResultsResponse,
} from '@/admin/shared/types/admin';
```

## Error Handling

Comprehensive validation and error handling:

```typescript
// Step validation
if (selectedAthletes.length === 0) {
  error('Please select at least one athlete');
  return;
}

// API errors
try {
  await api.submitManualResults(submission);
  success('Results submitted!');
} catch (err) {
  error(err instanceof Error ? err.message : 'Failed to submit');
}
```

## Performance Optimizations

1. **Debounced Search** - 300ms delay prevents excessive API calls
2. **Memoized Callbacks** - useCallback prevents unnecessary re-renders
3. **Efficient State Updates** - Minimal re-renders during data entry
4. **Auto-reset** - Cleanup after submission

## API Endpoints

This feature interacts with:

```
POST /api/admin/manual-results  - Submit manual entry results
GET  /api/admin/athletes/search - Search athletes (from athlete-management)
```

## Future Enhancements

- [ ] Save draft functionality
- [ ] Bulk time entry (paste from spreadsheet)
- [ ] Event templates (save common event sets)
- [ ] Multi-meet entry (enter results for multiple meets)
- [ ] Import times from clipboard
- [ ] Time validation (check for reasonable times)
- [ ] Auto-calculate splits and paces
- [ ] Duplicate result detection
