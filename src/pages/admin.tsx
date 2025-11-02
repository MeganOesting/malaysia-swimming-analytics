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

interface Meet {
  id: string;
  name: string;
  alias: string;
  date: string;
  city: string;
  result_count: number;
}

interface Athlete {
  id: string;
  name: string;
  gender: string;
  birth_date: string | null;
  club_name: string | null;
  state_code: string | null;
  nation: string | null;
}

interface SelectedAthlete extends Athlete {
  selected: boolean;
}

interface ManualResult {
  athlete_id: string;
  athlete_name: string;
  event_distance: number;
  event_stroke: string;
  event_gender: string;
  time_string: string;
  place: number | null;
}

export default function AdminPage() {
  try {
    console.log('🔵 AdminPage component rendering...');
  } catch (e) {
    console.error('Error in AdminPage render:', e);
  }
  
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState(false);
  const [conversionResult, setConversionResult] = useState<ConversionResult | null>(null);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [meets, setMeets] = useState<Meet[]>([]);
  const [editingAlias, setEditingAlias] = useState<{ [key: string]: string }>({});
  const [loadingMeets, setLoadingMeets] = useState(false);
  
  // Manual entry state
  const [activeTab, setActiveTab] = useState<'upload' | 'manual' | 'manage'>('upload');
  const [manualStep, setManualStep] = useState<1 | 2 | 3>(1);
  const [athleteSearchQuery, setAthleteSearchQuery] = useState('');
  const [athleteSearchResults, setAthleteSearchResults] = useState<Athlete[]>([]);
  const [selectedAthletes, setSelectedAthletes] = useState<SelectedAthlete[]>([]);
  const [meetName, setMeetName] = useState('');
  const [meetDate, setMeetDate] = useState('');
  const [meetCity, setMeetCity] = useState('');
  const [meetCourse, setMeetCourse] = useState<'LCM' | 'SCM'>('LCM');
  const [meetAlias, setMeetAlias] = useState('');
  const [selectedEvents, setSelectedEvents] = useState<{distance: number, stroke: string, gender: string}[]>([]);
  const [manualResults, setManualResults] = useState<ManualResult[]>([]);
  const [searchingAthletes, setSearchingAthletes] = useState(false);

  const router = useRouter();

  console.log('🔵 AdminPage state - isAuthenticated:', isAuthenticated, 'loadingMeets:', loadingMeets, 'meets:', meets.length);

  // Manual entry functions - must be defined before useEffect hooks
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

  // Check if already authenticated and fetch meets
  useEffect(() => {
    console.log('AdminPage useEffect running...');
    const authStatus = localStorage.getItem('admin_authenticated');
    console.log('Auth status:', authStatus);
    
    let abortController: AbortController | null = null;
    
    if (authStatus === 'true') {
      console.log('User authenticated, setting state...');
      setIsAuthenticated(true);
      // Small delay to ensure component is fully mounted
      const timer = setTimeout(() => {
        console.log('Calling fetchMeets from useEffect...');
        fetchMeets();
      }, 100);
      
      // Cleanup function
      return () => {
        clearTimeout(timer);
      };
    } else {
      console.log('User not authenticated');
      setIsAuthenticated(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Athlete search useEffect - must be before early return
  useEffect(() => {
    if (athleteSearchQuery.length >= 2) {
      const timer = setTimeout(() => {
        searchAthletes(athleteSearchQuery);
      }, 200); // Reduced debounce for faster response
      return () => clearTimeout(timer);
    } else {
      setAthleteSearchResults([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [athleteSearchQuery]);

  // Debug: log uploadedFiles whenever it changes - must be before early return
  useEffect(() => {
    console.log('📁 uploadedFiles state changed:', uploadedFiles.length, 'files:', uploadedFiles.map(f => f.name));
  }, [uploadedFiles]);

  const fetchMeets = async () => {
    console.log('=== fetchMeets called ===');
    try {
      console.log('Setting loadingMeets to true...');
      setLoadingMeets(true);
      setError(''); // Clear previous errors
      
      console.log('Fetching meets from API: http://localhost:8000/api/admin/meets');
      
      // Add timeout to fetch
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
      
      const response = await fetch('http://localhost:8000/api/admin/meets', {
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      console.log('Fetch completed, status:', response.status);
      
      console.log('Response status:', response.status, response.statusText);
      
      if (!response.ok) {
        throw new Error(`Server error: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('Received data:', data);
      console.log('Meets count:', data.meets?.length);
      
      if (data.error) {
        setError(`Error loading meets: ${data.error}`);
        setMeets([]);
      } else if (data.meets) {
        console.log('Setting meets:', data.meets.length);
        setMeets(data.meets);
        if (data.meets.length === 0) {
          console.log('No meets found in database');
        }
      } else {
        console.warn('No meets property in response:', data);
        setMeets([]);
      }
    } catch (err: any) {
      // AbortError is expected during hot reload - don't show error for it
      if (err.name === 'AbortError') {
        console.log('Fetch aborted (likely due to hot reload) - this is normal in development');
        return; // Don't update state on abort
      }
      
      console.error('Failed to fetch meets:', err);
      if (err.message?.includes('timeout') || err.message?.includes('timed out')) {
        setError('Request timed out. The backend may not be responding. Please check if the FastAPI server is running at http://localhost:8000');
      } else {
        setError(`Failed to fetch meets: ${err.message || 'Unknown error'}. Please check if the backend server is running.`);
      }
      setMeets([]);
    } finally {
      console.log('Setting loading to false');
      // Force update with a small delay to ensure React processes it
      setTimeout(() => {
        setLoadingMeets(false);
        console.log('Loading state set to false');
      }, 0);
    }
  };

  const handleUpdateAlias = async (meetId: string, newAlias: string) => {
    if (!newAlias.trim()) {
      setError('Alias cannot be empty');
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/api/admin/meets/${meetId}/alias`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ alias: newAlias.trim() }),
      });

      const result = await response.json();

      if (response.ok) {
        setError('');
        setEditingAlias({});
        await fetchMeets(); // Refresh the list
      } else {
        setError(result.detail || result.message || 'Update failed');
      }
    } catch (err: any) {
      setError(err.message || 'Update failed');
    }
  };

  const handleDeleteMeet = async (meetId: string, meetName: string) => {
    if (!confirm(`Are you sure you want to delete "${meetName}"? This will also delete all associated results. This cannot be undone.`)) {
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/api/admin/meets/${meetId}`, {
        method: 'DELETE',
      });

      const result = await response.json();

      if (response.ok) {
        setError('');
        await fetchMeets(); // Refresh the list
        alert(`✅ ${result.message}`);
      } else {
        setError(result.detail || result.message || 'Delete failed');
      }
    } catch (err: any) {
      setError(err.message || 'Delete failed');
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    console.log('Login attempt with password:', password);

    try {
      console.log('Sending request to http://localhost:8000/api/admin/authenticate');
      const response = await fetch('http://localhost:8000/api/admin/authenticate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ password }),
      });

      console.log('Response received. Status:', response.status);
      console.log('Response ok:', response.ok);
      
      let result;
      try {
        result = await response.json();
        console.log('Response data:', result);
      } catch (jsonError) {
        console.error('Failed to parse JSON response:', jsonError);
        const text = await response.text();
        console.error('Response text:', text);
        throw new Error(`Server returned non-JSON response: ${text}`);
      }

      if (response.ok) {
        setIsAuthenticated(true);
        localStorage.setItem('admin_authenticated', 'true');
        setPassword('');
        setError('');
        await fetchMeets(); // Fetch meets after successful login
      } else {
        setError(result.detail || result.message || 'Invalid password');
      }
    } catch (err: any) {
      console.error('Login error:', err);
      setError(err.message || 'Authentication failed. Check console for details.');
    }
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    localStorage.removeItem('admin_authenticated');
    setPassword('');
    setError('');
    setConversionResult(null);
    setUploadedFiles([]);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    console.log('🔵 File input changed. files:', files, 'length:', files?.length);
    
    if (files && files.length > 0) {
      const newFiles = Array.from(files);
      console.log(`✅ File select: received ${newFiles.length} file(s):`, newFiles.map(f => `${f.name} (${f.size} bytes)`));
      
      // Add new files to existing ones (avoid duplicates by filename)
      setUploadedFiles(prevFiles => {
        console.log(`📦 Previous files in state: ${prevFiles.length}`);
        const existingFilenames = new Set(prevFiles.map(f => f.name));
        const uniqueNewFiles = newFiles.filter(f => !existingFilenames.has(f.name));
        const updatedFiles = [...prevFiles, ...uniqueNewFiles];
        console.log(`✅ File select: total files now ${updatedFiles.length}:`, updatedFiles.map(f => f.name));
        return updatedFiles;
      });
      setConversionResult(null);
      setError(''); // Clear any previous errors
    } else {
      console.log('⚠️ File input changed but no files selected');
    }
    
    // Reset the input value to allow selecting the same files again if needed
    // (This doesn't clear our state, just the input element)
    e.target.value = '';
  };

  const handleRemoveFile = (index: number) => {
    setUploadedFiles(prevFiles => prevFiles.filter((_, i) => i !== index));
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    
    console.log('Upload triggered. Files in state:', uploadedFiles.length, uploadedFiles.map(f => f.name));
    
    if (uploadedFiles.length === 0) {
      setError('Please select at least one file to upload');
      return;
    }

    setUploading(true);
    setError('');
    setConversionResult(null);

    try {
      const formData = new FormData();
      
      console.log('Creating FormData with files:', uploadedFiles.length);
      
      // Add all uploaded files - gender will be auto-detected from file contents
      for (const file of uploadedFiles) {
        if (!file || !(file instanceof File)) {
          console.error('Invalid file object:', file);
          setError(`Invalid file detected: ${file}`);
          setUploading(false);
          return;
        }
        console.log(`Adding file to FormData: ${file.name} (${file.size} bytes)`);
        formData.append('files', file);
      }
      
      console.log('FormData created, sending request...');

      const response = await fetch('http://localhost:8000/api/admin/convert-excel', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (response.ok) {
        setConversionResult(result);
        // Reset form
        setUploadedFiles([]);
        // Reset file input
        const fileInput = document.getElementById('meet-files') as HTMLInputElement;
        if (fileInput) fileInput.value = '';
        // Refresh meets list
        await fetchMeets();
      } else {
        setError(result.detail || result.message || 'Conversion failed');
      }
    } catch (err: any) {
      setError(err.message || 'Upload failed');
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
          <p style={{ 
            textAlign: 'center', 
            marginBottom: '1rem',
            color: '#666',
            fontSize: '0.9rem'
          }}>
            Enter password to access admin panel
          </p>
          
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

  const handleAddAthlete = (athlete: Athlete) => {
    if (!selectedAthletes.find(a => a.id === athlete.id)) {
      setSelectedAthletes([...selectedAthletes, { ...athlete, selected: true }]);
    }
  };

  const handleRemoveAthlete = (athleteId: string) => {
    setSelectedAthletes(selectedAthletes.filter(a => a.id !== athleteId));
  };

  const handleNextToStep2 = () => {
    if (selectedAthletes.length === 0) {
      setError('Please select at least one athlete');
      return;
    }
    setManualStep(2);
    setError('');
  };

  const handleNextToStep3 = () => {
    if (!meetName || !meetDate || selectedEvents.length === 0) {
      setError('Please fill in meet name, date, and select at least one event');
      return;
    }
    
    // Initialize results: one row per athlete x event combination
    const results: ManualResult[] = [];
    selectedAthletes.forEach(athlete => {
      selectedEvents.forEach(event => {
        // Only add if gender matches
        if (event.gender === athlete.gender || event.gender === '') {
          results.push({
            athlete_id: athlete.id,
            athlete_name: athlete.name,
            event_distance: event.distance,
            event_stroke: event.stroke,
            event_gender: event.gender || athlete.gender,
            time_string: '',
            place: null
          });
        }
      });
    });
    
    setManualResults(results);
    setManualStep(3);
    setError('');
  };

  const handleSubmitManualResults = async () => {
    if (manualResults.some(r => !r.time_string.trim())) {
      setError('Please enter times for all results');
      return;
    }

    setUploading(true);
    setError('');
    
    try {
      const response = await fetch('http://localhost:8000/api/admin/manual-results', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          meet_name: meetName,
          meet_date: meetDate,
          meet_city: meetCity || undefined,
          course: meetCourse,
          alias: meetAlias || undefined,
          results: manualResults.map(r => ({
            athlete_id: r.athlete_id,
            event_distance: r.event_distance,
            event_stroke: r.event_stroke,
            event_gender: r.event_gender,
            time_string: r.time_string,
            place: r.place || undefined
          }))
        })
      });

      const result = await response.json();

      if (response.ok) {
        alert(`✅ ${result.message}`);
        // Reset manual entry
        setManualStep(1);
        setSelectedAthletes([]);
        setAthleteSearchQuery('');
        setMeetName('');
        setMeetDate('');
        setMeetCity('');
        setMeetAlias('');
        setSelectedEvents([]);
        setManualResults([]);
        await fetchMeets();
      } else {
        setError(result.detail || result.message || 'Failed to create manual results');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to submit manual results');
    } finally {
      setUploading(false);
    }
  };

  const canSubmit = uploadedFiles.length > 0 && !uploading;

  return (
    <div style={{ 
      fontFamily: 'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
      minHeight: '100vh',
      backgroundColor: '#f5f5f5',
      padding: '1.5rem'
    }}>
      <div style={{
        maxWidth: '1400px',
        margin: '0 auto',
        backgroundColor: 'white',
        borderRadius: '8px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        padding: '1.5rem'
      }}>
        {/* Header */}
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          marginBottom: '1.5rem',
          paddingBottom: '0.75rem',
          borderBottom: '1px solid #e5e5e5'
        }}>
          <h1 style={{ margin: 0, color: '#333', fontSize: '1.5rem' }}>
            Admin Panel - Meet Management
          </h1>
          <div>
            <button
              onClick={() => router.push('/')}
              style={{
                padding: '0.4rem 0.8rem',
                marginRight: '0.5rem',
                backgroundColor: '#6b7280',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.85rem'
              }}
            >
              Back to Main
            </button>
            <button
              onClick={handleLogout}
              style={{
                padding: '0.4rem 0.8rem',
                backgroundColor: '#dc2626',
                color: 'white',
                fontSize: '0.85rem',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Logout
            </button>
          </div>
        </div>

        {/* Tab Selection */}
        <div style={{ 
          display: 'flex', 
          gap: '0.5rem', 
          marginBottom: '1rem',
          borderBottom: '2px solid #e5e5e5'
        }}>
          <button
            type="button"
            onClick={() => {
              setActiveTab('upload');
              setError('');
            }}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: activeTab === 'upload' ? '#cc0000' : '#ffcccc',
              color: activeTab === 'upload' ? 'white' : '#000',
              border: activeTab === 'upload' ? 'none' : '1px solid #cc0000',
              borderBottom: activeTab === 'upload' ? '3px solid #cc0000' : '3px solid transparent',
              borderRadius: '4px 4px 0 0',
              cursor: 'pointer',
              fontSize: '0.9rem',
              fontWeight: activeTab === 'upload' ? '600' : '400'
            }}
          >
            File Upload
          </button>
          <button
            type="button"
            onClick={() => {
              setActiveTab('manual');
              setError('');
            }}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: activeTab === 'manual' ? '#cc0000' : '#ffcccc',
              color: activeTab === 'manual' ? 'white' : '#000',
              border: activeTab === 'manual' ? 'none' : '1px solid #cc0000',
              borderBottom: activeTab === 'manual' ? '3px solid #cc0000' : '3px solid transparent',
              borderRadius: '4px 4px 0 0',
              cursor: 'pointer',
              fontSize: '0.9rem',
              fontWeight: activeTab === 'manual' ? '600' : '400'
            }}
          >
            Manual Entry
          </button>
          <button
            type="button"
            onClick={() => {
              setActiveTab('manage');
              setError('');
              fetchMeets();
            }}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: activeTab === 'manage' ? '#cc0000' : '#ffcccc',
              color: activeTab === 'manage' ? 'white' : '#000',
              border: activeTab === 'manage' ? 'none' : '1px solid #cc0000',
              borderBottom: activeTab === 'manage' ? '3px solid #cc0000' : '3px solid transparent',
              borderRadius: '4px 4px 0 0',
              cursor: 'pointer',
              fontSize: '0.9rem',
              fontWeight: activeTab === 'manage' ? '600' : '400'
            }}
          >
            Manage Existing Meets
          </button>
        </div>

        {/* File Upload Tab */}
        {activeTab === 'upload' && (
        <form onSubmit={handleUpload}>
          {/* File Upload - Label, Choose Files button, and Upload button on same line */}
          <div style={{ marginBottom: '1rem' }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '1rem',
              marginBottom: '0.25rem'
            }}>
              {/* Label */}
              <label style={{ 
                fontWeight: '500',
                fontSize: '0.95rem',
                whiteSpace: 'nowrap',
                color: '#000'
              }}>
                Meet Files <span style={{ color: '#dc2626' }}>*</span>:
              </label>
              
              {/* Hidden file input */}
            <input
                id="meet-files"
                type="file"
                accept=".xlsx,.xls"
                onChange={handleFileSelect}
                multiple
              style={{
                  display: 'none'
                }}
              />
              
              {/* Custom button to trigger file selection */}
              <button
                type="button"
                onClick={() => {
                  const fileInput = document.getElementById('meet-files') as HTMLInputElement;
                  if (fileInput) fileInput.click();
                }}
                style={{
                  flex: '1',
                padding: '0.75rem',
                  border: uploadedFiles.length > 0 ? '2px solid #059669' : '1px solid #ddd',
                borderRadius: '4px',
                  fontSize: '1rem',
                  backgroundColor: uploadedFiles.length > 0 ? '#f0fdf4' : '#fff',
                  color: '#374151',
                  cursor: 'pointer',
                  fontWeight: '500',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem'
                }}
              >
                <span>📁</span>
                <span>{uploadedFiles.length > 0 ? `Add More Files (${uploadedFiles.length} selected)` : 'Choose Files'}</span>
              </button>
              
              {/* Upload button on same line */}
              <button
                type="submit"
                disabled={!canSubmit || uploading}
                onClick={(e) => {
                  console.log('Button clicked. canSubmit:', canSubmit, 'uploadedFiles.length:', uploadedFiles.length, 'uploading:', uploading);
                  if (!canSubmit) {
                    e.preventDefault();
                    setError(`Cannot submit: ${uploadedFiles.length} files selected, uploading: ${uploading}`);
                  }
                }}
                style={{
                  padding: '0.5rem 1.25rem',
                  backgroundColor: canSubmit && !uploading ? '#059669' : '#9ca3af',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  fontSize: '0.9rem',
                  cursor: canSubmit && !uploading ? 'pointer' : 'not-allowed',
                  whiteSpace: 'nowrap',
                  fontWeight: '600'
                }}
              >
                {uploading ? 'Processing...' : 'Upload & Convert Meet'}
              </button>
            </div>
            {uploadedFiles.length > 0 && (
              <div style={{ marginTop: '0.25rem' }}>
                <p style={{ color: '#059669', fontSize: '0.8rem', fontWeight: '500', marginBottom: '0.15rem' }}>
                  ✅ Selected {uploadedFiles.length} file(s) - Ready to upload
                </p>
                <div style={{ 
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  padding: '0.35rem',
                  backgroundColor: '#f9fafb'
                }}>
                  {uploadedFiles.map((file, idx) => (
                    <div
                      key={idx}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '0.35rem',
                        marginBottom: '0.15rem',
                        backgroundColor: 'white',
                        borderRadius: '4px',
                        border: '1px solid #e5e7eb'
                      }}
                    >
                      <span style={{ fontSize: '0.8rem', color: '#000' }}>{file.name}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveFile(idx)}
                        style={{
                          padding: '0.25rem 0.5rem',
                          backgroundColor: '#dc2626',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '0.75rem',
                          marginLeft: '0.5rem'
                        }}
                        title="Remove file"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
            <p style={{ 
              marginTop: '0.25rem',
                  fontSize: '0.75rem', 
                  color: '#000', 
                  fontStyle: 'italic' 
            }}>
                  You can select more files to add them to this list
            </p>
              </div>
            )}
          </div>


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
        </form>
        )}

        {/* Manual Entry Tab */}
        {activeTab === 'manual' && (
            <div>
            {/* Step Indicator */}
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              marginBottom: '2rem',
              position: 'relative'
            }}>
              <div style={{ 
                flex: 1, 
                textAlign: 'center',
                padding: '1rem',
                backgroundColor: manualStep >= 1 ? '#cc0000' : '#e5e5e5',
                color: manualStep >= 1 ? 'white' : '#666',
                borderRadius: '4px',
                marginRight: '0.5rem',
                fontWeight: manualStep === 1 ? '600' : '400'
              }}>
                Step 1: Select Athletes
              </div>
              <div style={{ 
                flex: 1, 
                textAlign: 'center',
                padding: '1rem',
                backgroundColor: manualStep >= 2 ? '#cc0000' : '#e5e5e5',
                color: manualStep >= 2 ? 'white' : '#666',
                borderRadius: '4px',
                marginRight: '0.5rem',
                marginLeft: '0.5rem',
                fontWeight: manualStep === 2 ? '600' : '400'
              }}>
                Step 2: Meet Info
              </div>
              <div style={{ 
                flex: 1, 
                textAlign: 'center',
                padding: '1rem',
                backgroundColor: manualStep >= 3 ? '#cc0000' : '#e5e5e5',
                color: manualStep >= 3 ? 'white' : '#666',
                borderRadius: '4px',
                marginLeft: '0.5rem',
                fontWeight: manualStep === 3 ? '600' : '400'
              }}>
                Step 3: Enter Times
              </div>
            </div>

            {/* Step 1: Athlete Selection */}
            {manualStep === 1 && (
              <div>
                <h2 style={{ marginBottom: '1rem', color: '#333' }}>Select Athletes</h2>
                
                {/* Search */}
                <div style={{ marginBottom: '1.5rem' }}>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
                    Search Athletes (type name):
              </label>
              <input
                type="text"
                    value={athleteSearchQuery}
                    onChange={(e) => setAthleteSearchQuery(e.target.value)}
                    placeholder="Start typing athlete name..."
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontSize: '1rem'
                }}
              />
                  {searchingAthletes && (
                    <p style={{ marginTop: '0.5rem', color: '#666', fontSize: '0.9rem' }}>Searching...</p>
                  )}
            </div>

                {/* Search Results */}
                {athleteSearchResults.length > 0 && (
                  <div style={{ marginBottom: '1.5rem' }}>
                    <h3 style={{ marginBottom: '0.5rem', fontSize: '1rem', color: '#666' }}>Search Results:</h3>
                    <div style={{ 
                      maxHeight: '300px', 
                      overflowY: 'auto',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      padding: '0.5rem'
                    }}>
                      {athleteSearchResults.map(athlete => (
                        <div
                          key={athlete.id}
                          onClick={() => handleAddAthlete(athlete)}
                          style={{
                            padding: '0.75rem',
                            marginBottom: '0.5rem',
                            backgroundColor: '#f8f9fa',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            border: selectedAthletes.find(a => a.id === athlete.id) 
                              ? '2px solid #059669' 
                              : '1px solid #ddd',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center'
                          }}
                        >
            <div>
                            <div style={{ fontWeight: '500' }}>{athlete.name}</div>
                            <div style={{ fontSize: '0.85rem', color: '#666' }}>
                              {athlete.gender} | {athlete.birth_date || 'No DOB'} | {athlete.club_name || 'No club'}
                            </div>
                          </div>
                          {selectedAthletes.find(a => a.id === athlete.id) && (
                            <span style={{ color: '#059669', fontWeight: '600' }}>✓ Selected</span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Selected Athletes */}
                {selectedAthletes.length > 0 && (
                  <div style={{ marginBottom: '1.5rem' }}>
                    <h3 style={{ marginBottom: '0.5rem', fontSize: '1rem', color: '#666' }}>
                      Selected Athletes ({selectedAthletes.length}):
                    </h3>
                    <div style={{ 
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      padding: '0.5rem'
                    }}>
                      {selectedAthletes.map(athlete => (
                        <div
                          key={athlete.id}
                          style={{
                            padding: '0.75rem',
                marginBottom: '0.5rem',
                            backgroundColor: '#f0fdf4',
                            borderRadius: '4px',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center'
                          }}
                        >
                          <div>
                            <div style={{ fontWeight: '500' }}>{athlete.name}</div>
                            <div style={{ fontSize: '0.85rem', color: '#666' }}>
                              {athlete.gender} | {athlete.birth_date || 'No DOB'}
                            </div>
                          </div>
                          <button
                            type="button"
                            onClick={() => handleRemoveAthlete(athlete.id)}
                            style={{
                              padding: '0.25rem 0.75rem',
                              backgroundColor: '#dc2626',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              cursor: 'pointer',
                              fontSize: '0.85rem'
                            }}
                          >
                            Remove
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <button
                  type="button"
                  onClick={handleNextToStep2}
                  disabled={selectedAthletes.length === 0}
                  style={{
                    padding: '0.75rem 2rem',
                    backgroundColor: selectedAthletes.length > 0 ? '#cc0000' : '#9ca3af',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    fontSize: '1rem',
                    cursor: selectedAthletes.length > 0 ? 'pointer' : 'not-allowed',
                    width: '100%'
                  }}
                >
                  Next: Enter Meet Information ({selectedAthletes.length} athlete{selectedAthletes.length !== 1 ? 's' : ''} selected)
                </button>
              </div>
            )}

            {/* Step 2: Meet Information */}
            {manualStep === 2 && (
              <div>
                <h2 style={{ marginBottom: '1rem', color: '#333' }}>Meet Information</h2>
                
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                  <div>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
                      Meet Name <span style={{ color: '#dc2626' }}>*</span>:
                    </label>
                    <input
                      type="text"
                      value={meetName}
                      onChange={(e) => setMeetName(e.target.value)}
                      placeholder="e.g., 67th Malaysian Open Championships"
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
                  <div>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
                      Meet Date <span style={{ color: '#dc2626' }}>*</span>:
              </label>
              <input
                type="date"
                value={meetDate}
                onChange={(e) => setMeetDate(e.target.value)}
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
          </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
                      City:
              </label>
              <input
                      type="text"
                      value={meetCity}
                      onChange={(e) => setMeetCity(e.target.value)}
                      placeholder="e.g., Kuala Lumpur"
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontSize: '1rem'
                }}
              />
            </div>
            <div>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
                      Course <span style={{ color: '#dc2626' }}>*</span>:
                    </label>
                    <select
                      value={meetCourse}
                      onChange={(e) => setMeetCourse(e.target.value as 'LCM' | 'SCM')}
                      style={{
                        width: '100%',
                        padding: '0.75rem',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        fontSize: '1rem'
                      }}
                    >
                      <option value="LCM">LCM (Long Course Meters)</option>
                      <option value="SCM">SCM (Short Course Meters)</option>
                    </select>
                  </div>
                </div>

                <div style={{ marginBottom: '1.5rem' }}>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
                    Alias/Code (optional):
              </label>
              <input
                    type="text"
                    value={meetAlias}
                    onChange={(e) => setMeetAlias(e.target.value)}
                    placeholder="e.g., MO25, MIAG25"
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontSize: '1rem'
                }}
              />
                </div>

                {/* Event Selection */}
                <div style={{ marginBottom: '1.5rem' }}>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
                    Select Events <span style={{ color: '#dc2626' }}>*</span>:
                  </label>
                  <div style={{ 
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    padding: '1rem',
                    maxHeight: '300px',
                    overflowY: 'auto'
                  }}>
                    {[50, 100, 200, 400, 800, 1500].map(distance => (
                      ['FR', 'BK', 'BR', 'BU', 'IM'].map(stroke => {
                        const genders = ['M', 'F'];
                        return genders.map(gender => {
                          const eventKey = `${distance}_${stroke}_${gender}`;
                          const isSelected = selectedEvents.some(
                            e => e.distance === distance && e.stroke === stroke && e.gender === gender
                          );
                          return (
                            <label
                              key={eventKey}
                              style={{
                                display: 'flex',
                                alignItems: 'center',
                                padding: '0.5rem',
                                cursor: 'pointer',
                                backgroundColor: isSelected ? '#f0f9ff' : 'transparent',
                                borderRadius: '4px',
                                marginBottom: '0.25rem'
                              }}
                            >
                              <input
                                type="checkbox"
                                checked={isSelected}
                                onChange={(e) => {
                                  if (e.target.checked) {
                                    setSelectedEvents([...selectedEvents, { distance, stroke, gender }]);
                                  } else {
                                    setSelectedEvents(selectedEvents.filter(
                                      e => !(e.distance === distance && e.stroke === stroke && e.gender === gender)
                                    ));
                                  }
                                }}
                                style={{ marginRight: '0.5rem', cursor: 'pointer' }}
                              />
                              <span>{gender} {distance}m {stroke}</span>
                            </label>
                          );
                        });
                      })
                    )).flat(3)}
            </div>
          </div>
          
                <div style={{ display: 'flex', gap: '1rem' }}>
                  <button
                    type="button"
                    onClick={() => setManualStep(1)}
                    style={{
                      flex: 1,
                      padding: '0.75rem',
                      backgroundColor: '#6b7280',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      fontSize: '1rem',
                      cursor: 'pointer'
                    }}
                  >
                    ← Back
                  </button>
                  <button
                    type="button"
                    onClick={handleNextToStep3}
                    disabled={!meetName || !meetDate || selectedEvents.length === 0}
                    style={{
                      flex: 2,
                      padding: '0.75rem',
                      backgroundColor: (!meetName || !meetDate || selectedEvents.length === 0) ? '#9ca3af' : '#cc0000',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      fontSize: '1rem',
                      cursor: (!meetName || !meetDate || selectedEvents.length === 0) ? 'not-allowed' : 'pointer'
                    }}
                  >
                    Next: Enter Times ({selectedEvents.length} event{selectedEvents.length !== 1 ? 's' : ''} selected)
                  </button>
                </div>
              </div>
            )}

            {/* Step 3: Time Entry */}
            {manualStep === 3 && (
              <div>
                <h2 style={{ marginBottom: '1rem', color: '#333' }}>Enter Times</h2>
                <p style={{ marginBottom: '1rem', color: '#666', fontSize: '0.9rem' }}>
                  Meet: <strong>{meetName}</strong> | Date: <strong>{meetDate}</strong> | Course: <strong>{meetCourse}</strong>
                </p>

            <div style={{
                  border: '1px solid #ddd',
              borderRadius: '4px',
                  padding: '1rem',
                  maxHeight: '600px',
                  overflowY: 'auto'
                }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                    <thead>
                      <tr style={{ backgroundColor: '#e2e8f0', borderBottom: '2px solid #cbd5e1' }}>
                        <th style={{ padding: '0.75rem', textAlign: 'left' }}>Athlete</th>
                        <th style={{ padding: '0.75rem', textAlign: 'left' }}>Event</th>
                        <th style={{ padding: '0.75rem', textAlign: 'left' }}>Time (MM:SS.ss or SS.ss)</th>
                        <th style={{ padding: '0.75rem', textAlign: 'left' }}>Place</th>
                      </tr>
                    </thead>
                    <tbody>
                      {manualResults.map((result, idx) => (
                        <tr key={idx} style={{ borderBottom: '1px solid #e2e8f0' }}>
                          <td style={{ padding: '0.75rem' }}>{result.athlete_name}</td>
                          <td style={{ padding: '0.75rem' }}>
                            {result.event_gender} {result.event_distance}m {result.event_stroke}
                          </td>
                          <td style={{ padding: '0.75rem' }}>
                            <input
                              type="text"
                              value={result.time_string}
                              onChange={(e) => {
                                const newResults = [...manualResults];
                                newResults[idx].time_string = e.target.value;
                                setManualResults(newResults);
                              }}
                              placeholder="e.g., 1:23.45 or 23.45"
                              style={{
                                width: '100%',
                                padding: '0.5rem',
                                border: '1px solid #ddd',
                                borderRadius: '4px',
                                fontSize: '0.9rem'
                              }}
                              required
                            />
                          </td>
                          <td style={{ padding: '0.75rem' }}>
                            <input
                              type="number"
                              value={result.place || ''}
                              onChange={(e) => {
                                const newResults = [...manualResults];
                                newResults[idx].place = e.target.value ? parseInt(e.target.value) : null;
                                setManualResults(newResults);
                              }}
                              placeholder="Optional"
                              min="1"
                              style={{
                                width: '100%',
                                padding: '0.5rem',
                                border: '1px solid #ddd',
                                borderRadius: '4px',
                                fontSize: '0.9rem'
                              }}
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
            </div>

                <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
          <button
                    type="button"
                    onClick={() => setManualStep(2)}
            style={{
                      flex: 1,
                      padding: '0.75rem',
                      backgroundColor: '#6b7280',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontSize: '1rem',
                      cursor: 'pointer'
            }}
          >
                    ← Back
          </button>
                  <button
                    type="button"
                    onClick={handleSubmitManualResults}
                    disabled={uploading || manualResults.some(r => !r.time_string.trim())}
                    style={{
                      flex: 2,
                      padding: '0.75rem',
                      backgroundColor: (uploading || manualResults.some(r => !r.time_string.trim())) ? '#9ca3af' : '#059669',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      fontSize: '1rem',
                      cursor: (uploading || manualResults.some(r => !r.time_string.trim())) ? 'not-allowed' : 'pointer'
                    }}
                  >
                    {uploading ? 'Submitting...' : `Submit ${manualResults.length} Results`}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

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
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
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

        {/* Manage Existing Meets Tab */}
        {activeTab === 'manage' && (
        <div>
        <div style={{
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            marginBottom: '1.5rem'
          }}>
            <h2 style={{ margin: 0, color: '#1e293b' }}>
              Manage Existing Meets {loadingMeets && '(Loading...)'} {meets.length > 0 && `(${meets.length} meets)`}
            </h2>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                onClick={() => {
                  console.log('Manual refresh triggered');
                  console.log('Current state - loadingMeets:', loadingMeets, 'meets:', meets.length);
                  setLoadingMeets(false);
                  setTimeout(() => fetchMeets(), 100);
                }}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: '#cc0000',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '0.9rem'
                }}
              >
                Force Refresh
              </button>
            </div>
          </div>

          {error && error.includes('meets') && (
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

          {loadingMeets ? (
            <div>
              <p style={{ color: '#666', textAlign: 'center', padding: '2rem' }}>
                Loading meets...
              </p>
              <p style={{ color: '#999', textAlign: 'center', fontSize: '0.85rem' }}>
                If this takes too long, check the browser console (F12) for errors
              </p>
            </div>
          ) : meets.length === 0 && !error ? (
            <p style={{ color: '#666', textAlign: 'center', padding: '2rem' }}>
              No meets found in database.
            </p>
          ) : meets.length > 0 ? (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ 
                width: '100%', 
                borderCollapse: 'collapse',
                fontSize: '0.9rem'
              }}>
                <thead>
                  <tr style={{ 
                    backgroundColor: '#e2e8f0',
                    borderBottom: '2px solid #cbd5e1'
                  }}>
                    <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: '600' }}>Meet Name</th>
                    <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: '600' }}>Alias/Code</th>
                    <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: '600' }}>Date</th>
                    <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: '600' }}>City</th>
                    <th style={{ padding: '0.75rem', textAlign: 'center', fontWeight: '600' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {meets.map((meet) => (
                    <tr key={meet.id} style={{ 
                      borderBottom: '1px solid #e2e8f0',
                      backgroundColor: editingAlias[meet.id] !== undefined ? '#fef3c7' : 'white'
                    }}>
                      <td style={{ padding: '0.75rem' }}>
                        {meet.name || '(No name)'}
                      </td>
                      <td style={{ padding: '0.75rem' }}>
                        {editingAlias[meet.id] !== undefined ? (
                          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                            <input
                              type="text"
                              value={editingAlias[meet.id]}
                              onChange={(e) => setEditingAlias({ ...editingAlias, [meet.id]: e.target.value })}
                              style={{
                                padding: '0.5rem',
                                border: '1px solid #cbd5e1',
                                borderRadius: '4px',
                                fontSize: '0.9rem',
                                width: '120px'
                              }}
                              onKeyPress={(e) => {
                                if (e.key === 'Enter') {
                                  handleUpdateAlias(meet.id, editingAlias[meet.id]);
                                }
                              }}
                            />
                            <button
                              onClick={() => handleUpdateAlias(meet.id, editingAlias[meet.id])}
                              style={{
                                padding: '0.25rem 0.5rem',
                                backgroundColor: '#059669',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                fontSize: '0.8rem'
                              }}
                            >
                              ✓
                            </button>
                            <button
                              onClick={() => {
                                const newEditing = { ...editingAlias };
                                delete newEditing[meet.id];
                                setEditingAlias(newEditing);
                              }}
                              style={{
                                padding: '0.25rem 0.5rem',
                                backgroundColor: '#6b7280',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                fontSize: '0.8rem'
                              }}
                            >
                              ✕
                            </button>
                          </div>
                        ) : (
                          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                            <span style={{ 
                              fontWeight: meet.alias ? '500' : 'normal',
                              color: meet.alias ? '#1e293b' : '#9ca3af'
                            }}>
                              {meet.alias || '(No alias)'}
                            </span>
                            <button
                              onClick={() => setEditingAlias({ ...editingAlias, [meet.id]: meet.alias || '' })}
                              style={{
                                padding: '0.25rem 0.5rem',
                                backgroundColor: '#3b82f6',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                fontSize: '0.75rem'
                              }}
                              title="Edit alias"
                            >
                              Edit
                            </button>
                          </div>
                        )}
                      </td>
                      <td style={{ padding: '0.75rem', color: '#666' }}>
                        {meet.date ? new Date(meet.date).toLocaleDateString() : '-'}
                      </td>
                      <td style={{ padding: '0.75rem', color: '#666' }}>
                        {meet.city || '-'}
                      </td>
                      <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
                          <button
                            onClick={async () => {
                              try {
                                // Generate PDF and open in new window
                                const pdfUrl = `http://localhost:8000/api/admin/meets/${meet.id}/pdf`;
                                window.open(pdfUrl, '_blank');
                              } catch (error: any) {
                                alert(`Error generating PDF: ${error.message}`);
                              }
                            }}
                            style={{
                              padding: '0.5rem 1rem',
                              backgroundColor: '#059669',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              cursor: 'pointer',
                              fontSize: '0.85rem'
                            }}
                            title={`Generate PDF report for ${meet.name} (event by event with place, name, birthdate, time)`}
                          >
                            View PDF
                          </button>
                          <button
                            onClick={() => handleDeleteMeet(meet.id, meet.name)}
                            style={{
                              padding: '0.5rem 1rem',
                              backgroundColor: '#dc2626',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              cursor: 'pointer',
                              fontSize: '0.85rem'
                            }}
                            title={`Delete ${meet.name} and all its results`}
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </div>
        )}

        {/* Instructions - Condensed */}
        {activeTab === 'upload' && (
        <div style={{
          marginTop: '1rem',
          padding: '0.75rem',
          backgroundColor: '#f8fafc',
          border: '1px solid #e2e8f0',
          borderRadius: '4px',
          fontSize: '0.85rem'
        }}>
          <p style={{ margin: 0, color: '#000' }}>
            <strong>Note:</strong> Upload Excel files (.xlsx/.xls). Meet info is auto-extracted. Set aliases in "Manage Existing Meets" tab after upload.
          </p>
        </div>
        )}
      </div>
    </div>
  );
}
