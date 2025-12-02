/**
 * File Upload API Functions
 * Handles Excel file uploads for meet conversion
 */

import { UploadSummary } from '../../shared/types/admin';

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
        // For SEAG uploads, convert to metrics format if available
        if (fileType === 'seag' && (result as any).results_inserted !== undefined) {
          summary.metrics = {
            athletes: 0,
            results: (result as any).results_inserted || 0,
            events: 0,
            meets: 1,
          };
        } else {
          summary.metrics = {
            athletes: result.athletes || 0,
            results: result.results || 0,
            events: result.events || 0,
            meets: result.meets || 0,
          };
        }
      }

      // Convert SEAG errors to issues format
      if (fileType === 'seag' && (result as any).errors) {
        const issues: Record<string, any[]> = {};

        // Add parsing errors
        if ((result as any).errors && (result as any).errors.length > 0) {
          issues['parsing_errors'] = (result as any).errors.map((err: string) => ({
            sheet: 'Sheet',
            row: err,
          }));
        }

        // Add unmatched athletes
        if ((result as any).unmatched_athletes && (result as any).unmatched_athletes.length > 0) {
          issues['unmatched_athletes'] = (result as any).unmatched_athletes.map((athlete: any) => ({
            fullname: athlete.fullname || '',
            gender: athlete.gender || '',
            distance: String(athlete.distance || ''),
            stroke: athlete.stroke || '',
            time: athlete.time || '',
          }));
        }

        summary.issues = issues;
        // Override status if there are critical errors but results were inserted
        if ((result as any).errors && (result as any).errors.length > 0 && (result as any).results_inserted === 0) {
          summary.status = 'error';
        }
      }

      if (result.issues && fileType !== 'seag') {
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
