/**
 * Meet Management API Functions
 * Handles all API calls related to meet management and file uploads
 */

import { Meet, UploadSummary } from '../../shared/types/admin';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

export interface ConversionResponse {
  success: boolean;
  message: string;
  athletes?: number;
  results?: number;
  events?: number;
  meets?: number;
  issues?: Record<string, any[]>;
}

/**
 * Fetch all meets from the database
 */
export async function getMeets(): Promise<Meet[]> {
  try {
    const response = await fetch(`${API_BASE}/api/admin/meets`);
    if (!response.ok) throw new Error('Failed to fetch meets');
    const data = await response.json();
    return data.meets || [];
  } catch (error) {
    console.error('Error fetching meets:', error);
    throw error;
  }
}

/**
 * Update meet alias/code
 */
export async function updateMeetAlias(
  meetId: string,
  alias: string
): Promise<any> {
  try {
    const response = await fetch(`${API_BASE}/api/admin/meets/${meetId}/alias`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ alias }),
    });

    if (!response.ok) throw new Error('Failed to update alias');
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error updating meet alias:', error);
    throw error;
  }
}

/**
 * Delete meet and all its results
 */
export async function deleteMeet(meetId: string): Promise<any> {
  try {
    const response = await fetch(`${API_BASE}/api/admin/meets/${meetId}`, {
      method: 'DELETE',
    });

    if (!response.ok) throw new Error('Failed to delete meet');
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error deleting meet:', error);
    throw error;
  }
}

/**
 * Get meet PDF URL (opens in new tab)
 */
export function getMeetPdfUrl(meetId: string): string {
  return `${API_BASE}/api/admin/meets/${meetId}/pdf`;
}

/**
 * Open meet PDF in new tab
 */
export function openMeetPdf(meetId: string): void {
  const pdfUrl = getMeetPdfUrl(meetId);
  window.open(pdfUrl, '_blank');
}

/**
 * Upload and convert Excel file
 */
export async function uploadMeetFile(
  file: File,
  fileType: 'swimrankings' | 'seag' = 'swimrankings',
  seagYear?: string,
  meetCity?: string,
  meetName?: string,
  meetMonth?: string,
  meetDay?: string
): Promise<ConversionResponse> {
  try {
    const formData = new FormData();
    formData.append('file', file);

    // Route to appropriate endpoint based on file type
    const endpoint =
      fileType === 'seag' ? '/api/admin/upload-seag' : '/api/admin/convert-excel';

    // Add required parameters for SEAG uploads
    if (fileType === 'seag') {
      if (!seagYear || !meetCity || !meetName || !meetMonth || !meetDay) {
        throw new Error('Year, meet city, meet name, and meet date are required for SEAG uploads');
      }
      formData.append('year', seagYear);
      formData.append('meetcity', meetCity);
      formData.append('meet_name', meetName);
      formData.append('meet_month', meetMonth);
      formData.append('meet_day', meetDay);
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || errorData.message || 'Upload failed'
      );
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error uploading file:', error);
    throw error;
  }
}

/**
 * Upload multiple files sequentially
 */
export async function uploadMultipleFiles(
  files: File[],
  fileType: 'swimrankings' | 'seag' = 'swimrankings',
  seagYear: string = '2025',
  meetCity?: string,
  meetName?: string,
  meetMonth?: string,
  meetDay?: string,
  onProgress?: (summary: UploadSummary) => void
): Promise<UploadSummary[]> {
  const summaries: UploadSummary[] = [];

  for (const file of files) {
    const summary: UploadSummary = {
      filename: file.name,
      status: 'processing',
      message: 'Uploading…',
    };

    if (onProgress) onProgress(summary);

    try {
      const result = await uploadMeetFile(file, fileType, seagYear, meetCity, meetName, meetMonth, meetDay);

      summary.status = result.success ? 'success' : 'error';
      summary.message = result.message;

      if (result.success) {
        summary.metrics = {
          athletes: result.athletes || 0,
          results: result.results || 0,
          events: result.events || 0,
          meets: result.meets || 0,
        };
      }

      if (result.issues) {
        summary.issues = result.issues;
      }
    } catch (error) {
      summary.status = 'error';
      summary.message =
        error instanceof Error ? error.message : 'Upload failed';
    }

    summaries.push(summary);
    if (onProgress) onProgress(summary);
  }

  return summaries;
}

/**
 * Test SEAG upload - Check athlete matching WITHOUT writing to database
 */
export async function testSeagUpload(file: File): Promise<any> {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/api/admin/test-seag-upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || errorData.message || 'Test failed'
      );
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error testing SEAG upload:', error);
    throw error;
  }
}

/**
 * Preview SEAG upload - Generate spreadsheet with mock results table data
 */
export async function previewSeagUpload(
  file: File,
  year: string,
  meetCity: string,
  meetName: string,
  meetMonth: string,
  meetDay: string
): Promise<Blob> {
  try {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('year', year);
    formData.append('meetcity', meetCity);
    formData.append('meet_name', meetName);
    formData.append('meet_month', meetMonth);
    formData.append('meet_day', meetDay);

    const response = await fetch(`${API_BASE}/api/admin/preview-seag-upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      // Handle FastAPI validation errors (detail is an array of objects)
      let errorMessage = 'Preview failed';
      if (Array.isArray(errorData.detail)) {
        errorMessage = errorData.detail.map((e: { loc?: string[]; msg?: string }) =>
          `${e.loc?.join('.') || 'field'}: ${e.msg || 'invalid'}`
        ).join('; ');
      } else if (typeof errorData.detail === 'string') {
        errorMessage = errorData.detail;
      } else if (errorData.message) {
        errorMessage = errorData.message;
      }
      throw new Error(errorMessage);
    }

    // Return blob for file download
    return await response.blob();
  } catch (error) {
    console.error('Error previewing SEAG upload:', error);
    throw error;
  }
}

/**
 * Preview result with summary info
 */
export interface PreviewResult {
  blob: Blob;
  summary: {
    total: number;
    matched: number;
    unmatched: number;
  };
}

/**
 * Preview SwimRankings upload - Generate spreadsheet with mock results table data
 * Extracts meet info from the file itself (no user input required)
 * Returns blob AND summary counts for user feedback
 */
export async function previewSwimRankingsUpload(file: File): Promise<PreviewResult> {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/api/admin/preview-swimrankings-upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      let errorMessage = 'Preview failed';
      if (Array.isArray(errorData.detail)) {
        errorMessage = errorData.detail.map((e: { loc?: string[]; msg?: string }) =>
          `${e.loc?.join('.') || 'field'}: ${e.msg || 'invalid'}`
        ).join('; ');
      } else if (typeof errorData.detail === 'string') {
        errorMessage = errorData.detail;
      } else if (errorData.message) {
        errorMessage = errorData.message;
      }
      throw new Error(errorMessage);
    }

    // Extract summary from response headers
    const summary = {
      total: parseInt(response.headers.get('X-Preview-Total') || '0', 10),
      matched: parseInt(response.headers.get('X-Preview-Matched') || '0', 10),
      unmatched: parseInt(response.headers.get('X-Preview-Unmatched') || '0', 10),
    };

    const blob = await response.blob();
    return { blob, summary };
  } catch (error) {
    console.error('Error previewing SwimRankings upload:', error);
    throw error;
  }
}
