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
          Download Excel
        </button>
      </div>

      {/* Search Athletes Section */}
      <div>
        <h3 style={{ marginBottom: '1rem', color: '#666' }}>Search Athletes by Name</h3>
        <p style={{ fontSize: '0.9rem', color: '#666', marginBottom: '1rem' }}>
          Enter partial name words to find potential matches (useful for matching SEAG athletes)
        </p>
        <div style={{ marginBottom: '1rem' }}>
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
              padding: '0.75rem',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontSize: '1rem',
              boxSizing: 'border-box'
            }}
          />
        </div>

        {searchingAthletes && <p style={{ color: '#666' }}>Searching...</p>}

        {athleteSearchResults.length > 0 && (
          <div style={{
            border: '1px solid #ddd',
            borderRadius: '4px',
            maxHeight: '500px',
            overflowY: 'auto'
          }}>
            <div style={{
              padding: '0.75rem',
              backgroundColor: '#f9fafb',
              borderBottom: '1px solid #ddd',
              fontSize: '0.85rem',
              color: '#666',
              fontWeight: '500'
            }}>
              {athleteSearchResults.length} result{athleteSearchResults.length !== 1 ? 's' : ''}
            </div>
            {athleteSearchResults.map(athlete => (
              <div
                key={athlete.id}
                style={{
                  padding: '1rem',
                  borderBottom: '1px solid #eee',
                  backgroundColor: '#ffffff'
                }}
              >
                <div style={{ marginBottom: '0.5rem' }}>
                  <div style={{ fontWeight: '600', fontSize: '1rem', color: '#111' }}>
                    {athlete.name}
                  </div>
                </div>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: '1rem',
                  fontSize: '0.85rem',
                  marginBottom: '0.75rem'
                }}>
                  <div>
                    <div style={{ color: '#666', fontSize: '0.75rem', marginBottom: '0.25rem' }}>ATHLETE ID</div>
                    <div style={{
                      fontFamily: 'monospace',
                      color: '#cc0000',
                      fontWeight: '600',
                      wordBreak: 'break-all'
                    }}>
                      {athlete.id}
                    </div>
                  </div>
                  <div>
                    <div style={{ color: '#666', fontSize: '0.75rem', marginBottom: '0.25rem' }}>BIRTHDATE</div>
                    <div style={{ fontWeight: '500', color: '#333' }}>
                      {athlete.birth_date || 'Not recorded'}
                    </div>
                  </div>
                </div>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: '1rem',
                  fontSize: '0.85rem',
                  marginBottom: '0.75rem'
                }}>
                  <div>
                    <div style={{ color: '#666', fontSize: '0.75rem', marginBottom: '0.25rem' }}>GENDER</div>
                    <div style={{ fontWeight: '500', color: '#333' }}>
                      {athlete.gender || '-'}
                    </div>
                  </div>
                  <div>
                    <div style={{ color: '#666', fontSize: '0.75rem', marginBottom: '0.25rem' }}>CLUB</div>
                    <div style={{ fontWeight: '500', color: '#333' }}>
                      {athlete.club_name || 'N/A'}
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => handleCopyId(athlete.id)}
                  style={{
                    padding: '0.4rem 0.8rem',
                    backgroundColor: '#cc0000',
                    color: 'white',
                    border: 'none',
                    borderRadius: '3px',
                    cursor: 'pointer',
                    fontSize: '0.85rem',
                    fontWeight: '500'
                  }}
                >
                  Copy ID
                </button>
              </div>
            ))}
          </div>
        )}

        {athleteSearchQuery.length > 0 && !searchingAthletes && athleteSearchResults.length === 0 && (
          <div style={{
            padding: '1rem',
            backgroundColor: '#fef3f2',
            border: '1px solid #fecaca',
            borderRadius: '4px',
            color: '#991b1b',
            fontSize: '0.9rem'
          }}>
            No athletes found matching "{athleteSearchQuery}". Try different name variations or partial words.
          </div>
        )}
      </div>
    </div>
  );
};

export default AthleteManagement;
