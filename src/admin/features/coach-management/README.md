# Coach Management Feature

## Overview

The Coach Management feature provides comprehensive tools for managing swimming coaches and managers, including:
- **Search** - Find coaches by name or club
- **CRUD Operations** - Create, read, update, delete coach records
- **Comprehensive Profile** - Contact info, certifications, apparel sizes
- **Course Tracking** - Track coaching certifications and seminars

## Components

### CoachManagement (Main Component)

The main component that handles all coach management operations.

**Props:**
```typescript
interface CoachManagementProps {
  isAuthenticated: boolean;
}
```

**Usage:**
```typescript
import { CoachManagement } from '@/admin/features/coach-management';

<CoachManagement isAuthenticated={true} />
```

## Features

### 1. Coach Search

Multi-criteria search functionality:
- **Search by Name** - Find coaches by their name
- **Search by Club** - Find all coaches for a specific club
- **Combined Search** - Use both filters together
- Results displayed in sortable table

### 2. Add New Coach

Create a new coach record with:

**Required Fields:**
- Club Name
- Name
- Role (Head Coach, Assistant Coach, Manager)

**Contact Information:**
- Email
- WhatsApp number
- IC (Identity Card)
- Passport Number
- Passport Photo (file path)

**Apparel Sizes:**
- Shoe Size
- T-Shirt Size
- Tracksuit Size

**Documents:**
- Logbook File (file path)

**Certifications** (checkboxes):
- Level 1 Sport Specific
- Level 2
- Level 3
- Level 1 ISN
- Level 2 ISN
- Level 3 ISN
- Seminar Oct 2024
- State Coach
- Other Courses (text area)

### 3. Edit Coach

Update existing coach information:
- Search and select coach from results
- Click "Edit" button
- Form auto-populates with coach data
- Modify any fields
- Click "Update Coach" to save
- Click "Cancel" to return to add mode

### 4. Delete Coach

Remove coach from database:
- Click "Delete" button in search results
- Confirm deletion in dialog
- Coach removed from database
- Search results refresh automatically

## API Functions

Located in `api.ts`, all API calls are abstracted into reusable functions:

```typescript
// Search coaches
searchCoaches(name?: string, clubName?: string): Promise<Coach[]>

// Create coach
createCoach(coachData: CoachFormData): Promise<any>

// Update coach
updateCoach(coachId: string, coachData: CoachFormData): Promise<any>

// Delete coach
deleteCoach(coachId: string): Promise<any>
```

**Type Definitions:**
```typescript
interface CoachFormData {
  club_name: string;
  name: string;
  role: string;
  email: string;
  whatsapp: string;
  passport_photo: string;
  passport_number: string;
  ic: string;
  shoe_size: string;
  tshirt_size: string;
  tracksuit_size: string;
  course_level_1_sport_specific: boolean;
  course_level_2: boolean;
  course_level_3: boolean;
  course_level_1_isn: boolean;
  course_level_2_isn: boolean;
  course_level_3_isn: boolean;
  seminar_oct_2024: boolean;
  other_courses: string;
  state_coach: boolean;
  logbook_file: string;
}

interface Coach extends CoachFormData {
  id: string;
}
```

## State Management

The component uses React hooks for state management:

```typescript
// Search
const [coachSearchName, setCoachSearchName] = useState('');
const [coachSearchClub, setCoachSearchClub] = useState('');
const [coaches, setCoaches] = useState<Coach[]>([]);

// Form
const [coachFormMode, setCoachFormMode] = useState<'add' | 'edit'>('add');
const [selectedCoach, setSelectedCoach] = useState<Coach | null>(null);
const [coachFormData, setCoachFormData] = useState<CoachFormData>({...});
```

## Form Sections

The coach form is organized into logical sections:

### Basic Information
- Club Name (required)
- Name (required)
- Role dropdown (required)
- Email
- WhatsApp
- IC
- Passport Number
- Passport Photo path

### Apparel Sizes
- Shoe Size
- T-Shirt Size
- Tracksuit Size

### Course Certifications
- Checkboxes for all certification levels
- Text area for other courses
- State Coach designation
- Logbook file path

## Styling

Uses Tailwind CSS for consistent, professional design:
- **Search Section**: Light gray background with border
- **Results Table**: Sticky header, scrollable body
- **Form**: Two-column grid layout
- **Certifications**: Three-column checkbox grid
- **Buttons**: Color-coded by action type
- **Required Fields**: Red asterisk indicators

## Shared Dependencies

This feature uses shared utilities from the admin panel:

### Components
- `Button` - Action buttons with variants, sizes, loading states
- `AlertBox` - Success/error notification messages

### Hooks
- `useNotification()` - Toast-style notifications

## Workflow Examples

### Adding a New Coach

1. Click "Add New Coach" button
2. Fill in required fields (club, name, role)
3. Add optional contact information
4. Enter apparel sizes if known
5. Check applicable certifications
6. Add notes about other courses
7. Click "Add Coach"
8. Success notification appears
9. Form resets for next entry

### Editing a Coach

1. Search for coach by name or club
2. Click "Edit" in search results
3. Form populates with coach data
4. Modify desired fields
5. Click "Update Coach"
6. Success notification appears
7. Search results refresh

### Deleting a Coach

1. Find coach in search results
2. Click "Delete" button
3. Confirm in browser dialog
4. Coach removed from database
5. Success notification appears
6. Search results refresh

## Validation

Form validation ensures data quality:
- Club name required
- Coach name required
- Role required
- All other fields optional but validated for format

## Error Handling

All errors are caught and displayed via the notification system:

```typescript
try {
  await api.createCoach(coachFormData);
  success('Coach created successfully');
} catch (err) {
  error(err instanceof Error ? err.message : 'Failed to save coach');
}
```

## Confirmation Dialogs

Delete operations require confirmation:
```typescript
if (!window.confirm(`Delete coach "${coach.name}"?`)) {
  return;
}
```

## API Endpoints

This feature interacts with the following backend endpoints:

```
GET    /api/admin/coaches                - Search coaches
GET    /api/admin/coaches?name={name}    - Search by name
GET    /api/admin/coaches?club_name={n}  - Search by club
POST   /api/admin/coaches                - Create new coach
PUT    /api/admin/coaches/{id}           - Update existing coach
DELETE /api/admin/coaches/{id}           - Delete coach
```

## Integration with Club Management

Coach management integrates with club management:
- Club names must match clubs in database
- Can view coaches from club management feature
- Coach-club association maintained

## Course Certifications

Tracks common Malaysian swimming coaching certifications:
- **Sport Specific Levels**: Official coaching qualifications
- **ISN Levels**: Integrated Sports Network certifications
- **Seminars**: Recent professional development
- **State Coach**: State-level coaching designation
- **Other Courses**: Freeform text for additional training

## Future Enhancements

- [ ] File upload for passport photos and logbooks
- [ ] Certificate expiration tracking
- [ ] Coach statistics (athletes coached, meet attendance)
- [ ] Email notifications for certification renewals
- [ ] Coach availability calendar
- [ ] Performance metrics and evaluations
- [ ] Export coach list to Excel
- [ ] Import coaches from CSV
- [ ] Coach profile photos
- [ ] Document management system
- [ ] Multi-club coach support
- [ ] Coach search by certification level
