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
  seagYear?: string
): Promise<ConversionResponse> {
  try {
    const formData = new FormData();
    formData.append('file', file);

    // Route to appropriate endpoint based on file type
    const endpoint =
      fileType === 'seag' ? '/api/admin/upload-seag' : '/api/admin/upload-excel';

    // Add year parameter for SEAG uploads
    if (fileType === 'seag' && seagYear) {
      formData.append('year', seagYear);
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
      const result = await uploadMeetFile(file, fileType, seagYear);

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
