/**
 * Coach Management Feature Component
 * Matches athlete-management layout and functionality
 */

import React, { useState } from 'react';
import { AlertBox } from '../../shared/components';
import { useNotification } from '../../shared/hooks';

// Helper function to format dates as dd MMM yyyy (e.g., 15 Mar 1998)
const formatDateDDMMMYYYY = (dateString: string | null | undefined): string => {
  if (!dateString) return '-';
  try {
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
  'AFG', 'ALB', 'ALG', 'AND', 'ANG', 'ARG', 'ARM', 'AUS', 'AUT', 'AZE',
  'BAH', 'BAN', 'BAR', 'BEL', 'BEN', 'BER', 'BHU', 'BIH', 'BLR', 'BOL', 'BRA',
  'BRN', 'BRU', 'BUL', 'CAM', 'CAN', 'CHI', 'CHN', 'COL', 'CRC', 'CRO', 'CUB',
  'CYP', 'CZE', 'DEN', 'ECU', 'EGY', 'ESP', 'EST', 'ETH', 'FIJ', 'FIN', 'FRA',
  'GBR', 'GER', 'GHA', 'GRE', 'GUA', 'HKG', 'HUN', 'INA', 'IND', 'IRI', 'IRL',
  'IRQ', 'ISL', 'ISR', 'ITA', 'JAM', 'JOR', 'JPN', 'KAZ', 'KEN', 'KGZ', 'KOR',
  'KSA', 'KUW', 'LAO', 'LAT', 'LBN', 'LTU', 'LUX', 'MAR', 'MDA', 'MEX', 'MGL',
  'MKD', 'MLT', 'MNE', 'MON', 'MYA', 'NAM', 'NED', 'NEP', 'NGR', 'NOR', 'NZL',
  'OMA', 'PAK', 'PAN', 'PAR', 'PER', 'PHI', 'POL', 'POR', 'PRK', 'PUR', 'QAT',
  'ROU', 'RSA', 'RUS', 'SGP', 'SLO', 'SRB', 'SRI', 'SUD', 'SUI', 'SVK', 'SWE',
  'SYR', 'THA', 'TJK', 'TKM', 'TPE', 'TTO', 'TUN', 'TUR', 'UAE', 'UGA', 'UKR',
  'URU', 'USA', 'UZB', 'VEN', 'VIE', 'YEM', 'ZAM', 'ZIM',
];

interface Coach {
  id: number;
  coach_name: string;
  birthdate?: string;
  gender?: string;
  nation?: string;
  club_name?: string;
  coach_role?: string;
  state_coach?: number;
  state_code?: string;
  msn_program?: string;
  coach_passport_number?: string;
  coach_email?: string;
  coach_phone?: string;
}

export interface CoachManagementProps {
  isAuthenticated: boolean;
}

export const CoachManagement: React.FC<CoachManagementProps> = ({
  isAuthenticated,
}) => {
  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Coach[]>([]);
  const [searching, setSearching] = useState(false);

  // Selected coach state
  const [selectedCoach, setSelectedCoach] = useState<Coach | null>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);

  // Edit form state
  const [editForm, setEditForm] = useState<{
    coach_name: string;
    birthdate: string;
    gender: string;
    nation: string;
    club_name: string;
    coach_role: string;
    state_coach: boolean;
    state_code: string;
    msn_program: string;
    coach_passport_number: string;
    coach_email: string;
    coach_phone: string;
  }>({
    coach_name: '',
    birthdate: '',
    gender: '',
    nation: '',
    club_name: '',
    coach_role: '',
    state_coach: false,
    state_code: '',
    msn_program: '',
    coach_passport_number: '',
    coach_email: '',
    coach_phone: '',
  });

  // Notifications
  const { notifications, success, error, clear } = useNotification();
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

  // Available fields for editing
  const availableFields = [
    { key: 'coach_name', label: 'Name' },
    { key: 'birthdate', label: 'Birthdate' },
    { key: 'gender', label: 'Gender' },
    { key: 'nation', label: 'Nation' },
    { key: 'club_name', label: 'Club' },
    { key: 'coach_role', label: 'Role' },
    { key: 'state_coach', label: 'State Coach' },
    { key: 'state_code', label: 'State Code' },
    { key: 'msn_program', label: 'MSN Program' },
    { key: 'coach_passport_number', label: 'Passport Number' },
    { key: 'coach_email', label: 'Email' },
    { key: 'coach_phone', label: 'Phone' },
  ];

  /**
   * Search coaches as user types
   */
  const searchCoaches = async (query: string) => {
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }

    setSearching(true);
    try {
      const response = await fetch(`${apiBase}/api/admin/coaches/search?q=${encodeURIComponent(query)}`);
      if (!response.ok) throw new Error('Search failed');
      const data = await response.json();
      setSearchResults(data.coaches || []);
    } catch (err: any) {
      setErrorMsg(`Failed to search coaches: ${err.message}`);
      console.error('Search error:', err);
    } finally {
      setSearching(false);
    }
  };

  /**
   * Select a coach and load full details
   */
  const handleSelectCoach = async (coach: Coach) => {
    setSelectedCoach(coach);
    setLoadingDetails(true);
    setErrorMsg('');
    setSuccessMsg('');

    try {
      const response = await fetch(`${apiBase}/api/admin/coaches/${coach.id}`);
      if (!response.ok) throw new Error('Failed to fetch coach details');
      const data = await response.json();
      const fullCoach = data.coach;

      setSelectedCoach({ ...coach, ...fullCoach });

      // Populate edit form
      setEditForm({
        coach_name: fullCoach.coach_name || '',
        birthdate: fullCoach.birthdate || '',
        gender: fullCoach.gender || '',
        nation: fullCoach.nation || '',
        club_name: fullCoach.club_name || '',
        coach_role: fullCoach.coach_role || '',
        state_coach: fullCoach.state_coach === 1 || fullCoach.state_coach === true,
        state_code: fullCoach.state_code || '',
        msn_program: fullCoach.msn_program || '',
        coach_passport_number: fullCoach.coach_passport_number || '',
        coach_email: fullCoach.coach_email || '',
        coach_phone: fullCoach.coach_phone || '',
      });
    } catch (err: any) {
      setErrorMsg(`Failed to load coach details: ${err.message}`);
    } finally {
      setLoadingDetails(false);
    }
  };

  /**
   * Export coaches to Excel
   */
  const handleExportCoaches = async () => {
    try {
      const response = await fetch(`${apiBase}/api/admin/coaches/export-excel`);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to export coaches: ${response.status} ${errorText}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'coaches_export.xlsx';
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setErrorMsg(err.message);
      console.error('Export error:', err);
    }
  };

  /**
   * Update coach
   */
  const handleUpdateCoach = async () => {
    if (!selectedCoach) return;

    try {
      const response = await fetch(`${apiBase}/api/admin/coaches/${selectedCoach.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...editForm,
          state_coach: editForm.state_coach ? 1 : 0,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to update coach: ${errorText}`);
      }

      setSuccessMsg('Coach updated successfully');
      // Refresh the coach details
      handleSelectCoach(selectedCoach);
    } catch (err: any) {
      setErrorMsg(err.message);
    }
  };

  /**
   * Copy coach ID to clipboard
   */
  const handleCopyId = (id: number) => {
    navigator.clipboard.writeText(String(id));
    const feedback = document.createElement('div');
    feedback.textContent = 'Coach ID copied!';
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

  return (
    <div>
      {/* Notifications */}
      {notifications.map(notification => (
        <AlertBox
          key={notification.id}
          type={notification.type}
          message={notification.message}
          onClose={() => clear(notification.id)}
        />
      ))}

      {successMsg && (
        <div style={{ padding: '0.75rem', marginBottom: '1rem', backgroundColor: '#ecfdf5', color: '#065f46', fontSize: '0.875rem', borderRadius: '4px' }}>
          {successMsg}
        </div>
      )}

      {errorMsg && (
        <div style={{ padding: '0.75rem', marginBottom: '1rem', backgroundColor: '#fef2f2', color: '#991b1b', fontSize: '0.875rem', borderRadius: '4px' }}>
          {errorMsg}
        </div>
      )}

      {/* Export Coaches Section */}
      <div style={{ marginTop: '1.5rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <button
          onClick={handleExportCoaches}
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
          Export Coaches Table
        </button>
      </div>

      {/* Search Coaches Section */}
      <div>
        <h3 style={{ fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.5rem', color: '#111' }}>
          Search Coaches by Name
        </h3>
        <p style={{ fontSize: '0.75rem', color: '#666', marginBottom: '0.75rem' }}>
          Enter partial name to find coaches
        </p>
        <div style={{ marginBottom: '0.75rem' }}>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              searchCoaches(e.target.value);
              // Clear selected coach when user starts typing to show search results
              if (selectedCoach) {
                setSelectedCoach(null);
              }
            }}
            placeholder="e.g., MAGNUS or CLARA..."
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

        {searching && <p style={{ color: '#666' }}>Searching...</p>}

        {searchResults.length > 0 && !selectedCoach && (
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
              {searchResults.length} result{searchResults.length !== 1 ? 's' : ''}
            </div>
            {searchResults.map(coach => (
              <div
                key={coach.id}
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
                onClick={() => handleSelectCoach(coach)}
              >
                <input
                  type="radio"
                  name="coach-selection"
                  checked={false}
                  onChange={() => handleSelectCoach(coach)}
                  style={{ cursor: 'pointer', flexShrink: 0 }}
                />
                <div style={{ fontWeight: '600', fontSize: '0.8rem', color: '#111', width: '220px', flexShrink: 0 }}>
                  {coach.coach_name}
                </div>
                <div style={{
                  fontFamily: 'monospace',
                  color: '#cc0000',
                  fontWeight: '600',
                  fontSize: '0.65rem',
                  width: '70px',
                  flexShrink: 0
                }}>
                  ID: {coach.id}
                </div>
                <div style={{ color: '#000', fontSize: '0.7rem', width: '90px', flexShrink: 0 }}>
                  {formatDateDDMMMYYYY(coach.birthdate) || '-'}
                </div>
                <div style={{ color: '#000', fontSize: '0.7rem', width: '20px', flexShrink: 0 }}>
                  {coach.gender || '-'}
                </div>
                <div style={{ color: '#666', fontSize: '0.7rem', flexShrink: 0 }}>
                  {coach.coach_role || '-'}
                </div>
              </div>
            ))}
          </div>
        )}

        {searchQuery.length > 0 && !searching && searchResults.length === 0 && (
          <div style={{ padding: '0.75rem', backgroundColor: '#eff6ff', color: '#1e40af', fontSize: '0.875rem', borderRadius: '4px' }}>
            No coaches found matching "{searchQuery}"
          </div>
        )}
      </div>

      {/* Edit Selected Coach Section */}
      {selectedCoach && (
        <div style={{ marginTop: '1.5rem', paddingTop: '1rem', borderTop: '2px solid #ddd' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: '#111', margin: 0 }}>
              Edit: {selectedCoach.coach_name}
              {loadingDetails && <span style={{ marginLeft: '0.5rem', color: '#666', fontWeight: 'normal', fontSize: '0.75rem' }}>(Loading details...)</span>}
            </h3>
            <button
              onClick={() => setSelectedCoach(null)}
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
              const currentValue = (editForm as any)[field.key];

              // Gender dropdown
              if (field.key === 'gender') {
                return (
                  <div key={field.key} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.25rem 0' }}>
                    <label style={{ width: '140px', fontWeight: '500', color: '#111', flexShrink: 0 }}>{field.label}:</label>
                    <select
                      value={currentValue || ''}
                      onChange={(e) => setEditForm({ ...editForm, gender: e.target.value })}
                      style={{
                        flex: 1,
                        padding: '0.3rem',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        color: currentValue ? '#111' : '#888'
                      }}
                    >
                      <option value="">-</option>
                      <option value="M">M</option>
                      <option value="F">F</option>
                    </select>
                  </div>
                );
              }

              // Nation dropdown
              if (field.key === 'nation') {
                return (
                  <div key={field.key} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.25rem 0' }}>
                    <label style={{ width: '140px', fontWeight: '500', color: '#111', flexShrink: 0 }}>{field.label}:</label>
                    <select
                      value={currentValue || ''}
                      onChange={(e) => setEditForm({ ...editForm, nation: e.target.value })}
                      style={{
                        flex: 1,
                        padding: '0.3rem',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        color: currentValue ? '#111' : '#888'
                      }}
                    >
                      <option value="">-</option>
                      {IOC_COUNTRY_CODES.map(code => (
                        <option key={code} value={code}>{code}</option>
                      ))}
                    </select>
                  </div>
                );
              }

              // State code dropdown
              if (field.key === 'state_code') {
                return (
                  <div key={field.key} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.25rem 0' }}>
                    <label style={{ width: '140px', fontWeight: '500', color: '#111', flexShrink: 0 }}>{field.label}:</label>
                    <select
                      value={currentValue || ''}
                      onChange={(e) => setEditForm({ ...editForm, state_code: e.target.value })}
                      style={{
                        flex: 1,
                        padding: '0.3rem',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        color: currentValue ? '#111' : '#888'
                      }}
                    >
                      <option value="">-</option>
                      {MALAYSIAN_STATES.map(state => (
                        <option key={state.code} value={state.code}>{state.code} - {state.name}</option>
                      ))}
                    </select>
                  </div>
                );
              }

              // Coach role dropdown
              if (field.key === 'coach_role') {
                return (
                  <div key={field.key} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.25rem 0' }}>
                    <label style={{ width: '140px', fontWeight: '500', color: '#111', flexShrink: 0 }}>{field.label}:</label>
                    <select
                      value={currentValue || ''}
                      onChange={(e) => setEditForm({ ...editForm, coach_role: e.target.value })}
                      style={{
                        flex: 1,
                        padding: '0.3rem',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        color: currentValue ? '#111' : '#888'
                      }}
                    >
                      <option value="">-</option>
                      <option value="Head Coach">Head Coach</option>
                      <option value="State Coach">State Coach</option>
                      <option value="Assistant Coach">Assistant Coach</option>
                      <option value="Club Coach">Club Coach</option>
                    </select>
                  </div>
                );
              }

              // State coach checkbox
              if (field.key === 'state_coach') {
                return (
                  <div key={field.key} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.25rem 0' }}>
                    <label style={{ width: '140px', fontWeight: '500', color: '#111', flexShrink: 0 }}>{field.label}:</label>
                    <input
                      type="checkbox"
                      checked={editForm.state_coach}
                      onChange={(e) => setEditForm({ ...editForm, state_coach: e.target.checked })}
                      style={{ cursor: 'pointer' }}
                    />
                  </div>
                );
              }

              // Birthdate field - date input
              if (field.key === 'birthdate') {
                const dateValue = currentValue ? currentValue.split('T')[0] : '';
                return (
                  <div key={field.key} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.25rem 0' }}>
                    <label style={{ width: '140px', fontWeight: '500', color: '#111', flexShrink: 0 }}>{field.label}:</label>
                    <input
                      type="date"
                      value={dateValue}
                      onChange={(e) => setEditForm({ ...editForm, birthdate: e.target.value ? `${e.target.value}T00:00:00Z` : '' })}
                      style={{
                        flex: 1,
                        padding: '0.3rem',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        color: currentValue ? '#111' : '#888'
                      }}
                    />
                  </div>
                );
              }

              // Default text input
              return (
                <div key={field.key} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.25rem 0' }}>
                  <label style={{ width: '140px', fontWeight: '500', color: '#111', flexShrink: 0 }}>{field.label}:</label>
                  <input
                    type="text"
                    value={currentValue || ''}
                    onChange={(e) => setEditForm({ ...editForm, [field.key]: e.target.value })}
                    style={{
                      flex: 1,
                      padding: '0.3rem',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      fontSize: '0.75rem',
                      color: currentValue ? '#111' : '#888'
                    }}
                  />
                </div>
              );
            })}
          </div>

          {/* Update button */}
          <div style={{ marginTop: '1rem' }}>
            <button
              onClick={handleUpdateCoach}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#cc0000',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.875rem',
                fontWeight: '600'
              }}
            >
              Update All Changes
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default CoachManagement;
