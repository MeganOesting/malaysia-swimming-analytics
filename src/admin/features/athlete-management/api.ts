/**
 * Athlete Management API Functions
 * Handles all API calls related to athlete management
 */

import { Athlete, AthleteDetail, AthleteInfoAnalysis } from '../../shared/types/admin';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

/**
 * Search for athletes by name
 */
export async function searchAthletes(query: string): Promise<Athlete[]> {
  try {
    const response = await fetch(
      `${API_BASE}/api/admin/athletes/search?query=${encodeURIComponent(query)}`
    );
    if (!response.ok) throw new Error('Search failed');
    const data = await response.json();
    return data.athletes || [];
  } catch (error) {
    console.error('Error searching athletes:', error);
    throw error;
  }
}

/**
 * Get athlete details by ID
 */
export async function getAthleteDetail(athleteId: string): Promise<AthleteDetail | null> {
  try {
    const response = await fetch(`${API_BASE}/api/admin/athletes/${athleteId}`);
    if (!response.ok) throw new Error('Failed to fetch athlete detail');
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching athlete detail:', error);
    throw error;
  }
}

/**
 * Get athlete results with optional filters
 */
export async function getAthleteResults(
  athleteId: string,
  options?: {
    startDate?: string;
    endDate?: string;
    bestOnly?: boolean;
  }
): Promise<any[]> {
  try {
    const params = new URLSearchParams();
    if (options?.startDate) params.append('start_date', options.startDate);
    if (options?.endDate) params.append('end_date', options.endDate);
    if (options?.bestOnly) params.append('best_only', 'true');

    const query = params.toString();
    const url = query
      ? `${API_BASE}/api/admin/athletes/${athleteId}/results?${query}`
      : `${API_BASE}/api/admin/athletes/${athleteId}/results`;

    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to fetch results');
    const data = await response.json();
    return data.results || [];
  } catch (error) {
    console.error('Error fetching athlete results:', error);
    throw error;
  }
}

/**
 * Export all athletes to Excel
 */
export async function exportAthletesExcel(): Promise<Blob> {
  try {
    const response = await fetch(`${API_BASE}/api/admin/athletes/export-excel`);
    if (!response.ok) throw new Error('Export failed');
    return await response.blob();
  } catch (error) {
    console.error('Error exporting athletes:', error);
    throw error;
  }
}

/**
 * Download athletes export file
 */
export function downloadAthletesExport(blob: Blob, filename: string = 'athletes_export.xlsx') {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

/**
 * Upload athlete info workbook for analysis
 */
export async function uploadAthleteInfoWorkbook(
  file: File
): Promise<AthleteInfoAnalysis> {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/api/admin/analyze-athlete-info`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) throw new Error('Upload failed');
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error uploading athlete info:', error);
    throw error;
  }
}

/**
 * Update athlete information
 */
export async function updateAthlete(
  athleteId: string,
  updates: Record<string, any>
): Promise<AthleteDetail> {
  try {
    const response = await fetch(`${API_BASE}/api/admin/athletes/${athleteId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updates),
    });

    if (!response.ok) throw new Error('Update failed');
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error updating athlete:', error);
    throw error;
  }
}

/**
 * Add athlete alias
 */
export async function addAthleteAlias(
  athleteId: string,
  alias: string
): Promise<any> {
  try {
    const response = await fetch(
      `${API_BASE}/api/admin/athletes/${athleteId}/add-alias`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ alias }),
      }
    );

    if (!response.ok) throw new Error('Failed to add alias');
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error adding athlete alias:', error);
    throw error;
  }
}
