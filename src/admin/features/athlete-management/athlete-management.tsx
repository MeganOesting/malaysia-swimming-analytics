import React, { useState } from 'react';
import { Athlete } from '../../shared/types/admin';
import { Button, AlertBox } from '../../shared/components';

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
  const [editForm, setEditForm] = useState<{
    name: string;
    gender: string;
    birth_date: string;
    club_name: string;
    state_code: string;
    nation: string;
    athlete_alias_1: string;
    athlete_alias_2: string;
  }>({
    name: '',
    gender: '',
    birth_date: '',
    club_name: '',
    state_code: '',
    nation: '',
    athlete_alias_1: '',
    athlete_alias_2: '',
  });

  const availableFields = [
    { key: 'name', label: 'Name' },
    { key: 'gender', label: 'Gender' },
    { key: 'birth_date', label: 'Birthdate' },
    { key: 'club_name', label: 'Club Name' },
    { key: 'state_code', label: 'State Code' },
    { key: 'nation', label: 'Nation' },
    { key: 'athlete_alias_1', label: 'Alias 1' },
    { key: 'athlete_alias_2', label: 'Alias 2' },
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

  const handleSelectAthlete = (athlete: Athlete) => {
    setSelectedAthlete(athlete);
    setFieldsToEdit(new Set());
    setIsEditingMode(false);
    setEditForm({
      name: athlete.name || '',
      gender: athlete.gender || '',
      birth_date: athlete.birth_date || '',
      club_name: athlete.club_name || '',
      state_code: athlete.state_code || '',
      nation: athlete.nation || '',
      athlete_alias_1: (athlete as any).athlete_alias_1 || '',
      athlete_alias_2: (athlete as any).athlete_alias_2 || '',
    });
    setError('');
    setSuccess('');
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
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
      const response = await fetch(`${apiBase}/api/admin/athletes/${selectedAthlete.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(editForm),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to update athlete: ${response.status} ${errorText}`);
      }

      setSuccess(`Athlete "${editForm.name}" updated successfully!`);
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
      {error && <AlertBox type="error" message={error} onClose={() => setError('')} />}
      {success && <AlertBox type="success" message={success} onClose={() => setSuccess('')} />}

      {/* Export Athletes Section */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.75rem', color: '#111' }}>
          Export Athletes
        </h3>
        <Button onClick={handleExportAthletes} variant="primary">
          Download Excel
        </Button>
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
                  padding: '0.75rem',
                  borderBottom: '1px solid #eee',
                  backgroundColor: '#ffffff',
                  cursor: 'pointer',
                  transition: 'background-color 0.2s',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem'
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
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '1rem',
                  fontSize: '0.75rem',
                  flex: 1
                }}>
                  <div style={{ fontWeight: '600', fontSize: '0.875rem', color: '#111', minWidth: '150px' }}>
                    {athlete.name}
                  </div>
                  <div style={{
                    fontFamily: 'monospace',
                    color: '#cc0000',
                    fontWeight: '600',
                    fontSize: '0.75rem'
                  }}>
                    ID: {athlete.id}
                  </div>
                  <div style={{ fontWeight: '500', color: '#333' }}>
                    DOB: {athlete.birth_date || '-'}
                  </div>
                  <div style={{ fontWeight: '500', color: '#333' }}>
                    {athlete.gender || '-'}
                  </div>
                  <div style={{ fontWeight: '500', color: '#333' }}>
                    {athlete.club_name || '-'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {athleteSearchQuery.length > 0 && !searchingAthletes && athleteSearchResults.length === 0 && (
          <AlertBox
            type="info"
            message={`No athletes found matching "${athleteSearchQuery}"`}
            onClose={() => {}}
          />
        )}
      </div>

      {/* Edit Selected Athlete Section */}
      {selectedAthlete && !isEditingMode && (
        <div style={{ marginTop: '2rem', paddingTop: '1.5rem', borderTop: '2px solid #ddd' }}>
          <h3 style={{ fontSize: '0.875rem', fontWeight: '600', marginBottom: '1rem', color: '#111' }}>
            Select Fields to Edit: {selectedAthlete.name}
          </h3>

          <div style={{ marginBottom: '1.5rem' }}>
            <p style={{ fontSize: '0.75rem', color: '#666', marginBottom: '0.75rem' }}>
              Check the fields you want to edit, then click "Continue to Editing"
            </p>
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '0.75rem',
              padding: '1rem',
              backgroundColor: '#f9fafb',
              borderRadius: '4px',
              border: '1px solid #ddd'
            }}>
              {availableFields.map(field => (
                <label key={field.key} style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  cursor: 'pointer',
                  fontSize: '0.875rem'
                }}>
                  <input
                    type="checkbox"
                    checked={fieldsToEdit.has(field.key)}
                    onChange={() => toggleFieldSelection(field.key)}
                    style={{ cursor: 'pointer' }}
                  />
                  {field.label}
                </label>
              ))}
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={handleStartEditing}
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
              Continue to Editing
            </button>
            <button
              onClick={() => setSelectedAthlete(null)}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#9ca3af',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.875rem',
                fontWeight: '600'
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Edit Form Section */}
      {selectedAthlete && isEditingMode && (
        <div style={{ marginTop: '2rem', paddingTop: '1.5rem', borderTop: '2px solid #ddd' }}>
          <h3 style={{ fontSize: '0.875rem', fontWeight: '600', marginBottom: '1rem', color: '#111' }}>
            Edit Athlete: {selectedAthlete.name}
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            {fieldsToEdit.has('name') && (
              <div>
                <label style={{ fontSize: '0.75rem', fontWeight: '500', color: '#666', display: 'block', marginBottom: '0.3rem' }}>
                  Name
                </label>
                <input
                  type="text"
                  value={editForm.name}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
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
            )}
            {fieldsToEdit.has('gender') && (
              <div>
                <label style={{ fontSize: '0.75rem', fontWeight: '500', color: '#666', display: 'block', marginBottom: '0.3rem' }}>
                  Gender
                </label>
                <select
                  value={editForm.gender}
                  onChange={(e) => setEditForm({ ...editForm, gender: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    fontSize: '0.875rem',
                    boxSizing: 'border-box'
                  }}
                >
                  <option value="">Select Gender</option>
                  <option value="M">Male</option>
                  <option value="F">Female</option>
                </select>
              </div>
            )}
            {fieldsToEdit.has('birth_date') && (
              <div>
                <label style={{ fontSize: '0.75rem', fontWeight: '500', color: '#666', display: 'block', marginBottom: '0.3rem' }}>
                  Birthdate
                </label>
                <input
                  type="text"
                  placeholder="YYYY-MM-DD"
                  value={editForm.birth_date}
                  onChange={(e) => setEditForm({ ...editForm, birth_date: e.target.value })}
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
            )}
            {fieldsToEdit.has('club_name') && (
              <div>
                <label style={{ fontSize: '0.75rem', fontWeight: '500', color: '#666', display: 'block', marginBottom: '0.3rem' }}>
                  Club Name
                </label>
                <input
                  type="text"
                  value={editForm.club_name}
                  onChange={(e) => setEditForm({ ...editForm, club_name: e.target.value })}
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
            )}
            {fieldsToEdit.has('state_code') && (
              <div>
                <label style={{ fontSize: '0.75rem', fontWeight: '500', color: '#666', display: 'block', marginBottom: '0.3rem' }}>
                  State Code
                </label>
                <input
                  type="text"
                  value={editForm.state_code}
                  onChange={(e) => setEditForm({ ...editForm, state_code: e.target.value })}
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
            )}
            {fieldsToEdit.has('nation') && (
              <div>
                <label style={{ fontSize: '0.75rem', fontWeight: '500', color: '#666', display: 'block', marginBottom: '0.3rem' }}>
                  Nation
                </label>
                <input
                  type="text"
                  value={editForm.nation}
                  onChange={(e) => setEditForm({ ...editForm, nation: e.target.value })}
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
            )}
            {fieldsToEdit.has('athlete_alias_1') && (
              <div>
                <label style={{ fontSize: '0.75rem', fontWeight: '500', color: '#666', display: 'block', marginBottom: '0.3rem' }}>
                  Alias 1
                </label>
                <input
                  type="text"
                  value={editForm.athlete_alias_1}
                  onChange={(e) => setEditForm({ ...editForm, athlete_alias_1: e.target.value })}
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
            )}
            {fieldsToEdit.has('athlete_alias_2') && (
              <div>
                <label style={{ fontSize: '0.75rem', fontWeight: '500', color: '#666', display: 'block', marginBottom: '0.3rem' }}>
                  Alias 2
                </label>
                <input
                  type="text"
                  value={editForm.athlete_alias_2}
                  onChange={(e) => setEditForm({ ...editForm, athlete_alias_2: e.target.value })}
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
            )}
          </div>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={handleUpdateAthlete}
              disabled={isUpdating}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: isUpdating ? '#9ca3af' : '#cc0000',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: isUpdating ? 'not-allowed' : 'pointer',
                fontSize: '0.875rem',
                fontWeight: '600'
              }}
            >
              {isUpdating ? 'Updating...' : 'Update Athlete'}
            </button>
            <button
              onClick={() => setIsEditingMode(false)}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#9ca3af',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.875rem',
                fontWeight: '600'
              }}
            >
              Back to Fields
            </button>
            <button
              onClick={() => setSelectedAthlete(null)}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#9ca3af',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.875rem',
                fontWeight: '600'
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AthleteManagement;
