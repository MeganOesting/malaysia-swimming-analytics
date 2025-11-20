# Meet Management Feature

## Overview

The Meet Management feature provides tools for managing swimming meets in the database, including:
- **View Meets** - Display all meets in a sortable table
- **Edit Aliases** - Update meet aliases/codes inline
- **Delete Meets** - Remove meets and all associated results
- **Generate PDFs** - View meet results as formatted PDF reports

## Components

### MeetManagement (Main Component)

The main component that handles all meet management operations.

**Props:**
```typescript
interface MeetManagementProps {
  isAuthenticated: boolean;
}
```

**Usage:**
```typescript
import { MeetManagement } from '@/admin/features/meet-management';

<MeetManagement isAuthenticated={true} />
```

## Features

### 1. View Meets Table

Displays all meets with the following columns:
- **Meet Name** - Full name of the meet
- **ID** - Unique meet identifier (UUID, shown in monospace)
- **Alias/Code** - Short code for the meet (editable)
- **Date** - Meet date (formatted)
- **City** - Meet location
- **Results** - Number of results in the meet
- **Actions** - PDF generation and delete buttons

### 2. Edit Meet Aliases

Users can edit meet aliases inline:
- Click "Edit" button next to alias
- Enter new alias in input field
- Press Enter or click ✓ to save
- Click ✕ to cancel editing
- Row highlights in amber during edit mode

### 3. Delete Meets

Admins can delete meets with confirmation:
- Click "Delete" button
- Confirm deletion in browser dialog
- Meet and all associated results are removed
- Success notification appears
- Table updates automatically

### 4. Generate PDF Reports

One-click PDF generation:
- Click "View PDF" button
- PDF opens in new browser tab
- Report shows event-by-event results with:
  - Place
  - Athlete name
  - Birthdate
  - Time

### 5. Force Refresh

Manual refresh button to reload meet data:
- Resets loading state
- Fetches latest data from API
- Useful for troubleshooting

## API Functions

Located in `api.ts`, all API calls are abstracted into reusable functions:

```typescript
// Fetch all meets
getMeets(): Promise<Meet[]>

// Update alias
updateMeetAlias(meetId: string, alias: string): Promise<any>

// Delete meet
deleteMeet(meetId: string): Promise<any>

// Get PDF URL
getMeetPdfUrl(meetId: string): string

// Open PDF in new tab
openMeetPdf(meetId: string): void
```

## State Management

The component uses React hooks for state management:

```typescript
// Meets data
const [meets, setMeets] = useState<Meet[]>([]);
const [loadingMeets, setLoadingMeets] = useState(false);

// Editing state (tracks which alias is being edited)
const [editingAlias, setEditingAlias] = useState<Record<string, string>>({});
```

## Styling

Uses Tailwind CSS utility classes for consistent styling:
- Table with alternating row hover effects
- Amber highlight during alias editing
- Color-coded action buttons:
  - Green for PDF generation
  - Red for deletion
  - Blue for alias editing
- Responsive layout with horizontal scroll on small screens

## Shared Dependencies

This feature uses shared utilities from the admin panel:

### Components
- `Button` - Reusable button component with variants
- `AlertBox` - Notification alerts for success/error messages

### Hooks
- `useNotification()` - Success/error message system

### Types
```typescript
import { Meet } from '@/admin/shared/types/admin';
```

**Meet Interface:**
```typescript
interface Meet {
  id: string;
  name: string;
  alias: string;
  date: string;
  city: string;
  result_count: number;
}
```

## Error Handling

All errors are caught and displayed via the notification system:
```typescript
try {
  await api.deleteMeet(meetId);
  success('Meet deleted');
} catch (err) {
  error(err instanceof Error ? err.message : 'Failed to delete meet');
}
```

## User Interactions

### Confirmation Dialogs
- Delete operations require confirmation via `window.confirm()`
- Prevents accidental data loss

### Inline Editing
- Alias editing happens inline without modal dialogs
- Enter key submits changes
- Escape-style cancel button (✕)

### Loading States
- "Loading..." indicator while fetching meets
- Helpful message if load takes too long
- Disabled buttons during operations

## API Endpoints

This feature interacts with the following backend endpoints:

```
GET    /api/admin/meets              - Fetch all meets
PUT    /api/admin/meets/{id}/alias   - Update meet alias
DELETE /api/admin/meets/{id}         - Delete meet
GET    /api/admin/meets/{id}/pdf     - Generate PDF report
```

## Future Enhancements

- [ ] Meet search and filtering
- [ ] Sort by columns (name, date, results count)
- [ ] Bulk operations (delete multiple meets)
- [ ] Meet editing (name, date, city)
- [ ] Export meets to Excel
- [ ] Meet merging functionality
- [ ] Results preview before PDF generation
