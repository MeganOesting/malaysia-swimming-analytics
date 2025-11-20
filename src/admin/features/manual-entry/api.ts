/**
 * Manual Entry API Functions
 * Handles manual result entry submission
 */

import { ManualResultsSubmission, ManualResultsResponse } from '../../shared/types/admin';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

/**
 * Submit manual results
 */
export async function submitManualResults(
  submission: ManualResultsSubmission
): Promise<ManualResultsResponse> {
  try {
    const response = await fetch(`${API_BASE}/api/admin/manual-results`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(submission),
    });

    if (!response.ok) throw new Error('Failed to submit results');
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error submitting manual results:', error);
    throw error;
  }
}
