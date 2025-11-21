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
    ClubCode: string;
    ClubName: string;
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
    ClubCode: '',
    ClubName: '',
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
    // Club & Nation
    { key: 'ClubCode', label: 'Club Code' },
    { key: 'ClubName', label: 'Club Name' },
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
      FULLNAME: (athlete as any).FULLNAME || '',
      FIRSTNAME: (athlete as any).FIRSTNAME || '',
      LASTNAME: (athlete as any).LASTNAME || '',
      MIDDLEINITIAL: (athlete as any).MIDDLEINITIAL || '',
      SUFFIX: (athlete as any).SUFFIX || '',
      IC: (athlete as any).IC || '',
      NATION: athlete.nation || '',
      MembEmail: (athlete as any).MembEmail || '',
      PreferredName: (athlete as any).PreferredName || '',
      Phone: (athlete as any).Phone || '',
      AcctFirstName: (athlete as any).AcctFirstName || '',
      AcctLastName: (athlete as any).AcctLastName || '',
      AcctMiddleInitial: (athlete as any).AcctMiddleInitial || '',
      Address: (athlete as any).Address || '',
      Address2: (athlete as any).Address2 || '',
      City: (athlete as any).City || '',
      EmergencyContact: (athlete as any).EmergencyContact || '',
      EmergencyPhone: (athlete as any).EmergencyPhone || '',
      Guardian1FirstName: (athlete as any).Guardian1FirstName || '',
      Guardian1HomePhone: (athlete as any).Guardian1HomePhone || '',
      Guardian1LastName: (athlete as any).Guardian1LastName || '',
      Guardian1MobilePhone: (athlete as any).Guardian1MobilePhone || '',
      Guardian1WorkPhone: (athlete as any).Guardian1WorkPhone || '',
      Guardian2FirstName: (athlete as any).Guardian2FirstName || '',
      Guardian2HomePhone: (athlete as any).Guardian2HomePhone || '',
      Guardian2LastName: (athlete as any).Guardian2LastName || '',
      Guardian2MobilePhone: (athlete as any).Guardian2MobilePhone || '',
      Guardian2WorkPhone: (athlete as any).Guardian2WorkPhone || '',
      AcctIC: (athlete as any).AcctIC || '',
      Gender: athlete.gender || '',
      ClubCode: (athlete as any).ClubCode || '',
      ClubName: athlete.club_name || '',
      athlete_alias_1: (athlete as any).athlete_alias_1 || '',
      athlete_alias_2: (athlete as any).athlete_alias_2 || '',
      passport_number: (athlete as any).passport_number || '',
      shoe_size: (athlete as any).shoe_size || '',
      tshirt_size: (athlete as any).tshirt_size || '',
      tracksuit_size: (athlete as any).tracksuit_size || '',
      cap_name: (athlete as any).cap_name || '',
      School_University_Name: (athlete as any).School_University_Name || '',
      School_University_Address: (athlete as any).School_University_Address || '',
      passport_expiry_date: (athlete as any).passport_expiry_date || '',
      BIRTHDATE: athlete.birth_date || '',
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
      // Only send the fields that were selected for editing
      const updateData: Record<string, any> = {};
      fieldsToEdit.forEach(fieldKey => {
        updateData[fieldKey] = (editForm as any)[fieldKey];
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
      <div style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: '#111', margin: 0 }}>
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
                    DOB: {formatDateDDMMMYYYY(athlete.birth_date)}
                  </div>
                  <div style={{ fontWeight: '500', color: '#333' }}>
                    {athlete.gender || '-'}
                  </div>
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
            {availableFields.map(field => {
              if (!fieldsToEdit.has(field.key)) return null;

              // Gender field - dropdown
              if (field.key === 'Gender') {
                return (
                  <div key={field.key}>
                    <label style={{ fontSize: '0.75rem', fontWeight: '500', color: '#666', display: 'block', marginBottom: '0.3rem' }}>
                      {field.label}
                    </label>
                    <select
                      value={(editForm as any)[field.key] || ''}
                      onChange={(e) => setEditForm({ ...editForm, [field.key]: e.target.value })}
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
                );
              }

              // All other fields - text input
              return (
                <div key={field.key}>
                  <label style={{ fontSize: '0.75rem', fontWeight: '500', color: '#666', display: 'block', marginBottom: '0.3rem' }}>
                    {field.label}
                  </label>
                  <input
                    type={field.key.includes('date') || field.key.includes('Date') ? 'text' : 'text'}
                    placeholder={field.key.includes('date') || field.key.includes('Date') ? 'YYYY-MM-DD' : ''}
                    value={(editForm as any)[field.key] || ''}
                    onChange={(e) => setEditForm({ ...editForm, [field.key]: e.target.value })}
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
              );
            })}
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
