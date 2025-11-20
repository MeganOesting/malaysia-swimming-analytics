import React, { useState } from 'react';
import { Athlete } from '../../shared/types/admin';

interface AthleteManagementProps {
  isAuthenticated: boolean;
}

export const AthleteManagement: React.FC<AthleteManagementProps> = ({ isAuthenticated }) => {
  const [athleteSearchQuery, setAthleteSearchQuery] = useState('');
  const [athleteSearchResults, setAthleteSearchResults] = useState<Athlete[]>([]);
  const [searchingAthletes, setSearchingAthletes] = useState(false);
  const [error, setError] = useState('');

  const searchAthletes = async (query: string) => {
    if (query.length < 2) {
      setAthleteSearchResults([]);
      return;
    }

    setSearchingAthletes(true);
    try {
      const response = await fetch(`http://localhost:8000/api/admin/athletes/search?q=${encodeURIComponent(query)}`);
      const data = await response.json();
      setAthleteSearchResults(data.athletes || []);
    } catch (err: any) {
      setError(`Failed to search athletes: ${err.message}`);
    } finally {
      setSearchingAthletes(false);
    }
  };

  const handleExportAthletes = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/admin/athletes/export-excel');
      if (!response.ok) throw new Error('Failed to export athletes');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'athletes_export.xlsx';
      link.click();
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div style={{ padding: '1rem' }}>
      <h2 style={{ marginBottom: '1.5rem', color: '#333' }}>Athlete Management</h2>

      {error && (
        <div style={{
          color: '#dc2626',
          marginBottom: '1rem',
          padding: '0.75rem',
          backgroundColor: '#fef2f2',
          borderRadius: '4px'
        }}>
          {error}
        </div>
      )}

      {/* Export Athletes Section */}
      <div style={{ marginBottom: '2rem' }}>
        <h3 style={{ marginBottom: '1rem', color: '#666' }}>Export All Athletes</h3>
        <button
          onClick={handleExportAthletes}
          style={{
            padding: '0.75rem 1.5rem',
            backgroundColor: '#059669',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          📥 Download Excel
        </button>
      </div>

      {/* Search Athletes Section */}
      <div>
        <h3 style={{ marginBottom: '1rem', color: '#666' }}>Search Athletes</h3>
        <div style={{ marginBottom: '1rem' }}>
          <input
            type="text"
            value={athleteSearchQuery}
            onChange={(e) => {
              setAthleteSearchQuery(e.target.value);
              searchAthletes(e.target.value);
            }}
            placeholder="Search by athlete name..."
            style={{
              width: '100%',
              padding: '0.75rem',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontSize: '1rem',
              boxSizing: 'border-box'
            }}
          />
        </div>

        {searchingAthletes && <p>Searching...</p>}

        {athleteSearchResults.length > 0 && (
          <div style={{
            border: '1px solid #ddd',
            borderRadius: '4px',
            maxHeight: '300px',
            overflowY: 'auto'
          }}>
            {athleteSearchResults.map(athlete => (
              <div
                key={athlete.id}
                style={{
                  padding: '0.75rem',
                  borderBottom: '1px solid #eee',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}
              >
                <div>
                  <div style={{ fontWeight: '500' }}>{athlete.name}</div>
                  <div style={{ fontSize: '0.85rem', color: '#666' }}>
                    {athlete.gender} | {athlete.birth_date || 'N/A'} | {athlete.club_name || 'N/A'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AthleteManagement;
