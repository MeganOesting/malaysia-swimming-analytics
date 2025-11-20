# File Upload Feature

## Overview

The File Upload feature provides a robust Excel file upload system for importing swimming meet results, including:
- **Multi-file Upload** - Upload multiple Excel files at once
- **Progress Tracking** - Real-time upload status for each file
- **Validation Issues** - Detailed reporting of data issues
- **Expandable Details** - Collapsible issue groups for easy review
- **Metrics Display** - Success metrics (athletes, results, events, meets)

## Components

### FileUpload (Main Component)

The main component that handles Excel file upload and conversion.

**Props:**
```typescript
interface FileUploadProps {
  isAuthenticated: boolean;
}
```

**Usage:**
```typescript
import { FileUpload } from '@/admin/features/file-upload';

<FileUpload isAuthenticated={true} />
```

## Features

### 1. File Selection

Users can select one or more Excel files:
- Click "Choose Files" button
- Select .xlsx or .xls files
- Multiple files can be selected at once
- Additional files can be added before upload
- Selected files shown in a list with remove buttons

**File Management:**
- Add files incrementally
- Remove unwanted files before upload
- No duplicate filenames allowed
- File list persists until upload

### 2. Upload & Convert

Upload all selected files with one click:
- Click "Upload & Convert Meet" button
- Files processed sequentially
- Real-time status updates
- Upload button disabled during processing
- Success/error notifications

### 3. Upload Summaries

Each file gets a detailed summary card:

**Status Indicators:**
- **Pending** (gray) - Waiting to process
- **Processing** (yellow) - Currently uploading
- **Success** (green) - Upload completed successfully
- **Error** (red) - Upload failed

**Success Metrics:**
- Athletes imported
- Results added
- Events created
- Meets processed

**Displayed as large numbers with labels**

### 4. Validation Issues

Collapsible issue groups show data problems:

**Issue Types:**
- **Name Format Mismatches** - Athlete names don't match database format
- **Club Not Found** - Club names not in database
- **Duplicate Athletes** - Same athlete appears multiple times
- **Invalid Times** - Time format errors
- **Missing Birthdates** - Athletes without birthdates

**Issue Display:**
- Expandable/collapsible groups
- Issue count shown in header
- Click to expand/collapse
- Sheet and row numbers provided
- Detailed field information

### 5. Issue Resolution

For certain issues, resolution actions are available:
- **Add as Alias** - Add name variant as athlete alias
- **Create Club** - Quick-add missing clubs (if implemented)
- **Merge Athletes** - Combine duplicate entries (if implemented)

## API Functions

Located in `api.ts`, all API calls are abstracted into reusable functions:

```typescript
// Upload single file
uploadMeetFile(file: File): Promise<ConversionResponse>

// Upload multiple files with progress callback
uploadMultipleFiles(
  files: File[],
  onProgress?: (summary: UploadSummary) => void
): Promise<UploadSummary[]>
```

**Type Definitions:**
```typescript
interface ConversionResponse {
  success: boolean;
  message: string;
  athletes?: number;
  results?: number;
  events?: number;
  meets?: number;
  issues?: Record<string, any[]>;
}

interface UploadSummary {
  filename: string;
  status: 'pending' | 'processing' | 'success' | 'error';
  message: string;
  metrics?: {
    athletes: number;
    results: number;
    events: number;
    meets: number;
  };
  issues?: ValidationIssues;
}

interface ValidationIssueDetail {
  sheet?: string;
  row?: string;
  [key: string]: string | undefined;
}

type ValidationIssues = Record<string, ValidationIssueDetail[]>;
```

## State Management

The component uses React hooks for state management:

```typescript
// File state
const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
const [uploading, setUploading] = useState(false);

// Results
const [uploadSummaries, setUploadSummaries] = useState<UploadSummary[]>([]);
const [expandedIssueKeys, setExpandedIssueKeys] = useState<Record<string, boolean>>({});
```

## Styling

Uses Tailwind CSS with dynamic inline styles for status colors:

**Upload Section:**
- Sticky positioning at top
- Green border for emphasis
- File list with remove buttons
- Status-based color coding

**Summary Cards:**
- Border color matches status
- Large metric numbers in red
- Collapsible issue sections
- Hover effects on interactive elements

**Status Colors:**
- Success: Green (#166534, #bbf7d0)
- Processing: Yellow (#854d0e, #fcd34d)
- Pending: Gray (#1f2937, #d1d5db)
- Error: Red (#b91c1c, #fecaca)

## Shared Dependencies

This feature uses shared utilities from the admin panel:

### Components
- `Button` - Upload button with loading state
- `AlertBox` - Success/error notifications

### Hooks
- `useNotification()` - Toast-style notifications

### Types
```typescript
import {
  UploadSummary,
  ValidationIssueDetail,
} from '@/admin/shared/types/admin';
```

## Upload Flow

1. **Select Files** → Click "Choose Files" button
2. **Add Files** → Select one or more .xlsx/.xls files
3. **Review List** → See selected files, add more or remove
4. **Upload** → Click "Upload & Convert Meet"
5. **Watch Progress** → Status updates for each file
6. **Review Results** → Check metrics and issues
7. **Expand Issues** → Click to see validation problems
8. **Resolve Issues** → Take action on data problems

## Validation Issue Labels

User-friendly labels for technical issue keys:

```typescript
const ISSUE_LABELS = {
  name_format_mismatches: 'Name Format Mismatches',
  club_misses: 'Club Not Found',
  duplicate_athletes: 'Duplicate Athletes',
  invalid_times: 'Invalid Times',
  missing_birthdates: 'Missing Birthdates',
};
```

## Error Handling

Comprehensive error handling throughout:

```typescript
try {
  const result = await uploadMeetFile(file);
  // Process success
} catch (error) {
  summary.status = 'error';
  summary.message = error instanceof Error ? error.message : 'Upload failed';
}
```

## Progress Callbacks

Upload progress is tracked via callbacks:

```typescript
await uploadMultipleFiles(files, (summary) => {
  // Update UI with latest summary
  setUploadSummaries(prev =>
    prev.map(s => s.filename === summary.filename ? summary : s)
  );
});
```

## File Type Restrictions

Only Excel files accepted:
- `.xlsx` (Excel 2007+)
- `.xls` (Excel 97-2003)
- Enforced via input `accept` attribute

## API Endpoints

This feature interacts with:

```
POST /api/admin/upload-excel  - Upload and convert Excel file
```

**Request:**
- Content-Type: multipart/form-data
- Body: FormData with 'file' field

**Response:**
```json
{
  "success": true,
  "message": "Successfully processed 25 results...",
  "athletes": 15,
  "results": 25,
  "events": 8,
  "meets": 1,
  "issues": {
    "name_format_mismatches": [
      {
        "sheet": "Results",
        "row": "12",
        "upload_fullname": "John Doe",
        "database_fullname": "Doe, John"
      }
    ]
  }
}
```

## Performance Considerations

1. **Sequential Upload** - Files uploaded one at a time to avoid overwhelming server
2. **Progress Updates** - Real-time UI updates without blocking
3. **Issue Grouping** - Collapsed by default to reduce initial render size
4. **Duplicate Prevention** - Filenames checked before adding to list

## User Experience Features

1. **Sticky Upload Section** - Always visible at top during scroll
2. **Clear Visual Feedback** - Color-coded status indicators
3. **Detailed Error Information** - Sheet and row numbers for issues
4. **Bulk Operations** - Upload multiple files at once
5. **Incremental File Addition** - Add more files before uploading

## Future Enhancements

- [ ] Drag-and-drop file upload
- [ ] Upload history/log
- [ ] Automatic issue resolution suggestions
- [ ] Preview file contents before upload
- [ ] Pause/resume upload capability
- [ ] Parallel upload option (with server support)
- [ ] Excel template download
- [ ] Format validation before upload
- [ ] Upload scheduling (queue large batches)
- [ ] Email notifications on completion
- [ ] Download processed results
- [ ] Rollback capability for failed uploads
- [ ] File size limits and warnings
- [ ] Compression for large files
