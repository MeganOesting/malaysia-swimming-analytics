import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';

interface ConversionResult {
  success: boolean;
  message: string;
  athletes: number;
  results: number;
  events: number;
  meets: number;
}

export default function AdminPage() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState(false);
  const [conversionResult, setConversionResult] = useState<ConversionResult | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [meetName, setMeetName] = useState('');
  const [meetCode, setMeetCode] = useState('');
  const [existingMeets, setExistingMeets] = useState<any[]>([]);
  const [selectedExistingMeet, setSelectedExistingMeet] = useState('');
  const [uploadMode, setUploadMode] = useState<'new' | 'existing'>('new');

  const router = useRouter();

  // Check if already authenticated and load existing meets
  useEffect(() => {
    const authStatus = localStorage.getItem('admin_authenticated');
    if (authStatus === 'true') {
      setIsAuthenticated(true);
      loadExistingMeets();
    }
  }, []);

  const loadExistingMeets = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/meets');
      const data = await response.json();
      setExistingMeets(data.meets || []);
    } catch (err) {
      console.error('Failed to load existing meets:', err);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      const response = await fetch('http://localhost:8000/api/admin/authenticate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ password }),
      });

      if (response.ok) {
        setIsAuthenticated(true);
        localStorage.setItem('admin_authenticated', 'true');
        setPassword('');
        loadExistingMeets();
      } else {
        setError('Invalid password');
      }
    } catch (err) {
      setError('Authentication failed');
    }
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    localStorage.removeItem('admin_authenticated');
    setPassword('');
    setError('');
    setConversionResult(null);
    setSelectedFile(null);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setConversionResult(null);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;
    
    // Validate based on upload mode
    if (uploadMode === 'new' && (!meetName || !meetCode)) return;
    if (uploadMode === 'existing' && !selectedExistingMeet) return;

    setUploading(true);
    setError('');
    setConversionResult(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      
      if (uploadMode === 'new') {
        formData.append('meet_name', meetName);
        formData.append('meet_code', meetCode);
      } else {
        formData.append('existing_meet_id', selectedExistingMeet);
      }

      const response = await fetch('http://localhost:8000/api/admin/convert-excel', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (response.ok) {
        setConversionResult(result);
        setSelectedFile(null);
        setMeetName('');
        setMeetCode('');
        setSelectedExistingMeet('');
        setUploadMode('new');
        // Reset file input
        const fileInput = document.getElementById('excel-file') as HTMLInputElement;
        if (fileInput) fileInput.value = '';
        // Reload existing meets
        loadExistingMeets();
      } else {
        setError(result.message || 'Conversion failed');
      }
    } catch (err) {
      setError('Upload failed');
    } finally {
      setUploading(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <div style={{ 
        fontFamily: 'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#f5f5f5'
      }}>
        <div style={{
          backgroundColor: 'white',
          padding: '2rem',
          borderRadius: '8px',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
          width: '100%',
          maxWidth: '400px'
        }}>
          <h1 style={{ 
            textAlign: 'center', 
            marginBottom: '1.5rem',
            color: '#333'
          }}>
            Admin Access
          </h1>
          
          <form onSubmit={handleLogin}>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ 
                display: 'block', 
                marginBottom: '0.5rem',
                fontWeight: '500'
              }}>
                Password:
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontSize: '1rem'
                }}
                required
              />
            </div>
            
            {error && (
              <div style={{
                color: '#dc2626',
                marginBottom: '1rem',
                padding: '0.5rem',
                backgroundColor: '#fef2f2',
                borderRadius: '4px',
                border: '1px solid #fecaca'
              }}>
                {error}
              </div>
            )}
            
            <button
              type="submit"
              style={{
                width: '100%',
                padding: '0.75rem',
                backgroundColor: '#cc0000',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                fontSize: '1rem',
                cursor: 'pointer'
              }}
            >
              Login
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div style={{ 
      fontFamily: 'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
      minHeight: '100vh',
      backgroundColor: '#f5f5f5',
      padding: '2rem'
    }}>
      <div style={{
        maxWidth: '800px',
        margin: '0 auto',
        backgroundColor: 'white',
        borderRadius: '8px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        padding: '2rem'
      }}>
        {/* Header */}
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          marginBottom: '2rem',
          paddingBottom: '1rem',
          borderBottom: '1px solid #e5e5e5'
        }}>
          <h1 style={{ margin: 0, color: '#333' }}>
            Admin Panel - Excel Conversion
          </h1>
          <div>
            <button
              onClick={() => router.push('/')}
              style={{
                padding: '0.5rem 1rem',
                marginRight: '0.5rem',
                backgroundColor: '#6b7280',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Back to Main
            </button>
            <button
              onClick={handleLogout}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#dc2626',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Logout
            </button>
          </div>
        </div>

        {/* Upload Form */}
        <form onSubmit={handleUpload}>
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ 
              display: 'block', 
              marginBottom: '0.5rem',
              fontWeight: '500',
              fontSize: '1.1rem'
            }}>
              Upload Excel Meet File:
            </label>
            <input
              id="excel-file"
              type="file"
              accept=".xlsx,.xls"
              onChange={handleFileSelect}
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '1rem'
              }}
              required
            />
            <p style={{ 
              marginTop: '0.5rem',
              color: '#666',
              fontSize: '0.9rem'
            }}>
              Supported formats: .xlsx, .xls. The file will be processed using the same logic as the old build.
            </p>
          </div>

          {/* Upload Mode Selection */}
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ 
              display: 'block', 
              marginBottom: '0.5rem',
              fontWeight: '500',
              fontSize: '1.1rem'
            }}>
              Upload Mode:
            </label>
            <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
              <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                <input
                  type="radio"
                  name="uploadMode"
                  value="new"
                  checked={uploadMode === 'new'}
                  onChange={(e) => setUploadMode(e.target.value as 'new' | 'existing')}
                  style={{ marginRight: '0.5rem' }}
                />
                Create New Meet
              </label>
              <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                <input
                  type="radio"
                  name="uploadMode"
                  value="existing"
                  checked={uploadMode === 'existing'}
                  onChange={(e) => setUploadMode(e.target.value as 'new' | 'existing')}
                  style={{ marginRight: '0.5rem' }}
                />
                Add to Existing Meet
              </label>
            </div>
          </div>

          {/* New Meet Fields */}
          {uploadMode === 'new' && (
            <>
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ 
                  display: 'block', 
                  marginBottom: '0.5rem',
                  fontWeight: '500',
                  fontSize: '1.1rem'
                }}>
                  Meet Name (Display Name):
                </label>
                <input
                  type="text"
                  value={meetName}
                  onChange={(e) => setMeetName(e.target.value)}
                  placeholder="e.g., SEA Age 25"
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    fontSize: '1rem'
                  }}
                  required
                />
                <p style={{ 
                  marginTop: '0.5rem',
                  color: '#666',
                  fontSize: '0.9rem'
                }}>
                  This is the name that will appear in the meet selection dropdown.
                </p>
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ 
                  display: 'block', 
                  marginBottom: '0.5rem',
                  fontWeight: '500',
                  fontSize: '1.1rem'
                }}>
                  Meet Code (Internal ID):
                </label>
                <input
                  type="text"
                  value={meetCode}
                  onChange={(e) => setMeetCode(e.target.value)}
                  placeholder="e.g., SEAG25"
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    fontSize: '1rem'
                  }}
                  required
                />
                <p style={{ 
                  marginTop: '0.5rem',
                  color: '#666',
                  fontSize: '0.9rem'
                }}>
                  This is the internal code used for database storage and API calls.
                </p>
              </div>
            </>
          )}

          {/* Existing Meet Selection */}
          {uploadMode === 'existing' && (
            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ 
                display: 'block', 
                marginBottom: '0.5rem',
                fontWeight: '500',
                fontSize: '1.1rem'
              }}>
                Select Existing Meet:
              </label>
              <select
                value={selectedExistingMeet}
                onChange={(e) => setSelectedExistingMeet(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontSize: '1rem'
                }}
                required
              >
                <option value="">Choose a meet...</option>
                {existingMeets.map((meet) => (
                  <option key={meet.id} value={meet.id}>
                    {meet.name} ({meet.id})
                  </option>
                ))}
              </select>
              <p style={{ 
                marginTop: '0.5rem',
                color: '#666',
                fontSize: '0.9rem'
              }}>
                Select the meet you want to add this data to. This is useful for uploading men's and women's files for the same meet.
              </p>
            </div>
          )}

          {error && (
            <div style={{
              color: '#dc2626',
              marginBottom: '1rem',
              padding: '0.75rem',
              backgroundColor: '#fef2f2',
              borderRadius: '4px',
              border: '1px solid #fecaca'
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={!selectedFile || !meetName || !meetCode || uploading}
            style={{
              padding: '0.75rem 2rem',
              backgroundColor: (selectedFile && meetName && meetCode && !uploading) ? '#cc0000' : '#9ca3af',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontSize: '1rem',
              cursor: (selectedFile && meetName && meetCode && !uploading) ? 'pointer' : 'not-allowed'
            }}
          >
            {uploading ? 'Converting...' : 'Convert & Store'}
          </button>
        </form>

        {/* Conversion Results */}
        {conversionResult && (
          <div style={{
            marginTop: '2rem',
            padding: '1rem',
            backgroundColor: conversionResult.success ? '#f0fdf4' : '#fef2f2',
            border: `1px solid ${conversionResult.success ? '#bbf7d0' : '#fecaca'}`,
            borderRadius: '4px'
          }}>
            <h3 style={{ 
              margin: '0 0 1rem 0',
              color: conversionResult.success ? '#166534' : '#dc2626'
            }}>
              {conversionResult.success ? 'Conversion Successful!' : 'Conversion Failed'}
            </h3>
            <p style={{ margin: '0 0 1rem 0', color: '#374151' }}>
              {conversionResult.message}
            </p>
            {conversionResult.success && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#cc0000' }}>
                    {conversionResult.athletes}
                  </div>
                  <div style={{ color: '#666' }}>Athletes</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#cc0000' }}>
                    {conversionResult.results}
                  </div>
                  <div style={{ color: '#666' }}>Results</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#cc0000' }}>
                    {conversionResult.events}
                  </div>
                  <div style={{ color: '#666' }}>Events</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#cc0000' }}>
                    {conversionResult.meets}
                  </div>
                  <div style={{ color: '#666' }}>Meets</div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Instructions */}
        <div style={{
          marginTop: '2rem',
          padding: '1rem',
          backgroundColor: '#f8fafc',
          border: '1px solid #e2e8f0',
          borderRadius: '4px'
        }}>
          <h3 style={{ margin: '0 0 1rem 0', color: '#1e293b' }}>
            Instructions:
          </h3>
          <ul style={{ margin: 0, paddingLeft: '1.5rem', color: '#475569' }}>
            <li>Upload an Excel file (.xlsx or .xls) containing swimming meet results</li>
            <li>The file will be processed using the same logic as the old build</li>
            <li>Only sheets with valid swimming events will be processed</li>
            <li>Relay events and 5000m events will be automatically excluded</li>
            <li>After conversion, the data will be available in the main application</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
