/**
 * Coach Management API Functions
 * Handles all API calls related to coach/manager management
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

export interface CoachFormData {
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

export interface Coach extends CoachFormData {
  id: string;
}

/**
 * Search coaches
 */
export async function searchCoaches(
  name?: string,
  clubName?: string
): Promise<Coach[]> {
  try {
    const params = new URLSearchParams();
    if (name) params.append('name', name);
    if (clubName) params.append('club_name', clubName);

    const url = `${API_BASE}/api/admin/coaches${
      params.toString() ? `?${params.toString()}` : ''
    }`;

    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to search coaches');
    const data = await response.json();
    return data.coaches || [];
  } catch (error) {
    console.error('Error searching coaches:', error);
    throw error;
  }
}

/**
 * Create new coach
 */
export async function createCoach(coachData: CoachFormData): Promise<any> {
  try {
    const response = await fetch(`${API_BASE}/api/admin/coaches`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(coachData),
    });

    if (!response.ok) throw new Error('Failed to create coach');
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error creating coach:', error);
    throw error;
  }
}

/**
 * Update existing coach
 */
export async function updateCoach(
  coachId: string,
  coachData: CoachFormData
): Promise<any> {
  try {
    const response = await fetch(`${API_BASE}/api/admin/coaches/${coachId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(coachData),
    });

    if (!response.ok) throw new Error('Failed to update coach');
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error updating coach:', error);
    throw error;
  }
}

/**
 * Delete coach
 */
export async function deleteCoach(coachId: string): Promise<any> {
  try {
    const response = await fetch(`${API_BASE}/api/admin/coaches/${coachId}`, {
      method: 'DELETE',
    });

    if (!response.ok) throw new Error('Failed to delete coach');
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error deleting coach:', error);
    throw error;
  }
}
