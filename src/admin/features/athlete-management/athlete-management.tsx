import React, { useState } from 'react';
import { Athlete } from '../../shared/types/admin';
import { Button } from '../../shared/components';

// Helper function to format dates as dd MMM yyyy (e.g., 15 Mar 1998)
const formatDateDDMMMYYYY = (dateString: string | null | undefined): string => {
  if (!dateString) return '-';
  try {
    // Handle ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DD)
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '-';

    const day = String(date.getDate()).padStart(2, '0');
    const monthAbbr = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][date.getMonth()];
    const year = date.getFullYear();

    return `${day} ${monthAbbr} ${year}`;
  } catch {
    return '-';
  }
};

// Malaysian state codes
const MALAYSIAN_STATES = [
  { code: 'JHR', name: 'Johor' },
  { code: 'KDH', name: 'Kedah' },
  { code: 'KTN', name: 'Kelantan' },
  { code: 'MLK', name: 'Melaka' },
  { code: 'NSN', name: 'Negeri Sembilan' },
  { code: 'PHG', name: 'Pahang' },
  { code: 'PRK', name: 'Perak' },
  { code: 'PLS', name: 'Perlis' },
  { code: 'PNG', name: 'Pulau Pinang' },
  { code: 'SBH', name: 'Sabah' },
  { code: 'SWK', name: 'Sarawak' },
  { code: 'SEL', name: 'Selangor' },
  { code: 'TRG', name: 'Terengganu' },
  { code: 'KUL', name: 'WP Kuala Lumpur' },
  { code: 'LBN', name: 'WP Labuan' },
  { code: 'PJY', name: 'WP Putrajaya' },
];

// IOC country codes (MAS first, then alphabetical)
const IOC_COUNTRY_CODES = [
  'MAS',  // Malaysia first
  'AFG', 'ALB', 'ALG', 'AND', 'ANG', 'ANT', 'ARG', 'ARM', 'ARU', 'ASA', 'AUS', 'AUT', 'AZE',
  'BAH', 'BAN', 'BAR', 'BDI', 'BEL', 'BEN', 'BER', 'BHU', 'BIH', 'BIZ', 'BLR', 'BOL', 'BOT',
  'BRA', 'BRN', 'BRU', 'BUL', 'BUR', 'CAF', 'CAM', 'CAN', 'CAY', 'CGO', 'CHA', 'CHI', 'CHN',
  'CIV', 'CMR', 'COD', 'COK', 'COL', 'COM', 'CPV', 'CRC', 'CRO', 'CUB', 'CYP', 'CZE',
  'DEN', 'DJI', 'DMA', 'DOM', 'ECU', 'EGY', 'ERI', 'ESA', 'ESP', 'EST', 'ETH', 'FIJ', 'FIN',
  'FRA', 'FSM', 'GAB', 'GAM', 'GBR', 'GBS', 'GEO', 'GEQ', 'GER', 'GHA', 'GRE', 'GRN', 'GUA',
  'GUI', 'GUM', 'GUY', 'HAI', 'HKG', 'HON', 'HUN', 'INA', 'IND', 'IRI', 'IRL', 'IRQ', 'ISL',
  'ISR', 'ISV', 'ITA', 'IVB', 'JAM', 'JOR', 'JPN', 'KAZ', 'KEN', 'KGZ', 'KIR', 'KOR', 'KOS',
  'KSA', 'KUW', 'LAO', 'LAT', 'LBA', 'LBN', 'LBR', 'LCA', 'LES', 'LIE', 'LTU', 'LUX',
  'MAD', 'MAR', 'MAW', 'MDA', 'MDV', 'MEX', 'MGL', 'MHL', 'MKD', 'MLI', 'MLT', 'MNE',
  'MON', 'MOZ', 'MRI', 'MTN', 'MYA', 'NAM', 'NCA', 'NED', 'NEP', 'NGR', 'NIG', 'NOR', 'NRU',
  'NZL', 'OMA', 'PAK', 'PAN', 'PAR', 'PER', 'PHI', 'PLE', 'PLW', 'PNG', 'POL', 'POR', 'PRK',
  'PUR', 'QAT', 'ROU', 'RSA', 'RUS', 'RWA', 'SAM', 'SEN', 'SEY', 'SGP', 'SKN', 'SLE', 'SLO',
  'SMR', 'SOL', 'SOM', 'SRB', 'SRI', 'SSD', 'STP', 'SUD', 'SUI', 'SUR', 'SVK', 'SWE', 'SWZ',
  'SYR', 'TAN', 'TGA', 'THA', 'TJK', 'TKM', 'TLS', 'TOG', 'TPE', 'TTO', 'TUN', 'TUR', 'TUV',
  'UAE', 'UGA', 'UKR', 'URU', 'USA', 'UZB', 'VAN', 'VEN', 'VIE', 'VIN', 'YEM', 'ZAM', 'ZIM',
];

interface AthleteManagementProps {
  isAuthenticated: boolean;
}

export const AthleteManagement: React.FC<AthleteManagementProps> = ({ isAuthenticated }) => {
  const [athleteSearchQuery, setAthleteSearchQuery] = useState('');
  const [athleteSearchResults, setAthleteSearchResults] = useState<Athlete[]>([]);
  const [searchingAthletes, setSearchingAthletes] = useState(false);
  const [selectedAthlete, setSelectedAthlete] = useState<Athlete | null>(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);
  const [fieldsToEdit, setFieldsToEdit] = useState<Set<string>>(new Set());
  const [isEditingMode, setIsEditingMode] = useState(false);
  const [clubsForState, setClubsForState] = useState<{club_code: string, club_name: string}[]>([]);
  const [loadingAthleteDetails, setLoadingAthleteDetails] = useState(false);
  const [editForm, setEditForm] = useState<{
    FULLNAME: string;
    FIRSTNAME: string;
    LASTNAME: string;
    MIDDLEINITIAL: string;
    SUFFIX: string;
    IC: string;
    NATION: string;
    MembEmail: string;
    PreferredName: string;
    Phone: string;
    AcctFirstName: string;
    AcctLastName: string;
    AcctMiddleInitial: string;
    Address: string;
    Address2: string;
    City: string;
    EmergencyContact: string;
    EmergencyPhone: string;
    Guardian1FirstName: string;
    Guardian1HomePhone: string;
    Guardian1LastName: string;
    Guardian1MobilePhone: string;
    Guardian1WorkPhone: string;
    Guardian2FirstName: string;
    Guardian2HomePhone: string;
    Guardian2LastName: string;
    Guardian2MobilePhone: string;
    Guardian2WorkPhone: string;
    AcctIC: string;
    Gender: string;
    state_code: string;
    club_code: string;
    club_name: string;
    athlete_alias_1: string;
    athlete_alias_2: string;
    passport_number: string;
    shoe_size: string;
    tshirt_size: string;
    tracksuit_size: string;
    cap_name: string;
    School_University_Name: string;
    School_University_Address: string;
    passport_expiry_date: string;
    BIRTHDATE: string;
    postal_code: string;
    address_state: string;
  }>({
    FULLNAME: '',
    FIRSTNAME: '',
    LASTNAME: '',
    MIDDLEINITIAL: '',
    SUFFIX: '',
    IC: '',
    NATION: '',
    MembEmail: '',
    PreferredName: '',
    Phone: '',
    AcctFirstName: '',
    AcctLastName: '',
    AcctMiddleInitial: '',
    Address: '',
    Address2: '',
    City: '',
    EmergencyContact: '',
    EmergencyPhone: '',
    Guardian1FirstName: '',
    Guardian1HomePhone: '',
    Guardian1LastName: '',
    Guardian1MobilePhone: '',
    Guardian1WorkPhone: '',
    Guardian2FirstName: '',
    Guardian2HomePhone: '',
    Guardian2LastName: '',
    Guardian2MobilePhone: '',
    Guardian2WorkPhone: '',
    AcctIC: '',
    Gender: '',
    state_code: '',
    club_code: '',
    club_name: '',
    athlete_alias_1: '',
    athlete_alias_2: '',
    passport_number: '',
    shoe_size: '',
    tshirt_size: '',
    tracksuit_size: '',
    cap_name: '',
    School_University_Name: '',
    School_University_Address: '',
    passport_expiry_date: '',
    BIRTHDATE: '',
    postal_code: '',
    address_state: '',
  });

  const availableFields = [
    // Core Information
    { key: 'FULLNAME', label: 'Full Name' },
    { key: 'FIRSTNAME', label: 'First Name' },
    { key: 'LASTNAME', label: 'Last Name' },
    { key: 'MIDDLEINITIAL', label: 'Middle Initial' },
    { key: 'SUFFIX', label: 'Suffix' },
    { key: 'Gender', label: 'Gender' },
    { key: 'BIRTHDATE', label: 'Birthdate' },
    // Contact Information
    { key: 'MembEmail', label: 'Member Email' },
    { key: 'Phone', label: 'Phone' },
    { key: 'PreferredName', label: 'Preferred Name' },
    { key: 'EmergencyContact', label: 'Emergency Contact' },
    { key: 'EmergencyPhone', label: 'Emergency Phone' },
    // Identification
    { key: 'IC', label: 'IC Number' },
    { key: 'AcctIC', label: 'Account IC' },
    { key: 'passport_number', label: 'Passport Number' },
    { key: 'passport_expiry_date', label: 'Passport Expiry Date' },
    // Account Information
    { key: 'AcctFirstName', label: 'Account First Name' },
    { key: 'AcctLastName', label: 'Account Last Name' },
    { key: 'AcctMiddleInitial', label: 'Account Middle Initial' },
    // Address Information
    { key: 'Address', label: 'Address' },
    { key: 'Address2', label: 'Address 2' },
    { key: 'City', label: 'City' },
    // Guardian Information
    { key: 'Guardian1FirstName', label: 'Guardian 1 First Name' },
    { key: 'Guardian1LastName', label: 'Guardian 1 Last Name' },
    { key: 'Guardian1HomePhone', label: 'Guardian 1 Home Phone' },
    { key: 'Guardian1MobilePhone', label: 'Guardian 1 Mobile Phone' },
    { key: 'Guardian1WorkPhone', label: 'Guardian 1 Work Phone' },
    { key: 'Guardian2FirstName', label: 'Guardian 2 First Name' },
    { key: 'Guardian2LastName', label: 'Guardian 2 Last Name' },
    { key: 'Guardian2HomePhone', label: 'Guardian 2 Home Phone' },
    { key: 'Guardian2MobilePhone', label: 'Guardian 2 Mobile Phone' },
    { key: 'Guardian2WorkPhone', label: 'Guardian 2 Work Phone' },
    // State, Club & Nation
    { key: 'state_code', label: 'State' },
    { key: 'club_name', label: 'Club' },
    { key: 'NATION', label: 'Nation' },
    // Athlete Aliases
    { key: 'athlete_alias_1', label: 'Alias 1' },
    { key: 'athlete_alias_2', label: 'Alias 2' },
    // Size Information
    { key: 'shoe_size', label: 'Shoe Size' },
    { key: 'tshirt_size', label: 'T-Shirt Size' },
    { key: 'tracksuit_size', label: 'Tracksuit Size' },
    { key: 'cap_name', label: 'Cap Name' },
    // Education
    { key: 'School_University_Name', label: 'School/University Name' },
    { key: 'School_University_Address', label: 'School/University Address' },
  ];

  const searchAthletes = async (query: string) => {
    if (query.length < 2) {
      setAthleteSearchResults([]);
      return;
    }

    setSearchingAthletes(true);
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
      const response = await fetch(`${apiBase}/api/admin/athletes/search?q=${encodeURIComponent(query)}`);
      const data = await response.json();
      setAthleteSearchResults(data.athletes || []);
    } catch (err: any) {
      setError(`Failed to search athletes: ${err.message}`);
      console.error('Search error:', err);
    } finally {
      setSearchingAthletes(false);
    }
  };

  const fetchClubsByState = async (stateCode: string) => {
    if (!stateCode) {
      setClubsForState([]);
      return;
    }
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
      const response = await fetch(`${apiBase}/api/clubs?state_code=${encodeURIComponent(stateCode)}`);
      if (response.ok) {
        const data = await response.json();
        // API returns {code, name} but we need {club_code, club_name}
        const mappedClubs = (data.clubs || []).map((c: any) => ({
          club_code: c.code || c.club_code,
          club_name: c.name || c.club_name
        }));
        setClubsForState(mappedClubs);
      }
    } catch (err) {
      console.error('Failed to fetch clubs:', err);
      setClubsForState([]);
    }
  };

  const handleExportAthletes = async () => {
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
      const response = await fetch(`${apiBase}/api/admin/athletes/export-excel`);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to export athletes: ${response.status} ${errorText}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'athletes_export.xlsx';
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.message);
      console.error('Export error:', err);
    }
  };

  const handleExportForeignAthletes = async () => {
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
      const response = await fetch(`${apiBase}/api/admin/foreign-athletes/export-excel`);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to export foreign athletes: ${response.status} ${errorText}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'foreign_athletes_export.xlsx';
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.message);
      console.error('Export error:', err);
    }
  };

  const handleCopyId = (id: string) => {
    navigator.clipboard.writeText(id);
    // Show brief feedback
    const feedback = document.createElement('div');
    feedback.textContent = 'Athlete ID copied!';
    feedback.style.position = 'fixed';
    feedback.style.top = '20px';
    feedback.style.right = '20px';
    feedback.style.backgroundColor = '#059669';
    feedback.style.color = 'white';
    feedback.style.padding = '0.5rem 1rem';
    feedback.style.borderRadius = '4px';
    feedback.style.zIndex = '9999';
    document.body.appendChild(feedback);
    setTimeout(() => feedback.remove(), 2000);
  };

  const handleSelectAthlete = async (athlete: Athlete) => {
    // Set basic info immediately from search results
    setSelectedAthlete(athlete);
    setFieldsToEdit(new Set());
    setIsEditingMode(false);
    setError('');
    setSuccess('');
    setLoadingAthleteDetails(true);

    // Fetch full athlete details from API
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
      const response = await fetch(`${apiBase}/api/admin/athletes/${athlete.id}`);
      if (!response.ok) {
        throw new Error('Failed to fetch athlete details');
      }
      const data = await response.json();
      const fullAthlete = data.athlete;

      // Check if IC looks like a passport number and passport_number is empty
      const isPassportInIC = (ic: string) => {
        if (!ic) return false;
        const cleaned = ic.replace(/[-\s]/g, '');
        // Has letters = passport
        if (/[a-zA-Z]/.test(cleaned)) return true;
        // 7-9 digit number = passport
        if (cleaned.length >= 7 && cleaned.length <= 9 && /^\d+$/.test(cleaned)) return true;
        return false;
      };

      let icValue = fullAthlete.IC || '';
      let passportValue = fullAthlete.passport_number || '';

      // Auto-move passport from IC field if detected
      if (icValue && !passportValue && isPassportInIC(icValue)) {
        passportValue = icValue;
        icValue = '';
        // Note: This only affects the form, not the database. User needs to save.
      }

      // Update selected athlete with full details
      setSelectedAthlete({ ...athlete, ...fullAthlete });

      // Populate form with all fields from the full record
      setEditForm({
        FULLNAME: fullAthlete.FULLNAME || '',
        FIRSTNAME: fullAthlete.FIRSTNAME || '',
        LASTNAME: fullAthlete.LASTNAME || '',
        MIDDLEINITIAL: fullAthlete.MIDDLEINITIAL || '',
        SUFFIX: fullAthlete.SUFFIX || '',
        IC: icValue,
        NATION: fullAthlete.nation || fullAthlete.NATION || '',
        MembEmail: fullAthlete.MembEmail || '',
        PreferredName: fullAthlete.PreferredName || '',
        Phone: fullAthlete.Phone || '',
        AcctFirstName: fullAthlete.AcctFirstName || '',
        AcctLastName: fullAthlete.AcctLastName || '',
        AcctMiddleInitial: fullAthlete.AcctMiddleInitial || '',
        Address: fullAthlete.Address || '',
        Address2: fullAthlete.Address2 || '',
        City: fullAthlete.City || '',
        EmergencyContact: fullAthlete.EmergencyContact || '',
        EmergencyPhone: fullAthlete.EmergencyPhone || '',
        Guardian1FirstName: fullAthlete.Guardian1FirstName || '',
        Guardian1HomePhone: fullAthlete.Guardian1HomePhone || '',
        Guardian1LastName: fullAthlete.Guardian1LastName || '',
        Guardian1MobilePhone: fullAthlete.Guardian1MobilePhone || '',
        Guardian1WorkPhone: fullAthlete.Guardian1WorkPhone || '',
        Guardian2FirstName: fullAthlete.Guardian2FirstName || '',
        Guardian2HomePhone: fullAthlete.Guardian2HomePhone || '',
        Guardian2LastName: fullAthlete.Guardian2LastName || '',
        Guardian2MobilePhone: fullAthlete.Guardian2MobilePhone || '',
        Guardian2WorkPhone: fullAthlete.Guardian2WorkPhone || '',
        AcctIC: fullAthlete.AcctIC || '',
        Gender: fullAthlete.Gender || fullAthlete.gender || '',
        state_code: fullAthlete.state_code || '',
        club_code: fullAthlete.club_code || '',
        club_name: fullAthlete.club_name || '',
        athlete_alias_1: fullAthlete.athlete_alias_1 || '',
        athlete_alias_2: fullAthlete.athlete_alias_2 || '',
        passport_number: passportValue,
        shoe_size: fullAthlete.shoe_size || '',
        tshirt_size: fullAthlete.tshirt_size || '',
        tracksuit_size: fullAthlete.tracksuit_size || '',
        cap_name: fullAthlete.cap_name || '',
        School_University_Name: fullAthlete.School_University_Name || '',
        School_University_Address: fullAthlete.School_University_Address || '',
        passport_expiry_date: fullAthlete.passport_expiry_date || '',
        BIRTHDATE: fullAthlete.BIRTHDATE || fullAthlete.birth_date || '',
        postal_code: fullAthlete.postal_code || '',
        address_state: fullAthlete.address_state || '',
      });

      // Fetch clubs for athlete's state
      if (fullAthlete.state_code) {
        fetchClubsByState(fullAthlete.state_code);
      }
    } catch (err: any) {
      console.error('Failed to fetch athlete details:', err);
      setError('Failed to load full athlete details');
    } finally {
      setLoadingAthleteDetails(false);
    }
  };

  const toggleFieldSelection = (fieldKey: string) => {
    const newFields = new Set(fieldsToEdit);
    if (newFields.has(fieldKey)) {
      newFields.delete(fieldKey);
    } else {
      newFields.add(fieldKey);
    }
    setFieldsToEdit(newFields);
  };

  const handleStartEditing = () => {
    if (fieldsToEdit.size === 0) {
      setError('Please select at least one field to edit');
      return;
    }
    setIsEditingMode(true);
  };

  const handleUpdateAthlete = async () => {
    if (!selectedAthlete) return;

    setIsUpdating(true);
    try {
      // Send all fields from editForm
      const updateData: Record<string, any> = {};
      availableFields.forEach(field => {
        updateData[field.key] = (editForm as any)[field.key] || '';
      });

      const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
      const response = await fetch(`${apiBase}/api/admin/athletes/${selectedAthlete.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to update athlete: ${response.status} ${errorText}`);
      }

      setSuccess(`Athlete "${editForm.FULLNAME || selectedAthlete.name}" updated successfully!`);
      // Update the selected athlete and search results
      const updated = { ...selectedAthlete, ...editForm };
      setSelectedAthlete(updated);
      setAthleteSearchResults(
        athleteSearchResults.map(a => (a.id === selectedAthlete.id ? updated : a))
      );
    } catch (err: any) {
      setError(`Failed to update athlete: ${err.message}`);
      console.error('Update error:', err);
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <div>
      {success && (
        <div style={{ padding: '0.75rem', marginBottom: '1rem', backgroundColor: '#ecfdf5', color: '#065f46', fontSize: '0.875rem', borderRadius: '4px' }}>
          ✓ {success}
        </div>
      )}

      {/* Export Athletes Section */}
      <div style={{ marginTop: '1.5rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <button
          onClick={handleExportAthletes}
          style={{
            padding: '2px 10px',
            backgroundColor: '#cc0000',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            fontSize: '0.9em',
            cursor: 'pointer',
            whiteSpace: 'nowrap',
            display: 'inline-block',
          }}
        >
          Export MAS Registered Athletes Table
        </button>

        <button
          onClick={handleExportForeignAthletes}
          style={{
            padding: '2px 10px',
            backgroundColor: '#cc0000',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            fontSize: '0.9em',
            cursor: 'pointer',
            whiteSpace: 'nowrap',
            display: 'inline-block',
          }}
        >
          Export Foreign Athletes Table
        </button>
      </div>

      {/* Search Athletes Section */}
      <div>
        <h3 style={{ fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.5rem', color: '#111' }}>
          Search Athletes by Name
        </h3>
        <p style={{ fontSize: '0.75rem', color: '#666', marginBottom: '0.75rem' }}>
          Enter partial name words to find potential matches
        </p>
        <div style={{ marginBottom: '0.75rem' }}>
          <input
            type="text"
            value={athleteSearchQuery}
            onChange={(e) => {
              setAthleteSearchQuery(e.target.value);
              searchAthletes(e.target.value);
              // Clear selected athlete when user starts typing to show search results
              if (selectedAthlete) {
                setSelectedAthlete(null);
              }
            }}
            placeholder="e.g., MUHAMMAD or DHUHA or CHNG..."
            style={{
              width: '100%',
              padding: '0.5rem',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontSize: '0.875rem',
              boxSizing: 'border-box'
            }}
          />
        </div>

        {searchingAthletes && <p style={{ color: '#666' }}>Searching...</p>}

        {athleteSearchResults.length > 0 && !selectedAthlete && (
          <div style={{
            border: '1px solid #ddd',
            borderRadius: '4px',
            maxHeight: '400px',
            overflowY: 'auto'
          }}>
            <div style={{
              padding: '0.5rem',
              backgroundColor: '#f9fafb',
              borderBottom: '1px solid #ddd',
              fontSize: '0.75rem',
              color: '#666',
              fontWeight: '500'
            }}>
              {athleteSearchResults.length} result{athleteSearchResults.length !== 1 ? 's' : ''}
            </div>
            {athleteSearchResults.map(athlete => (
              <div
                key={athlete.id}
                style={{
                  padding: '0.4rem 0.75rem',
                  borderBottom: '1px solid #eee',
                  backgroundColor: '#ffffff',
                  cursor: 'pointer',
                  transition: 'background-color 0.2s',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}
                onClick={() => handleSelectAthlete(athlete)}
              >
                <input
                  type="radio"
                  name="athlete-selection"
                  checked={false}
                  onChange={() => handleSelectAthlete(athlete)}
                  style={{ cursor: 'pointer', flexShrink: 0 }}
                />
                <div style={{ fontWeight: '600', fontSize: '0.8rem', color: '#111', width: '220px', flexShrink: 0 }}>
                  {athlete.name}
                </div>
                <div style={{
                  fontFamily: 'monospace',
                  color: '#cc0000',
                  fontWeight: '600',
                  fontSize: '0.65rem',
                  width: '70px',
                  flexShrink: 0
                }}>
                  ID: {athlete.id}
                </div>
                <div style={{ color: '#000', fontSize: '0.7rem', width: '90px', flexShrink: 0 }}>
                  {formatDateDDMMMYYYY(athlete.birth_date) || '-'}
                </div>
                <div style={{ color: '#000', fontSize: '0.7rem', width: '20px', flexShrink: 0 }}>
                  {athlete.gender || '-'}
                </div>
              </div>
            ))}
          </div>
        )}

        {athleteSearchQuery.length > 0 && !searchingAthletes && athleteSearchResults.length === 0 && (
          <div style={{ padding: '0.75rem', backgroundColor: '#eff6ff', color: '#1e40af', fontSize: '0.875rem', borderRadius: '4px' }}>
            ℹ No athletes found matching "{athleteSearchQuery}"
          </div>
        )}
      </div>

      {/* Edit Selected Athlete Section - Per-field editing with confirmation */}
      {selectedAthlete && (
        <div style={{ marginTop: '1.5rem', paddingTop: '1rem', borderTop: '2px solid #ddd' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: '#111', margin: 0 }}>
              Edit: {selectedAthlete.name}
              {loadingAthleteDetails && <span style={{ marginLeft: '0.5rem', color: '#666', fontWeight: 'normal', fontSize: '0.75rem' }}>(Loading details...)</span>}
            </h3>
            <button
              onClick={() => setSelectedAthlete(null)}
              style={{
                padding: '0.4rem 0.75rem',
                backgroundColor: '#6b7280',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.75rem',
                fontWeight: '600'
              }}
            >
              Close
            </button>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '0.4rem',
            fontSize: '0.75rem'
          }}>
            {availableFields.map(field => {
              const currentValue = (editForm as any)[field.key] || '';
              // Map field keys to actual selectedAthlete property names
              const getOriginalValue = () => {
                if (field.key === 'BIRTHDATE') return (selectedAthlete as any).birth_date || '';
                if (field.key === 'Gender') return (selectedAthlete as any).gender || '';
                if (field.key === 'NATION') return (selectedAthlete as any).nation || '';
                if (field.key === 'club_name') return (selectedAthlete as any).club_name || '';
                if (field.key === 'state_code') return (selectedAthlete as any).state_code || '';
                return (selectedAthlete as any)[field.key] || '';
              };
              const originalValue = getOriginalValue();

              // Birthdate field - 3 dropdowns (day, month, year)
              if (field.key === 'BIRTHDATE') {
                const parsed = currentValue ? new Date(currentValue) : null;
                const originalParsed = originalValue ? new Date(originalValue) : null;
                const currentDay = parsed && !isNaN(parsed.getTime()) ? parsed.getDate() : '';
                const currentMonth = parsed && !isNaN(parsed.getTime()) ? parsed.getMonth() : '';
                const currentYear = parsed && !isNaN(parsed.getTime()) ? parsed.getFullYear() : '';
                const originalDay = originalParsed && !isNaN(originalParsed.getTime()) ? originalParsed.getDate() : '';
                const originalMonth = originalParsed && !isNaN(originalParsed.getTime()) ? originalParsed.getMonth() : '';
                const originalYear = originalParsed && !isNaN(originalParsed.getTime()) ? originalParsed.getFullYear() : '';
                const isDayChanged = currentDay !== originalDay;
                const isMonthChanged = currentMonth !== originalMonth;
                const isYearChanged = currentYear !== originalYear;

                return (
                  <div key={field.key} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', gridColumn: 'span 2' }}>
                    <label style={{ color: '#111', fontWeight: '500', minWidth: '80px', flexShrink: 0 }}>
                      {field.label}:
                    </label>
                    <select
                      value={currentDay}
                      onChange={(e) => {
                        const d = parsed || new Date();
                        d.setDate(parseInt(e.target.value) || 1);
                        setEditForm({ ...editForm, [field.key]: d.toISOString() });
                      }}
                      style={{ padding: '0.2rem', border: '1px solid #ddd', borderRadius: '3px', fontSize: '0.7rem', color: isDayChanged ? '#111' : '#888' }}
                    >
                      <option value="" style={{ color: '#111' }}>DD</option>
                      {Array.from({ length: 31 }, (_, i) => i + 1).map(d => (
                        <option key={d} value={d} style={{ color: '#111' }}>{d}</option>
                      ))}
                    </select>
                    <select
                      value={currentMonth}
                      onChange={(e) => {
                        const d = parsed || new Date();
                        d.setMonth(parseInt(e.target.value));
                        setEditForm({ ...editForm, [field.key]: d.toISOString() });
                      }}
                      style={{ padding: '0.2rem', border: '1px solid #ddd', borderRadius: '3px', fontSize: '0.7rem', color: isMonthChanged ? '#111' : '#888' }}
                    >
                      <option value="" style={{ color: '#111' }}>MMM</option>
                      {['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].map((m, i) => (
                        <option key={m} value={i} style={{ color: '#111' }}>{m}</option>
                      ))}
                    </select>
                    <select
                      value={currentYear}
                      onChange={(e) => {
                        const d = parsed || new Date();
                        d.setFullYear(parseInt(e.target.value) || 2000);
                        setEditForm({ ...editForm, [field.key]: d.toISOString() });
                      }}
                      style={{ padding: '0.2rem', border: '1px solid #ddd', borderRadius: '3px', fontSize: '0.7rem', color: isYearChanged ? '#111' : '#888' }}
                    >
                      <option value="" style={{ color: '#111' }}>YYYY</option>
                      {Array.from({ length: 100 }, (_, i) => 2024 - i).map(y => (
                        <option key={y} value={y} style={{ color: '#111' }}>{y}</option>
                      ))}
                    </select>
                    <button
                      onClick={async () => {
                        const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
                        try {
                          const response = await fetch(`${apiBase}/api/admin/athletes/${selectedAthlete.id}`, {
                            method: 'PATCH',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ [field.key]: currentValue }),
                          });
                          if (response.ok) {
                            setSuccess(`${field.label} updated!`);
                            setSelectedAthlete({ ...selectedAthlete, birth_date: currentValue });
                          } else {
                            setError(`Failed to update ${field.label}`);
                          }
                        } catch (err) {
                          setError(`Failed to update ${field.label}`);
                        }
                      }}
                      style={{
                        padding: '0.2rem 0.4rem',
                        backgroundColor: '#cc0000',
                        color: 'white',
                        border: 'none',
                        borderRadius: '3px',
                        cursor: 'pointer',
                        fontSize: '0.65rem',
                        fontWeight: '600'
                      }}
                    >
                      Update
                    </button>
                  </div>
                );
              }

              // Gender field - dropdown
              if (field.key === 'Gender') {
                const isChanged = currentValue !== originalValue;
                return (
                  <div key={field.key} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                    <label style={{ color: '#111', fontWeight: '500', minWidth: '80px', flexShrink: 0 }}>
                      {field.label}:
                    </label>
                    <select
                      value={currentValue}
                      onChange={(e) => setEditForm({ ...editForm, [field.key]: e.target.value })}
                      style={{ padding: '0.2rem', border: '1px solid #ddd', borderRadius: '3px', fontSize: '0.7rem', color: isChanged ? '#111' : '#888' }}
                    >
                      <option value="M" style={{ color: '#111' }}>M</option>
                      <option value="F" style={{ color: '#111' }}>F</option>
                    </select>
                    <button
                      onClick={async () => {
                        const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
                        try {
                          const response = await fetch(`${apiBase}/api/admin/athletes/${selectedAthlete.id}`, {
                            method: 'PATCH',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ [field.key]: currentValue }),
                          });
                          if (response.ok) {
                            setSuccess(`${field.label} updated!`);
                            setSelectedAthlete({ ...selectedAthlete, gender: currentValue });
                          } else {
                            setError(`Failed to update ${field.label}`);
                          }
                        } catch (err) {
                          setError(`Failed to update ${field.label}`);
                        }
                      }}
                      style={{
                        padding: '0.2rem 0.4rem',
                        backgroundColor: '#cc0000',
                        color: 'white',
                        border: 'none',
                        borderRadius: '3px',
                        cursor: 'pointer',
                        fontSize: '0.65rem',
                        fontWeight: '600'
                      }}
                    >
                      Update
                    </button>
                  </div>
                );
              }

              // Passport Expiry Date field - dropdowns like birthdate
              if (field.key === 'passport_expiry_date') {
                const parsed = currentValue ? new Date(currentValue) : null;
                const originalParsed = originalValue ? new Date(originalValue) : null;
                const currentDay = parsed && !isNaN(parsed.getTime()) ? parsed.getDate() : '';
                const currentMonth = parsed && !isNaN(parsed.getTime()) ? parsed.getMonth() : '';
                const currentYear = parsed && !isNaN(parsed.getTime()) ? parsed.getFullYear() : '';
                const originalDay = originalParsed && !isNaN(originalParsed.getTime()) ? originalParsed.getDate() : '';
                const originalMonth = originalParsed && !isNaN(originalParsed.getTime()) ? originalParsed.getMonth() : '';
                const originalYear = originalParsed && !isNaN(originalParsed.getTime()) ? originalParsed.getFullYear() : '';
                const isDayChanged = currentDay !== originalDay;
                const isMonthChanged = currentMonth !== originalMonth;
                const isYearChanged = currentYear !== originalYear;

                return (
                  <div key={field.key} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', gridColumn: 'span 2' }}>
                    <label style={{ color: '#111', fontWeight: '500', minWidth: '80px', flexShrink: 0 }}>
                      {field.label}:
                    </label>
                    <select
                      value={currentDay}
                      onChange={(e) => {
                        const d = parsed || new Date();
                        d.setDate(parseInt(e.target.value) || 1);
                        setEditForm({ ...editForm, [field.key]: d.toISOString() });
                      }}
                      style={{ padding: '0.2rem', border: '1px solid #ddd', borderRadius: '3px', fontSize: '0.7rem', color: isDayChanged ? '#111' : '#888' }}
                    >
                      <option value="" style={{ color: '#111' }}>DD</option>
                      {Array.from({ length: 31 }, (_, i) => i + 1).map(d => (
                        <option key={d} value={d} style={{ color: '#111' }}>{d}</option>
                      ))}
                    </select>
                    <select
                      value={currentMonth}
                      onChange={(e) => {
                        const d = parsed || new Date();
                        d.setMonth(parseInt(e.target.value));
                        setEditForm({ ...editForm, [field.key]: d.toISOString() });
                      }}
                      style={{ padding: '0.2rem', border: '1px solid #ddd', borderRadius: '3px', fontSize: '0.7rem', color: isMonthChanged ? '#111' : '#888' }}
                    >
                      <option value="" style={{ color: '#111' }}>MMM</option>
                      {['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].map((m, i) => (
                        <option key={m} value={i} style={{ color: '#111' }}>{m}</option>
                      ))}
                    </select>
                    <select
                      value={currentYear}
                      onChange={(e) => {
                        const d = parsed || new Date();
                        d.setFullYear(parseInt(e.target.value) || 2025);
                        setEditForm({ ...editForm, [field.key]: d.toISOString() });
                      }}
                      style={{ padding: '0.2rem', border: '1px solid #ddd', borderRadius: '3px', fontSize: '0.7rem', color: isYearChanged ? '#111' : '#888' }}
                    >
                      <option value="" style={{ color: '#111' }}>YYYY</option>
                      {Array.from({ length: 20 }, (_, i) => 2025 + i).map(y => (
                        <option key={y} value={y} style={{ color: '#111' }}>{y}</option>
                      ))}
                    </select>
                    <button
                      onClick={async () => {
                        const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
                        try {
                          const response = await fetch(`${apiBase}/api/admin/athletes/${selectedAthlete.id}`, {
                            method: 'PATCH',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ [field.key]: currentValue }),
                          });
                          if (response.ok) {
                            setSuccess(`${field.label} updated!`);
                            setSelectedAthlete({ ...selectedAthlete, [field.key]: currentValue });
                          } else {
                            setError(`Failed to update ${field.label}`);
                          }
                        } catch (err) {
                          setError(`Failed to update ${field.label}`);
                        }
                      }}
                      style={{
                        padding: '0.2rem 0.4rem',
                        backgroundColor: '#cc0000',
                        color: 'white',
                        border: 'none',
                        borderRadius: '3px',
                        cursor: 'pointer',
                        fontSize: '0.65rem',
                        fontWeight: '600'
                      }}
                    >
                      Update
                    </button>
                  </div>
                );
              }

              // State Code field - dropdown
              if (field.key === 'state_code') {
                const isChanged = currentValue !== originalValue;
                return (
                  <div key={field.key} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                    <label style={{ color: '#111', fontWeight: '500', minWidth: '80px', flexShrink: 0 }}>
                      {field.label}:
                    </label>
                    <select
                      value={currentValue}
                      onChange={(e) => {
                        setEditForm({ ...editForm, [field.key]: e.target.value });
                        fetchClubsByState(e.target.value);
                      }}
                      style={{ padding: '0.2rem', border: '1px solid #ddd', borderRadius: '3px', fontSize: '0.7rem', color: isChanged ? '#111' : '#888' }}
                    >
                      <option value="" style={{ color: '#111' }}>Select State</option>
                      {MALAYSIAN_STATES.map(state => (
                        <option key={state.code} value={state.code} style={{ color: '#111' }}>{state.name} ({state.code})</option>
                      ))}
                    </select>
                    <button
                      onClick={async () => {
                        const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
                        try {
                          const response = await fetch(`${apiBase}/api/admin/athletes/${selectedAthlete.id}`, {
                            method: 'PATCH',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ state_code: currentValue }),
                          });
                          if (response.ok) {
                            setSuccess(`${field.label} updated!`);
                            setSelectedAthlete({ ...selectedAthlete, state_code: currentValue });
                          } else {
                            setError(`Failed to update ${field.label}`);
                          }
                        } catch (err) {
                          setError(`Failed to update ${field.label}`);
                        }
                      }}
                      style={{
                        padding: '0.2rem 0.4rem',
                        backgroundColor: '#cc0000',
                        color: 'white',
                        border: 'none',
                        borderRadius: '3px',
                        cursor: 'pointer',
                        fontSize: '0.65rem',
                        fontWeight: '600'
                      }}
                    >
                      Update
                    </button>
                  </div>
                );
              }

              // Club Name field - dropdown based on state
              if (field.key === 'club_name') {
                const currentClubCode = editForm.club_code;
                const originalClubCode = (selectedAthlete as any).club_code || '';
                const isChanged = currentClubCode !== originalClubCode;
                return (
                  <div key={field.key} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                    <label style={{ color: '#111', fontWeight: '500', minWidth: '80px', flexShrink: 0 }}>
                      {field.label}:
                    </label>
                    <select
                      value={currentClubCode}
                      onChange={(e) => {
                        const selectedClub = clubsForState.find(c => c.club_code === e.target.value);
                        setEditForm({
                          ...editForm,
                          club_code: e.target.value,
                          club_name: selectedClub?.club_name || ''
                        });
                      }}
                      style={{ padding: '0.2rem', border: '1px solid #ddd', borderRadius: '3px', fontSize: '0.7rem', flex: 1, color: isChanged ? '#111' : '#888' }}
                    >
                      <option value="" style={{ color: '#111' }}>Select Club</option>
                      {clubsForState.map(club => (
                        <option key={club.club_code} value={club.club_code} style={{ color: '#111' }}>
                          {club.club_name} ({club.club_code})
                        </option>
                      ))}
                    </select>
                    <button
                      onClick={async () => {
                        const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
                        try {
                          const response = await fetch(`${apiBase}/api/admin/athletes/${selectedAthlete.id}`, {
                            method: 'PATCH',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ club_code: editForm.club_code, club_name: editForm.club_name }),
                          });
                          if (response.ok) {
                            setSuccess(`${field.label} updated!`);
                            setSelectedAthlete({ ...selectedAthlete, club_code: editForm.club_code, club_name: editForm.club_name });
                          } else {
                            setError(`Failed to update ${field.label}`);
                          }
                        } catch (err) {
                          setError(`Failed to update ${field.label}`);
                        }
                      }}
                      style={{
                        padding: '0.2rem 0.4rem',
                        backgroundColor: '#cc0000',
                        color: 'white',
                        border: 'none',
                        borderRadius: '3px',
                        cursor: 'pointer',
                        fontSize: '0.65rem',
                        fontWeight: '600'
                      }}
                    >
                      Update
                    </button>
                  </div>
                );
              }

              // Nation field - dropdown with IOC codes
              if (field.key === 'NATION') {
                const isChanged = currentValue !== originalValue;
                return (
                  <div key={field.key} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                    <label style={{ color: '#111', fontWeight: '500', minWidth: '80px', flexShrink: 0 }}>
                      {field.label}:
                    </label>
                    <select
                      value={currentValue}
                      onChange={(e) => setEditForm({ ...editForm, [field.key]: e.target.value })}
                      style={{ padding: '0.2rem', border: '1px solid #ddd', borderRadius: '3px', fontSize: '0.7rem', color: isChanged ? '#111' : '#888' }}
                    >
                      <option value="" style={{ color: '#111' }}>Select Nation</option>
                      {IOC_COUNTRY_CODES.map(code => (
                        <option key={code} value={code} style={{ color: '#111' }}>{code}</option>
                      ))}
                    </select>
                    <button
                      onClick={async () => {
                        const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
                        try {
                          const response = await fetch(`${apiBase}/api/admin/athletes/${selectedAthlete.id}`, {
                            method: 'PATCH',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ nation: currentValue }),
                          });
                          if (response.ok) {
                            setSuccess(`${field.label} updated!`);
                            setSelectedAthlete({ ...selectedAthlete, nation: currentValue });
                          } else {
                            setError(`Failed to update ${field.label}`);
                          }
                        } catch (err) {
                          setError(`Failed to update ${field.label}`);
                        }
                      }}
                      style={{
                        padding: '0.2rem 0.4rem',
                        backgroundColor: '#cc0000',
                        color: 'white',
                        border: 'none',
                        borderRadius: '3px',
                        cursor: 'pointer',
                        fontSize: '0.65rem',
                        fontWeight: '600'
                      }}
                    >
                      Update
                    </button>
                  </div>
                );
              }

              // IC Number fields (IC, AcctIC) - 5 boxes: YY MM DD - PB - ####
              if (field.key === 'IC' || field.key === 'AcctIC') {
                // Parse IC: format YYMMDD-PB-#### or just digits
                const parseIC = (ic: string) => {
                  if (!ic) return { yy: '', mm: '', dd: '', pb: '', last: '', isPassport: false, raw: '' };

                  // Remove dashes and spaces
                  const cleaned = ic.replace(/[-\s]/g, '');

                  // Check if it looks like a passport (has letters or is 7-9 chars)
                  const hasLetter = /[a-zA-Z]/.test(cleaned);
                  const isPassportLength = cleaned.length >= 7 && cleaned.length <= 9;
                  if (hasLetter || (isPassportLength && cleaned.length < 12)) {
                    return { yy: '', mm: '', dd: '', pb: '', last: '', isPassport: true, raw: ic };
                  }

                  // Parse as IC: YYMMDDPB####
                  if (cleaned.length >= 6) {
                    const yy = cleaned.substring(0, 2);
                    const mm = cleaned.substring(2, 4);
                    const dd = cleaned.substring(4, 6);
                    const pb = cleaned.length >= 8 ? cleaned.substring(6, 8) : '';
                    const last = cleaned.length > 8 ? cleaned.substring(8) : '';
                    return { yy, mm, dd, pb, last, isPassport: false, raw: ic };
                  }

                  return { yy: '', mm: '', dd: '', pb: '', last: '', isPassport: false, raw: ic };
                };

                const parsed = parseIC(currentValue);
                const originalParsed = parseIC(originalValue);

                // Get days in month
                const getDaysInMonth = (mm: string) => {
                  if (!mm) return 31;
                  const month = parseInt(mm);
                  if ([1, 3, 5, 7, 8, 10, 12].includes(month)) return 31;
                  if ([4, 6, 9, 11].includes(month)) return 30;
                  if (month === 2) return 29; // Allow 29 for leap years
                  return 31;
                };

                const daysInMonth = getDaysInMonth(parsed.mm);

                // Build IC string from parts
                const buildIC = (yy: string, mm: string, dd: string, pb: string, last: string) => {
                  if (!yy && !mm && !dd && !pb && !last) return '';
                  return `${yy}${mm}${dd}-${pb}-${last}`;
                };

                // If it's a passport, show raw input
                if (parsed.isPassport) {
                  const isChanged = currentValue !== originalValue;
                  return (
                    <div key={field.key} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', gridColumn: 'span 2' }}>
                      <label style={{ color: '#111', fontWeight: '500', minWidth: '80px', flexShrink: 0 }}>
                        {field.label}:
                      </label>
                      <span style={{ fontSize: '0.65rem', color: '#cc0000', marginRight: '0.3rem' }}>(Passport?)</span>
                      <input
                        type="text"
                        value={currentValue}
                        placeholder={originalValue || 'Passport number detected'}
                        onChange={(e) => setEditForm({ ...editForm, [field.key]: e.target.value })}
                        style={{
                          flex: 1,
                          padding: '0.2rem 0.3rem',
                          border: '1px solid #ddd',
                          borderRadius: '3px',
                          fontSize: '0.7rem',
                          color: isChanged ? '#111' : '#888'
                        }}
                      />
                      <button
                        onClick={async () => {
                          const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
                          try {
                            const response = await fetch(`${apiBase}/api/admin/athletes/${selectedAthlete.id}`, {
                              method: 'PATCH',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({ [field.key]: currentValue }),
                            });
                            if (response.ok) {
                              setSuccess(`${field.label} updated!`);
                              setSelectedAthlete({ ...selectedAthlete, [field.key]: currentValue });
                            } else {
                              setError(`Failed to update ${field.label}`);
                            }
                          } catch (err) {
                            setError(`Failed to update ${field.label}`);
                          }
                        }}
                        style={{
                          padding: '0.2rem 0.4rem',
                          backgroundColor: '#cc0000',
                          color: 'white',
                          border: 'none',
                          borderRadius: '3px',
                          cursor: 'pointer',
                          fontSize: '0.65rem',
                          fontWeight: '600'
                        }}
                      >
                        Update
                      </button>
                    </div>
                  );
                }

                // IC format with 5 boxes
                const isYYChanged = parsed.yy !== originalParsed.yy;
                const isMMChanged = parsed.mm !== originalParsed.mm;
                const isDDChanged = parsed.dd !== originalParsed.dd;
                const isPBChanged = parsed.pb !== originalParsed.pb;
                const isLastChanged = parsed.last !== originalParsed.last;

                return (
                  <div key={field.key} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', gridColumn: 'span 2' }}>
                    <label style={{ color: '#111', fontWeight: '500', minWidth: '80px', flexShrink: 0 }}>
                      {field.label}:
                    </label>
                    {/* YY */}
                    <select
                      value={parsed.yy}
                      onChange={(e) => {
                        const newIC = buildIC(e.target.value, parsed.mm, parsed.dd, parsed.pb, parsed.last);
                        setEditForm({ ...editForm, [field.key]: newIC });
                      }}
                      style={{ padding: '0.2rem', border: '1px solid #ddd', borderRadius: '3px', fontSize: '0.7rem', width: '50px', color: isYYChanged ? '#111' : '#888' }}
                    >
                      <option value="" style={{ color: '#888' }}>YY</option>
                      {Array.from({ length: 100 }, (_, i) => String(i).padStart(2, '0')).map(y => (
                        <option key={y} value={y} style={{ color: '#111' }}>{y}</option>
                      ))}
                    </select>
                    {/* MM */}
                    <select
                      value={parsed.mm}
                      onChange={(e) => {
                        const newIC = buildIC(parsed.yy, e.target.value, parsed.dd, parsed.pb, parsed.last);
                        setEditForm({ ...editForm, [field.key]: newIC });
                      }}
                      style={{ padding: '0.2rem', border: '1px solid #ddd', borderRadius: '3px', fontSize: '0.7rem', width: '50px', color: isMMChanged ? '#111' : '#888' }}
                    >
                      <option value="" style={{ color: '#888' }}>MM</option>
                      {Array.from({ length: 12 }, (_, i) => String(i + 1).padStart(2, '0')).map(m => (
                        <option key={m} value={m} style={{ color: '#111' }}>{m}</option>
                      ))}
                    </select>
                    {/* DD */}
                    <select
                      value={parsed.dd}
                      onChange={(e) => {
                        const newIC = buildIC(parsed.yy, parsed.mm, e.target.value, parsed.pb, parsed.last);
                        setEditForm({ ...editForm, [field.key]: newIC });
                      }}
                      style={{ padding: '0.2rem', border: '1px solid #ddd', borderRadius: '3px', fontSize: '0.7rem', width: '50px', color: isDDChanged ? '#111' : '#888' }}
                    >
                      <option value="" style={{ color: '#888' }}>DD</option>
                      {Array.from({ length: daysInMonth }, (_, i) => String(i + 1).padStart(2, '0')).map(d => (
                        <option key={d} value={d} style={{ color: '#111' }}>{d}</option>
                      ))}
                    </select>
                    <span style={{ color: '#666' }}>-</span>
                    {/* PB (Place of Birth) */}
                    <select
                      value={parsed.pb}
                      onChange={(e) => {
                        const newIC = buildIC(parsed.yy, parsed.mm, parsed.dd, e.target.value, parsed.last);
                        setEditForm({ ...editForm, [field.key]: newIC });
                      }}
                      style={{ padding: '0.2rem', border: '1px solid #ddd', borderRadius: '3px', fontSize: '0.7rem', width: '50px', color: isPBChanged ? '#111' : '#888' }}
                    >
                      <option value="" style={{ color: '#888' }}>PB</option>
                      {Array.from({ length: 100 }, (_, i) => String(i).padStart(2, '0')).map(p => (
                        <option key={p} value={p} style={{ color: '#111' }}>{p}</option>
                      ))}
                    </select>
                    <span style={{ color: '#666' }}>-</span>
                    {/* Last 4+ digits */}
                    <input
                      type="text"
                      value={parsed.last}
                      placeholder={originalParsed.last || '####'}
                      onChange={(e) => {
                        const newIC = buildIC(parsed.yy, parsed.mm, parsed.dd, parsed.pb, e.target.value);
                        setEditForm({ ...editForm, [field.key]: newIC });
                      }}
                      style={{
                        width: '60px',
                        padding: '0.2rem 0.3rem',
                        border: '1px solid #ddd',
                        borderRadius: '3px',
                        fontSize: '0.7rem',
                        color: isLastChanged ? '#111' : '#888'
                      }}
                    />
                    <button
                      onClick={async () => {
                        const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
                        try {
                          const response = await fetch(`${apiBase}/api/admin/athletes/${selectedAthlete.id}`, {
                            method: 'PATCH',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ [field.key]: currentValue }),
                          });
                          if (response.ok) {
                            setSuccess(`${field.label} updated!`);
                            setSelectedAthlete({ ...selectedAthlete, [field.key]: currentValue });
                          } else {
                            setError(`Failed to update ${field.label}`);
                          }
                        } catch (err) {
                          setError(`Failed to update ${field.label}`);
                        }
                      }}
                      style={{
                        padding: '0.2rem 0.4rem',
                        backgroundColor: '#cc0000',
                        color: 'white',
                        border: 'none',
                        borderRadius: '3px',
                        cursor: 'pointer',
                        fontSize: '0.65rem',
                        fontWeight: '600'
                      }}
                    >
                      Update
                    </button>
                  </div>
                );
              }

              // Phone number fields - country code dropdown + digits input
              const phoneFields = ['Phone', 'EmergencyPhone', 'Guardian1HomePhone', 'Guardian1MobilePhone',
                                   'Guardian1WorkPhone', 'Guardian2HomePhone', 'Guardian2MobilePhone', 'Guardian2WorkPhone'];
              if (phoneFields.includes(field.key)) {
                // Common country codes
                const countryCodes = [
                  { code: '+60', country: 'MY' },
                  { code: '+65', country: 'SG' },
                  { code: '+1', country: 'US/CA' },
                  { code: '+44', country: 'UK' },
                  { code: '+61', country: 'AU' },
                  { code: '+86', country: 'CN' },
                  { code: '+82', country: 'KR' },
                  { code: '+81', country: 'JP' },
                  { code: '+91', country: 'IN' },
                  { code: '+62', country: 'ID' },
                  { code: '+63', country: 'PH' },
                  { code: '+66', country: 'TH' },
                  { code: '+84', country: 'VN' },
                  { code: '+852', country: 'HK' },
                  { code: '+886', country: 'TW' },
                  { code: '+971', country: 'AE' },
                  { code: '+33', country: 'FR' },
                  { code: '+49', country: 'DE' },
                  { code: '+31', country: 'NL' },
                  { code: '+39', country: 'IT' },
                  { code: '+34', country: 'ES' },
                  { code: '+7', country: 'RU' },
                  { code: '+20', country: 'EG' },
                  { code: '+27', country: 'ZA' },
                  { code: '+55', country: 'BR' },
                  { code: '+52', country: 'MX' },
                  { code: '+98', country: 'IR' },
                  { code: '+960', country: 'MV' },
                ];

                // Parse phone number to extract country code and digits
                const parsePhone = (phone: string) => {
                  if (!phone) return { countryCode: '+60', digits: '' };

                  const cleaned = phone.replace(/[\s\-\(\)]/g, '');

                  // Try to match country code
                  for (const cc of countryCodes.sort((a, b) => b.code.length - a.code.length)) {
                    if (cleaned.startsWith(cc.code)) {
                      return { countryCode: cc.code, digits: cleaned.slice(cc.code.length) };
                    }
                  }

                  // Check for 00 prefix (international format)
                  if (cleaned.startsWith('00')) {
                    const withoutPrefix = '+' + cleaned.slice(2);
                    for (const cc of countryCodes.sort((a, b) => b.code.length - a.code.length)) {
                      if (withoutPrefix.startsWith(cc.code)) {
                        return { countryCode: cc.code, digits: withoutPrefix.slice(cc.code.length) };
                      }
                    }
                  }

                  // If starts with 0, assume Malaysian local format
                  if (cleaned.startsWith('0')) {
                    return { countryCode: '+60', digits: cleaned.slice(1) };
                  }

                  // If no country code detected, assume Malaysian
                  return { countryCode: '+60', digits: cleaned };
                };

                const parsed = parsePhone(currentValue);
                const originalParsed = parsePhone(originalValue);

                const buildPhone = (countryCode: string, digits: string) => {
                  if (!digits) return '';
                  return `${countryCode}${digits}`;
                };

                // Format Malaysian phone numbers with spaces
                const formatMalaysianDigits = (digits: string) => {
                  const clean = digits.replace(/\s/g, '');
                  if (clean.length === 9) {
                    // XX XXX XXXX
                    return `${clean.slice(0, 2)} ${clean.slice(2, 5)} ${clean.slice(5)}`;
                  } else if (clean.length === 10) {
                    // XX XXXX XXXX
                    return `${clean.slice(0, 2)} ${clean.slice(2, 6)} ${clean.slice(6)}`;
                  }
                  return clean;
                };

                const displayDigits = parsed.countryCode === '+60'
                  ? formatMalaysianDigits(parsed.digits)
                  : parsed.digits;
                const originalDisplayDigits = originalParsed.countryCode === '+60'
                  ? formatMalaysianDigits(originalParsed.digits)
                  : originalParsed.digits;

                const isCodeChanged = parsed.countryCode !== originalParsed.countryCode;
                const isDigitsChanged = parsed.digits !== originalParsed.digits;

                return (
                  <div key={field.key} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                    <label style={{ color: '#111', fontWeight: '500', minWidth: '80px', flexShrink: 0, fontSize: '0.7rem' }}>
                      {field.label}:
                    </label>
                    {/* Country Code Dropdown */}
                    <select
                      value={parsed.countryCode}
                      onChange={(e) => {
                        const newPhone = buildPhone(e.target.value, parsed.digits);
                        setEditForm({ ...editForm, [field.key]: newPhone });
                      }}
                      style={{
                        padding: '0.2rem',
                        border: '1px solid #ddd',
                        borderRadius: '3px',
                        fontSize: '0.65rem',
                        width: '75px',
                        color: isCodeChanged ? '#111' : '#888'
                      }}
                    >
                      {countryCodes.map(cc => (
                        <option key={cc.code} value={cc.code} style={{ color: '#111' }}>
                          {cc.code} {cc.country}
                        </option>
                      ))}
                    </select>
                    {/* Phone Digits */}
                    <input
                      type="text"
                      value={displayDigits}
                      placeholder={originalDisplayDigits || 'Phone number'}
                      onChange={(e) => {
                        // Strip spaces and non-digits, then rebuild
                        const digitsOnly = e.target.value.replace(/\D/g, '');
                        const newPhone = buildPhone(parsed.countryCode, digitsOnly);
                        setEditForm({ ...editForm, [field.key]: newPhone });
                      }}
                      style={{
                        flex: 1,
                        padding: '0.2rem 0.3rem',
                        border: '1px solid #ddd',
                        borderRadius: '3px',
                        fontSize: '0.7rem',
                        minWidth: '80px',
                        color: isDigitsChanged ? '#111' : '#888'
                      }}
                    />
                    <button
                      onClick={async () => {
                        const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
                        try {
                          const response = await fetch(`${apiBase}/api/admin/athletes/${selectedAthlete.id}`, {
                            method: 'PATCH',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ [field.key]: currentValue }),
                          });
                          if (response.ok) {
                            setSuccess(`${field.label} updated!`);
                            setSelectedAthlete({ ...selectedAthlete, [field.key]: currentValue });
                          } else {
                            setError(`Failed to update ${field.label}`);
                          }
                        } catch (err) {
                          setError(`Failed to update ${field.label}`);
                        }
                      }}
                      style={{
                        padding: '0.2rem 0.4rem',
                        backgroundColor: '#cc0000',
                        color: 'white',
                        border: 'none',
                        borderRadius: '3px',
                        cursor: 'pointer',
                        fontSize: '0.65rem',
                        fontWeight: '600'
                      }}
                    >
                      Update
                    </button>
                  </div>
                );
              }

              // Address fields - structured input (skip individual rendering, handled as group)
              const addressFields = ['Address', 'Address2', 'City'];
              if (addressFields.includes(field.key)) {
                // Only render once for 'Address', skip Address2 and City (they're included in the group)
                if (field.key !== 'Address') return null;

                // Malaysian states
                const malaysianStates = [
                  { code: '', name: 'Select State' },
                  { code: 'JHR', name: 'Johor' },
                  { code: 'KDH', name: 'Kedah' },
                  { code: 'KTN', name: 'Kelantan' },
                  { code: 'MLK', name: 'Melaka' },
                  { code: 'NSN', name: 'Negeri Sembilan' },
                  { code: 'PHG', name: 'Pahang' },
                  { code: 'PRK', name: 'Perak' },
                  { code: 'PLS', name: 'Perlis' },
                  { code: 'PNG', name: 'Pulau Pinang' },
                  { code: 'SBH', name: 'Sabah' },
                  { code: 'SWK', name: 'Sarawak' },
                  { code: 'SGR', name: 'Selangor' },
                  { code: 'TRG', name: 'Terengganu' },
                  { code: 'KUL', name: 'Kuala Lumpur' },
                  { code: 'LBN', name: 'Labuan' },
                  { code: 'PJY', name: 'Putrajaya' },
                ];

                // Countries
                const countries = [
                  { code: 'MAS', name: 'Malaysia' },
                  { code: 'SGP', name: 'Singapore' },
                  { code: 'CHN', name: 'China' },
                  { code: 'KOR', name: 'South Korea' },
                  { code: 'JPN', name: 'Japan' },
                  { code: 'USA', name: 'United States' },
                  { code: 'AUS', name: 'Australia' },
                  { code: 'GBR', name: 'United Kingdom' },
                  { code: 'IND', name: 'India' },
                  { code: 'IDN', name: 'Indonesia' },
                  { code: 'PHL', name: 'Philippines' },
                  { code: 'THA', name: 'Thailand' },
                  { code: 'VNM', name: 'Vietnam' },
                  { code: 'HKG', name: 'Hong Kong' },
                  { code: 'TWN', name: 'Taiwan' },
                  { code: 'NLD', name: 'Netherlands' },
                  { code: 'DEU', name: 'Germany' },
                  { code: 'FRA', name: 'France' },
                  { code: 'CAN', name: 'Canada' },
                  { code: 'NZL', name: 'New Zealand' },
                ];

                const addressValue = editForm.Address || '';
                const address2Value = editForm.Address2 || '';
                const cityValue = editForm.City || '';
                const addressStateValue = editForm.address_state || '';
                const nationValue = editForm.NATION || 'MAS';

                const origAddress = (selectedAthlete as any).Address || '';
                const origAddress2 = (selectedAthlete as any).Address2 || '';
                const origCity = (selectedAthlete as any).City || '';
                const origAddressState = (selectedAthlete as any).address_state || '';
                const origNation = (selectedAthlete as any).nation || (selectedAthlete as any).NATION || 'MAS';

                return (
                  <div key="address-group" style={{ gridColumn: 'span 2', border: '1px solid #ddd', borderRadius: '4px', padding: '0.5rem', marginBottom: '0.5rem' }}>
                    <div style={{ fontWeight: '600', fontSize: '0.75rem', marginBottom: '0.5rem', color: '#333' }}>Address</div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.4rem' }}>
                      {/* Street Address */}
                      <div style={{ gridColumn: 'span 2', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                        <label style={{ color: '#111', fontWeight: '500', minWidth: '60px', fontSize: '0.65rem' }}>Street:</label>
                        <input
                          type="text"
                          value={addressValue}
                          placeholder={origAddress || 'Street address'}
                          onChange={(e) => setEditForm({ ...editForm, Address: e.target.value })}
                          style={{ flex: 1, padding: '0.2rem 0.3rem', border: '1px solid #ddd', borderRadius: '3px', fontSize: '0.7rem', color: addressValue !== origAddress ? '#111' : '#888' }}
                        />
                      </div>
                      {/* Address Line 2 */}
                      <div style={{ gridColumn: 'span 2', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                        <label style={{ color: '#111', fontWeight: '500', minWidth: '60px', fontSize: '0.65rem' }}>Line 2:</label>
                        <input
                          type="text"
                          value={address2Value}
                          placeholder={origAddress2 || 'Apartment, suite, etc.'}
                          onChange={(e) => setEditForm({ ...editForm, Address2: e.target.value })}
                          style={{ flex: 1, padding: '0.2rem 0.3rem', border: '1px solid #ddd', borderRadius: '3px', fontSize: '0.7rem', color: address2Value !== origAddress2 ? '#111' : '#888' }}
                        />
                      </div>
                      {/* City */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                        <label style={{ color: '#111', fontWeight: '500', minWidth: '60px', fontSize: '0.65rem' }}>City:</label>
                        <input
                          type="text"
                          value={cityValue}
                          placeholder={origCity || 'City/Town'}
                          onChange={(e) => setEditForm({ ...editForm, City: e.target.value })}
                          style={{ flex: 1, padding: '0.2rem 0.3rem', border: '1px solid #ddd', borderRadius: '3px', fontSize: '0.7rem', color: cityValue !== origCity ? '#111' : '#888' }}
                        />
                      </div>
                      {/* Postal Code */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                        <label style={{ color: '#111', fontWeight: '500', minWidth: '60px', fontSize: '0.65rem' }}>Postal:</label>
                        <input
                          type="text"
                          value={editForm.postal_code || ''}
                          placeholder={(selectedAthlete as any).postal_code || 'Postal code'}
                          onChange={(e) => setEditForm({ ...editForm, postal_code: e.target.value.replace(/[^0-9]/g, '').slice(0, 5) })}
                          style={{ width: '70px', padding: '0.2rem 0.3rem', border: '1px solid #ddd', borderRadius: '3px', fontSize: '0.7rem', color: editForm.postal_code !== ((selectedAthlete as any).postal_code || '') ? '#111' : '#888' }}
                          maxLength={5}
                        />
                      </div>
                      {/* Address State (separate from club state) */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                        <label style={{ color: '#111', fontWeight: '500', minWidth: '60px', fontSize: '0.65rem' }}>State:</label>
                        <select
                          value={addressStateValue}
                          onChange={(e) => setEditForm({ ...editForm, address_state: e.target.value })}
                          style={{ flex: 1, padding: '0.2rem', border: '1px solid #ddd', borderRadius: '3px', fontSize: '0.65rem', color: addressStateValue !== origAddressState ? '#111' : '#888' }}
                        >
                          {malaysianStates.map(s => (
                            <option key={s.code} value={s.code}>{s.code ? `${s.code} - ${s.name}` : s.name}</option>
                          ))}
                        </select>
                      </div>
                      {/* Country */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                        <label style={{ color: '#111', fontWeight: '500', minWidth: '60px', fontSize: '0.65rem' }}>Country:</label>
                        <select
                          value={nationValue}
                          onChange={(e) => setEditForm({ ...editForm, NATION: e.target.value })}
                          style={{ flex: 1, padding: '0.2rem', border: '1px solid #ddd', borderRadius: '3px', fontSize: '0.65rem', color: nationValue !== origNation ? '#111' : '#888' }}
                        >
                          {countries.map(c => (
                            <option key={c.code} value={c.code}>{c.name}</option>
                          ))}
                        </select>
                      </div>
                    </div>
                  </div>
                );
              }

              // Email fields - with validation
              const emailFields = ['MembEmail'];
              if (emailFields.includes(field.key)) {
                const isChanged = currentValue !== originalValue;
                const isValidEmail = (email: string) => {
                  if (!email) return true; // Empty is ok
                  return email.includes('@') && email.includes('.') && email.indexOf('@') < email.lastIndexOf('.');
                };
                const emailValid = isValidEmail(currentValue);

                return (
                  <div key={field.key} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                    <label style={{ color: '#111', fontWeight: '500', minWidth: '80px', flexShrink: 0 }}>
                      {field.label}:
                    </label>
                    <input
                      type="text"
                      value={currentValue}
                      placeholder={originalValue || `Enter ${field.label.toLowerCase()}`}
                      onChange={(e) => setEditForm({ ...editForm, [field.key]: e.target.value })}
                      style={{
                        flex: 1,
                        padding: '0.2rem 0.3rem',
                        border: `1px solid ${!emailValid ? '#cc0000' : '#ddd'}`,
                        borderRadius: '3px',
                        fontSize: '0.7rem',
                        minWidth: '100px',
                        color: isChanged ? '#111' : '#888',
                        backgroundColor: !emailValid ? '#fff0f0' : 'white'
                      }}
                    />
                    {!emailValid && (
                      <span style={{ color: '#cc0000', fontSize: '0.6rem', whiteSpace: 'nowrap' }}>Invalid</span>
                    )}
                    <button
                      disabled={!emailValid}
                      onClick={async () => {
                        if (!emailValid) {
                          setError('Please enter a valid email address');
                          return;
                        }
                        const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
                        try {
                          const response = await fetch(`${apiBase}/api/admin/athletes/${selectedAthlete.id}`, {
                            method: 'PATCH',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ [field.key]: currentValue }),
                          });
                          if (response.ok) {
                            setSuccess(`${field.label} updated!`);
                            setSelectedAthlete({ ...selectedAthlete, [field.key]: currentValue });
                          } else {
                            setError(`Failed to update ${field.label}`);
                          }
                        } catch (err) {
                          setError(`Failed to update ${field.label}`);
                        }
                      }}
                      style={{
                        padding: '0.2rem 0.4rem',
                        backgroundColor: emailValid ? '#cc0000' : '#ccc',
                        color: 'white',
                        border: 'none',
                        borderRadius: '3px',
                        cursor: emailValid ? 'pointer' : 'not-allowed',
                        fontSize: '0.65rem',
                        fontWeight: '600',
                        flexShrink: 0
                      }}
                    >
                      Update
                    </button>
                  </div>
                );
              }

              // All other fields - text input with current value as grey placeholder
              const isChanged = currentValue !== originalValue;
              return (
                <div key={field.key} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                  <label style={{ color: '#111', fontWeight: '500', minWidth: '80px', flexShrink: 0 }}>
                    {field.label}:
                  </label>
                  <input
                    type="text"
                    value={currentValue}
                    placeholder={originalValue || `Enter ${field.label.toLowerCase()}`}
                    onChange={(e) => setEditForm({ ...editForm, [field.key]: e.target.value })}
                    style={{
                      flex: 1,
                      padding: '0.2rem 0.3rem',
                      border: '1px solid #ddd',
                      borderRadius: '3px',
                      fontSize: '0.7rem',
                      minWidth: '100px',
                      color: isChanged ? '#111' : '#888'
                    }}
                  />
                  <button
                    onClick={async () => {
                      const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
                      try {
                        const response = await fetch(`${apiBase}/api/admin/athletes/${selectedAthlete.id}`, {
                          method: 'PATCH',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ [field.key]: currentValue }),
                        });
                        if (response.ok) {
                          setSuccess(`${field.label} updated!`);
                          setSelectedAthlete({ ...selectedAthlete, [field.key]: currentValue });
                        } else {
                          setError(`Failed to update ${field.label}`);
                        }
                      } catch (err) {
                        setError(`Failed to update ${field.label}`);
                      }
                    }}
                    style={{
                      padding: '0.2rem 0.4rem',
                      backgroundColor: '#cc0000',
                      color: 'white',
                      border: 'none',
                      borderRadius: '3px',
                      cursor: 'pointer',
                      fontSize: '0.65rem',
                      fontWeight: '600',
                      flexShrink: 0
                    }}
                  >
                    Update
                  </button>
                </div>
              );
            })}
          </div>

          {/* Update All Changes Button */}
          {(() => {
            // Calculate changed fields
            const changedFields: {key: string, value: any}[] = [];
            availableFields.forEach(field => {
              const currentValue = (editForm as any)[field.key] || '';
              const getOriginalValue = () => {
                if (field.key === 'BIRTHDATE') return (selectedAthlete as any).BIRTHDATE || (selectedAthlete as any).birth_date || '';
                if (field.key === 'Gender') return (selectedAthlete as any).Gender || (selectedAthlete as any).gender || '';
                if (field.key === 'NATION') return (selectedAthlete as any).nation || (selectedAthlete as any).NATION || '';
                if (field.key === 'club_name') return (selectedAthlete as any).club_name || '';
                if (field.key === 'state_code') return (selectedAthlete as any).state_code || '';
                return (selectedAthlete as any)[field.key] || '';
              };
              const originalValue = getOriginalValue();
              if (currentValue !== originalValue) {
                changedFields.push({ key: field.key, value: currentValue });
              }
            });

            const hasChanges = changedFields.length > 0;

            return (
              <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid #ddd', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <button
                  disabled={!hasChanges || isUpdating}
                  onClick={async () => {
                    if (!selectedAthlete || changedFields.length === 0) return;
                    setIsUpdating(true);
                    setError('');
                    try {
                      const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
                      const updatePayload: Record<string, any> = {};
                      changedFields.forEach(({ key, value }) => {
                        // Map field names for API
                        if (key === 'NATION') {
                          updatePayload['nation'] = value;
                        } else if (key === 'Gender') {
                          updatePayload['Gender'] = value;
                        } else {
                          updatePayload[key] = value;
                        }
                      });

                      const response = await fetch(`${apiBase}/api/admin/athletes/${selectedAthlete.id}`, {
                        method: 'PATCH',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(updatePayload),
                      });

                      if (response.ok) {
                        setSuccess(`Updated ${changedFields.length} field${changedFields.length > 1 ? 's' : ''} successfully!`);
                        // Update selectedAthlete with new values
                        const updatedAthlete = { ...selectedAthlete };
                        changedFields.forEach(({ key, value }) => {
                          (updatedAthlete as any)[key] = value;
                          if (key === 'NATION') (updatedAthlete as any).nation = value;
                          if (key === 'Gender') (updatedAthlete as any).gender = value;
                          if (key === 'BIRTHDATE') (updatedAthlete as any).birth_date = value;
                        });
                        setSelectedAthlete(updatedAthlete);
                      } else {
                        const errorText = await response.text();
                        setError(`Failed to update: ${errorText}`);
                      }
                    } catch (err: any) {
                      setError(`Failed to update: ${err.message}`);
                    } finally {
                      setIsUpdating(false);
                    }
                  }}
                  style={{
                    padding: '0.5rem 1.5rem',
                    backgroundColor: hasChanges ? '#cc0000' : '#9ca3af',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: hasChanges ? 'pointer' : 'not-allowed',
                    fontSize: '0.85rem',
                    fontWeight: '600'
                  }}
                >
                  {isUpdating ? 'Updating...' : `Update All Changes (${changedFields.length})`}
                </button>
                {hasChanges && (
                  <span style={{ fontSize: '0.75rem', color: '#666' }}>
                    {changedFields.length} field{changedFields.length > 1 ? 's' : ''} modified
                  </span>
                )}
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
};

export default AthleteManagement;
