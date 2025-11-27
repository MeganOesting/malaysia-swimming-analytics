/**
 * Shared TypeScript types and interfaces for the admin panel
 * Used across all features: athlete, club, coach, meet, manual-entry, file-upload
 */

// ============================================================================
// AUTHENTICATION & STATE
// ============================================================================

export interface AuthState {
  isAuthenticated: boolean;
  password: string;
  error: string;
}

// ============================================================================
// ATHLETES
// ============================================================================

export interface Athlete {
  id: string;
  name: string;
  gender: string;
  birth_date: string | null;
  club_name: string | null;
  state_code: string | null;
  nation: string | null;
}

export interface SelectedAthlete extends Athlete {
  selected: boolean;
  results?: any[];
}

export interface AthleteSearchResult {
  athletes: Athlete[];
}

export interface AthleteDetail extends Athlete {
  aliases?: string[];
  recent_results?: Result[];
}

export interface AthleteUpdateRequest {
  name?: string;
  gender?: string;
  birth_date?: string;
  club_name?: string;
  state_code?: string;
  nation?: string;
}

// ============================================================================
// MEETS & EVENTS
// ============================================================================

export interface Meet {
  id: string;
  name: string;
  alias: string;
  date: string;
  city: string;
  result_count: number;
  category: string;
}

export interface Event {
  id: string;
  distance: number;
  stroke: string;
  gender: string;
}

export interface Result {
  athlete_id: string;
  athlete_name: string;
  event_distance: number;
  event_stroke: string;
  event_gender: string;
  time_string: string;
  place: number | null;
  meet_name?: string;
  aqua_points?: number;
}

// ============================================================================
// MANUAL ENTRY
// ============================================================================

export interface ManualResult {
  athlete_id: string;
  athlete_name: string;
  event_distance: number;
  event_stroke: string;
  event_gender: string;
  time_string: string;
  place: number | null;
}

export interface ManualResultsSubmission {
  meet_name: string;
  meet_date: string;
  meet_city: string;
  meet_course: string;
  meet_alias: string;
  results: ManualResultPayload[];
}

export interface ManualResultPayload {
  athlete_id: string;
  distance: number;
  stroke: string;
  event_gender: string;
  time_string: string;
  place?: number | null;
}

export interface ManualResultsResponse {
  success: boolean;
  meet_id: string;
  results_inserted: number;
  total_results_submitted: number;
  message: string;
  errors?: string[];
}

// ============================================================================
// CLUBS
// ============================================================================

export interface Club {
  name: string;
  state: string;
  short_name?: string;
  country?: string;
}

export interface ClubCreateRequest {
  name: string;
  state: string;
  short_name?: string;
  country?: string;
}

export interface ClubSearchResult {
  clubs: Club[];
}

export interface ClubRoster {
  club_name: string;
  athletes: Athlete[];
}

export interface State {
  code: string;
  name: string;
}

// ============================================================================
// COACHES
// ============================================================================

export interface Coach {
  id?: string;
  name: string;
  email?: string;
  phone?: string;
  club_name?: string;
  specialization?: string;
}

export interface CoachCreateRequest {
  name: string;
  email?: string;
  phone?: string;
  club_name?: string;
  specialization?: string;
}

export interface CoachSearchResult {
  coaches: Coach[];
}

// ============================================================================
// FILE UPLOAD & CONVERSION
// ============================================================================

export interface ConversionResult {
  success: boolean;
  message: string;
  athletes: number;
  results: number;
  events: number;
  meets: number;
}

export interface ValidationIssueDetail {
  sheet?: string;
  row?: string;
  [key: string]: string | undefined;
}

export type ValidationIssues = Record<string, ValidationIssueDetail[]>;

export type UploadStatus = 'pending' | 'processing' | 'success' | 'error';

export interface UploadSummary {
  filename: string;
  status: UploadStatus;
  message: string;
  metrics?: {
    athletes: number;
    results: number;
    events: number;
    meets: number;
  };
  issues?: ValidationIssues;
}

export interface ClubConversionResult {
  success: boolean;
  message: string;
  clubs_created: number;
  clubs_updated: number;
}

export interface AthleteInfoAnalysis {
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  issues: ValidationIssues;
}

// ============================================================================
// API RESPONSES
// ============================================================================

export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data?: T;
  error?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

// ============================================================================
// FORM STATE
// ============================================================================

export interface AthleteFormState {
  id: string;
  name: string;
  gender: string;
  birth_date: string;
  club_name: string;
  state_code: string;
  nation: string;
}

export interface ClubFormState {
  name: string;
  state: string;
  short_name: string;
  country: string;
}

export interface CoachFormState {
  name: string;
  email: string;
  phone: string;
  club_name: string;
  specialization: string;
}

export interface MeetAliasUpdate {
  id: string;
  alias: string;
}

// ============================================================================
// UI STATE
// ============================================================================

export type TabType = 'manual' | 'manage' | 'athleteinfo' | 'clubinfo' | 'coachmanagement' | 'upload';

export interface FormMode {
  mode: 'view' | 'edit' | 'create';
  item?: any;
}

export interface LoadingState {
  [key: string]: boolean;
}

export interface ErrorState {
  [key: string]: string;
}

// ============================================================================
// MANUAL ENTRY WIZARD STATE
// ============================================================================

export type ManualEntryStep = 1 | 2 | 3;

export interface ManualEntryState {
  currentStep: ManualEntryStep;
  selectedAthletes: SelectedAthlete[];
  athleteSearchQuery: string;
  athleteSearchResults: Athlete[];
  searchingAthletes: boolean;
  meetName: string;
  meetDate: string;
  meetCity: string;
  meetCourse: string;
  meetAlias: string;
  manualResults: ManualResult[];
  submitting: boolean;
  successMessage: string;
}

// ============================================================================
// ATHLETE MANAGEMENT STATE
// ============================================================================

export interface AthleteManagementState {
  athleteSearchQuery: string;
  athleteSearchResults: Athlete[];
  searchingAthletes: boolean;
  athleteDetail: AthleteDetail | null;
  athleteFormData: AthleteFormState | null;
  athleteFormMode: FormMode;
  athleteFormMessage: string;
  athleteInfoUploading: boolean;
  athleteInfoAnalysis: AthleteInfoAnalysis | null;
  athleteInfoMessage: string;
}

// ============================================================================
// MEET MANAGEMENT STATE
// ============================================================================

export interface MeetManagementState {
  meets: Meet[];
  loadingMeets: boolean;
  editingAlias: string | null;
  newAlias: string;
  selectedMeetForPdf: string | null;
  generatingPdf: boolean;
}

// ============================================================================
// CLUB MANAGEMENT STATE
// ============================================================================

export interface ClubManagementState {
  states: State[];
  selectedState: string;
  clubs: Club[];
  selectedClub: Club | null;
  clubFormData: ClubFormState | null;
  clubFormMode: FormMode;
  clubFormMessage: string;
  clubSearchQuery: string;
  clubSearchResults: Club[];
  searchingClubs: boolean;
  selectedMeetForRoster: string | null;
  clubRoster: ClubRoster | null;
  loadingRoster: boolean;
}

// ============================================================================
// COACH MANAGEMENT STATE
// ============================================================================

export interface CoachManagementState {
  coaches: Coach[];
  selectedCoach: Coach | null;
  coachFormData: CoachFormState | null;
  coachFormMode: FormMode;
  coachFormMessage: string;
  coachSearchName: string;
  coachSearchClub: string;
  searchingCoaches: boolean;
  loadingCoaches: boolean;
}

// ============================================================================
// FILE UPLOAD STATE
// ============================================================================

export interface FileUploadState {
  uploading: boolean;
  uploadedFiles: File[];
  conversionResult: ConversionResult | null;
  uploadSummaries: UploadSummary[];
  expandedIssueKeys: Set<string>;
  clubUploadMessage: string;
  clubResult: ClubConversionResult | null;
  clubUploading: boolean;
  athleteInfoUploading: boolean;
  athleteInfoAnalysis: AthleteInfoAnalysis | null;
  athleteInfoMessage: string;
}
