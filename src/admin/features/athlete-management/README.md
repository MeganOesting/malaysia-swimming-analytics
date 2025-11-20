# Athlete Management Feature

## Overview

The Athlete Management feature provides comprehensive tools for managing athlete data, including:
- **Search** - Find athletes by name
- **Results Viewing** - View athlete performance results with date and time filters
- **Export** - Export athlete data to Excel spreadsheets
- **Upload & Analysis** - Upload and analyze athlete info workbooks

## Components

### AthleteManagement (Main Component)

The main component that orchestrates all athlete management functionality.

**Props:**
```typescript
interface AthleteManagementProps {
  isAuthenticated: boolean;
}
```

**Usage:**
```typescript
import { AthleteManagement } from '@/admin/features/athlete-management';

<AthleteManagement isAuthenticated={true} />
```

## Features

### 1. Search Athletes
Users can search for athletes by name with real-time results. The search interface includes:
- Text input for athlete name
- Date range filters (start/end dates)
- "Best Times Only" toggle
- Search button with loading state

### 2. View Results
Once an athlete is selected, their results are displayed in a table showing:
- Event (distance + stroke)
- Time
- Place
- Meet name
- Meet date
- Club
- State

Results can be filtered by:
- Date range
- Best times only (excludes slower times)

### 3. Export Athletes
One-click export of all athletes to an Excel file with columns:
- Athlete ID
- Full Name
- Birthdate

The file is automatically downloaded when the export button is clicked.

### 4. Upload & Analyze
Users can upload Excel workbooks containing athlete information for analysis. The feature:
- Validates the file format
- Analyzes sheet structure
- Displays sheet information (rows, columns, headers)
- Shows analysis results in a modal

## API Functions

Located in `api.ts`, all API calls are abstracted into reusable functions:

```typescript
// Search
searchAthletes(query: string): Promise<Athlete[]>

// Get athlete detail
getAthleteDetail(athleteId: string): Promise<AthleteDetail>

// Get results with filters
getAthleteResults(athleteId: string, options?: {
  startDate?: string;
  endDate?: string;
  bestOnly?: boolean;
}): Promise<any[]>

// Export
exportAthletesExcel(): Promise<Blob>
downloadAthletesExport(blob: Blob, filename?: string): void

// Upload
uploadAthleteInfoWorkbook(file: File): Promise<AthleteInfoAnalysis>

// Update
updateAthlete(athleteId: string, updates: Record<string, any>): Promise<AthleteDetail>
addAthleteAlias(athleteId: string, alias: string): Promise<any>
```

## State Management

The component uses React hooks for state management:

```typescript
// Search state
const [athleteSearchQuery, setAthleteSearchQuery] = useState('');
const [athleteSearchResults, setAthleteSearchResults] = useState<Athlete[]>([]);
const [searchingAthletes, setSearchingAthletes] = useState(false);

// Selected athlete & results
const [selectedAthletes, setSelectedAthletes] = useState<SelectedAthlete[]>([]);
const [athleteResults, setAthleteResults] = useState<any[]>([]);
const [loadingResults, setLoadingResults] = useState(false);

// Filters
const [startDate, setStartDate] = useState('');
const [endDate, setEndDate] = useState('');
const [bestOnly, setBestOnly] = useState(false);

// Upload state
const [athleteInfoUploading, setAthleteInfoUploading] = useState(false);
const [athleteInfoAnalysis, setAthleteInfoAnalysis] = useState<AthleteInfoAnalysis | null>(null);
```

## Styling

Uses Tailwind CSS utility classes for consistent styling:
- Color scheme: Red (#CC0000) primary, green (#059669) for export, blue for search
- Responsive grid layout
- Hover effects and transitions
- Modal overlays for analysis results

## Shared Dependencies

This feature uses shared utilities from the admin panel:

### Components
- `Button` - Reusable button component
- `SearchBox` - Search input with styling
- `AlertBox` - Notification alerts
- `Modal` - Dialog for analysis results

### Hooks
- `useNotification()` - Success/error messages

### Types
```typescript
import { Athlete, SelectedAthlete, AthleteInfoAnalysis } from '@/admin/shared/types';
```

## Error Handling

All errors are caught and displayed via the notification system:
```typescript
try {
  // API call
} catch (err) {
  error(err instanceof Error ? err.message : 'Failed to ...');
}
```

## Future Enhancements

- [ ] Batch athlete operations
- [ ] Advanced filtering and sorting
- [ ] Athlete profile editing modal
- [ ] Performance charts and analytics
- [ ] Integration with coach/club management
