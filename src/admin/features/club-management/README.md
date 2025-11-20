# Club Management Feature

## Overview

The Club Management feature provides comprehensive tools for managing swimming clubs in Malaysia, including:
- **State-based Organization** - Browse clubs by state
- **CRUD Operations** - Create, read, update club information
- **Coach Viewing** - View coaches and managers for each club
- **Roster Management** - View athlete rosters with optional meet filtering

## Components

### ClubManagement (Main Component)

The main component that handles all club management operations.

**Props:**
```typescript
interface ClubManagementProps {
  isAuthenticated: boolean;
  meets?: Meet[]; // Optional: for roster filtering
}
```

**Usage:**
```typescript
import { ClubManagement } from '@/admin/features/club-management';

<ClubManagement isAuthenticated={true} meets={meets} />
```

## Features

### 1. State Selection

Browse clubs by Malaysian state:
- Dropdown list of all states
- Automatically loads clubs when state is selected
- Resets club selection when state changes

### 2. Club Selection

Select a club to view/edit:
- Dropdown list filtered by selected state
- Shows club name and code (if available)
- Loads club data into edit form
- Disabled until state is selected

### 3. Add New Club

Create a new club with required and optional fields:

**Required Fields:**
- Club Name
- State Code

**Optional Fields:**
- Club Code (5 characters max, auto-uppercase)
- Nation (3 characters, defaults to 'MAS')
- Alias (alternative name for matching)

**Actions:**
- Click "Add New Club" button
- Fill in form fields
- Click "Add Club" to save
- Form resets after successful creation
- Club list refreshes automatically

### 4. Edit Club

Update existing club information:
- Select club from dropdown
- Form auto-populates with club data
- Modify any fields
- Click "Update Club" to save
- Click "Cancel" to reset form to "Add" mode

### 5. View Coaches & Managers

For a selected club:
- Click "Load Coaches/Managers" button
- Table displays all coaches with:
  - Name
  - Role (Head Coach, Assistant Coach, Manager)
  - Email
  - WhatsApp number
- Empty fields show "-"

### 6. View Athlete Roster

For a selected club:
- Optional: Select a specific meet to filter athletes
- Click "Load Roster" button
- Table displays athletes with:
  - Full Name
  - Gender
  - Year Age
  - Day Age
- Shows total athlete count
- Scrollable list for large rosters

## API Functions

Located in `api.ts`, all API calls are abstracted into reusable functions:

```typescript
// Fetch states
getStates(): Promise<string[]>

// Fetch clubs by state
getClubsByState(stateCode: string): Promise<Club[]>

// Create club
createClub(clubData: ClubData): Promise<any>

// Update club
updateClub(clubName: string, clubData: ClubData): Promise<any>

// Get coaches
getCoachesByClub(clubName: string): Promise<Coach[]>

// Get roster
getClubRoster(clubName: string, meetId?: string): Promise<RosterAthlete[]>
```

**Type Definitions:**
```typescript
interface ClubData {
  club_name: string;
  club_code: string;
  state_code: string;
  nation: string;
  alias: string;
}

interface Club {
  club_name: string;
  club_code?: string;
  state_code?: string;
  nation?: string;
  alias?: string;
}

interface Coach {
  id: string;
  name: string;
  role: string;
  email?: string;
  whatsapp?: string;
  club_name: string;
}

interface RosterAthlete {
  fullname: string;
  gender: string;
  year_age?: number;
  day_age?: number;
}
```

## State Management

The component uses React hooks for state management:

```typescript
// States and clubs
const [states, setStates] = useState<string[]>([]);
const [selectedState, setSelectedState] = useState('');
const [clubs, setClubs] = useState<Club[]>([]);
const [selectedClub, setSelectedClub] = useState<Club | null>(null);

// Club form
const [clubFormMode, setClubFormMode] = useState<'add' | 'edit'>('add');
const [clubFormData, setClubFormData] = useState<ClubData>({...});

// Coaches and roster
const [coaches, setCoaches] = useState<Coach[]>([]);
const [clubRoster, setClubRoster] = useState<RosterAthlete[]>([]);
const [loadingRoster, setLoadingRoster] = useState(false);
```

## Styling

Uses Tailwind CSS utility classes for consistent styling:
- **Form sections**: Light gray backgrounds with borders
- **Tables**: Striped rows with hover effects
- **Buttons**: Color-coded by action type
- **Inputs**: Red focus rings for consistency
- **Disabled states**: Gray backgrounds
- **Sticky headers**: In scrollable tables

## Shared Dependencies

This feature uses shared utilities from the admin panel:

### Components
- `Button` - Reusable button with variants, sizes, loading states
- `AlertBox` - Success/error notification messages

### Hooks
- `useNotification()` - Toast-style notifications

### Types
```typescript
import { Meet } from '@/admin/shared/types/admin';
```

## Workflow Examples

### Creating a New Club

1. Select state from dropdown
2. Click "Add New Club"
3. Enter club name (required)
4. Enter state code (required)
5. Optionally enter club code, nation, alias
6. Click "Add Club"
7. Success notification appears
8. Club added to dropdown list
9. Form resets for next entry

### Editing an Existing Club

1. Select state from dropdown
2. Select club from club dropdown
3. Form auto-fills with club data
4. Modify desired fields
5. Click "Update Club"
6. Success notification appears
7. Changes saved to database

### Viewing Club Roster

1. Select state and club
2. Optionally select a meet
3. Click "Load Roster"
4. Table displays all athletes
5. Scroll through list
6. Change meet selection to re-filter

## Error Handling

All errors are caught and displayed via the notification system:

```typescript
try {
  await api.createClub(clubData);
  success('Club created successfully');
} catch (err) {
  error(err instanceof Error ? err.message : 'Failed to save club');
}
```

## Validation

Form validation prevents invalid submissions:
- Club name cannot be empty
- State code cannot be empty
- Club code limited to 5 characters
- Nation limited to 3 characters
- Fields auto-uppercase where appropriate

## API Endpoints

This feature interacts with the following backend endpoints:

```
GET  /api/admin/states                        - Fetch all states
GET  /api/admin/clubs?state={code}            - Fetch clubs by state
POST /api/admin/clubs                         - Create new club
PUT  /api/admin/clubs/{name}                  - Update existing club
GET  /api/admin/coaches?club_name={name}      - Get coaches for club
GET  /api/admin/clubs/{name}/roster           - Get club roster
GET  /api/admin/clubs/{name}/roster?meet_id=  - Get roster for specific meet
```

## Integration with Coach Management

The club management feature integrates with coach management:
- View coaches button loads coaches for the club
- Can navigate to coach management to add/edit coaches
- Coach data includes club association

## Future Enhancements

- [ ] Delete club functionality
- [ ] Merge clubs (handle duplicates)
- [ ] Club search across all states
- [ ] Export club list to Excel
- [ ] Import clubs from CSV
- [ ] Club statistics (athlete count, meet participation)
- [ ] Club history/timeline
- [ ] Coach assignment from club form
- [ ] Bulk roster export
- [ ] Roster comparison across meets
