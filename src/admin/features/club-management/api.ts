/**
 * Club Management API Functions
 * Handles all API calls related to club management
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

export interface ClubData {
  club_name: string;
  club_code: string;
  state_code: string;
  nation: string;
  alias: string;
}

export interface Club {
  club_name: string;
  club_code?: string;
  state_code?: string;
  nation?: string;
  alias?: string;
}

export interface Coach {
  id: string;
  name: string;
  role: string;
  email?: string;
  whatsapp?: string;
  club_name: string;
}

export interface RosterAthlete {
  fullname: string;
  gender: string;
  year_age?: number;
  day_age?: number;
}

/**
 * Fetch all states
 */
export async function getStates(): Promise<string[]> {
  try {
    const response = await fetch(`${API_BASE}/api/admin/clubs/states`);
    if (!response.ok) throw new Error('Failed to fetch states');
    const data = await response.json();
    return data.states || [];
  } catch (error) {
    console.error('Error fetching states:', error);
    throw error;
  }
}

/**
 * Fetch clubs by state
 */
export async function getClubsByState(stateCode: string): Promise<Club[]> {
  try {
    const response = await fetch(
      `${API_BASE}/api/admin/clubs?state_code=${encodeURIComponent(stateCode)}`
    );
    if (!response.ok) throw new Error('Failed to fetch clubs');
    const data = await response.json();
    return data.clubs || [];
  } catch (error) {
    console.error('Error fetching clubs:', error);
    throw error;
  }
}

/**
 * Create new club
 */
export async function createClub(clubData: ClubData): Promise<any> {
  try {
    const response = await fetch(`${API_BASE}/api/admin/clubs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(clubData),
    });

    if (!response.ok) throw new Error('Failed to create club');
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error creating club:', error);
    throw error;
  }
}

/**
 * Update existing club
 */
export async function updateClub(
  clubName: string,
  clubData: ClubData
): Promise<any> {
  try {
    const response = await fetch(
      `${API_BASE}/api/admin/clubs/${encodeURIComponent(clubName)}`,
      {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(clubData),
      }
    );

    if (!response.ok) throw new Error('Failed to update club');
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error updating club:', error);
    throw error;
  }
}

/**
 * Get coaches for a club
 */
export async function getCoachesByClub(clubName: string): Promise<Coach[]> {
  try {
    const response = await fetch(
      `${API_BASE}/api/admin/coaches?club_name=${encodeURIComponent(clubName)}`
    );
    if (!response.ok) throw new Error('Failed to fetch coaches');
    const data = await response.json();
    return data.coaches || [];
  } catch (error) {
    console.error('Error fetching coaches:', error);
    throw error;
  }
}

/**
 * Get club roster (athletes)
 */
export async function getClubRoster(
  clubName: string,
  meetId?: string
): Promise<RosterAthlete[]> {
  try {
    const params = new URLSearchParams();
    if (meetId) params.append('meet_id', meetId);

    const url = `${API_BASE}/api/admin/clubs/${encodeURIComponent(
      clubName
    )}/roster${params.toString() ? `?${params.toString()}` : ''}`;

    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to fetch roster');
    const data = await response.json();
    return data.roster || [];
  } catch (error) {
    console.error('Error fetching roster:', error);
    throw error;
  }
}

/**
 * Delete a club
 */
export async function deleteClub(clubName: string): Promise<any> {
  try {
    const response = await fetch(
      `${API_BASE}/api/admin/clubs/${encodeURIComponent(clubName)}`,
      {
        method: 'DELETE',
      }
    );

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to delete club');
    }
    return await response.json();
  } catch (error) {
    console.error('Error deleting club:', error);
    throw error;
  }
}
