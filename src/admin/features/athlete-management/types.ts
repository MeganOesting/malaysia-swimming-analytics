/**
 * Athlete Management Feature - TypeScript Types
 * Re-exports shared types and defines feature-specific interfaces
 */

// ============================================================================
// RE-EXPORT SHARED TYPES (used by this feature)
// ============================================================================

export type {
  Athlete,
  SelectedAthlete,
  AthleteSearchResult,
  AthleteDetail,
  AthleteUpdateRequest,
  AthleteInfoAnalysis,
} from '../../shared/types/admin';

// ============================================================================
// FEATURE-SPECIFIC TYPES
// ============================================================================

/**
 * Props passed to the AthleteManagement component
 */
export interface AthleteManagementProps {
  isAuthenticated: boolean;
}

/**
 * Search filter options for athlete results
 */
export interface AthleteResultsFilter {
  startDate?: string;
  endDate?: string;
  bestOnly?: boolean;
}

/**
 * Athlete result entry with complete details
 */
export interface AthleteResultEntry {
  distance: number;
  stroke: string;
  time: string | null;
  place: number | null;
  meet_name: string | null;
  meet_date: string | null;
  club_name: string | null;
  state_code: string | null;
}

/**
 * State for the search UI
 */
export interface AthleteSearchState {
  query: string;
  results: any[];
  isLoading: boolean;
}

/**
 * State for the upload UI
 */
export interface AthleteInfoUploadState {
  isUploading: boolean;
  analysis: any | null;
  showModal: boolean;
}
