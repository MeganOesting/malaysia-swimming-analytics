import React, { useState, useEffect } from 'react';
import Head from 'next/head';

interface Result {
  name: string;
  gender: string;
  age: number;
  distance: number;
  stroke: string;
  time: string;
  place: number;
  aqua_points: number;
  meet: string;
}

interface Stats {
  total_results: number;
  total_athletes: number;
  total_meets: number;
}

interface Meet {
  id: string;
  name: string;
}

interface Event {
  id: string;
  name: string;
}

export default function Home() {
  const [results, setResults] = useState<Result[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [meets, setMeets] = useState<Meet[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filter states
  const [selectedMeets, setSelectedMeets] = useState<string[]>([]);
  const [selectedGenders, setSelectedGenders] = useState<string[]>(['M']);
  const [selectedEvents, setSelectedEvents] = useState<string[]>(['50 Free']);
  const [selectedAgeGroups, setSelectedAgeGroups] = useState<string[]>(['OPEN']);
  const [stateFilter, setStateFilter] = useState<string>('');
  const [includeForeign, setIncludeForeign] = useState<boolean>(true);
  const [resultsMode, setResultsMode] = useState<string>('all');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch all data in parallel
      const [resultsResponse, statsResponse, meetsResponse, eventsResponse] = await Promise.all([
        fetch('http://localhost:8000/api/results/simple'),
        fetch('http://localhost:8000/api/results/stats'),
        fetch('http://localhost:8000/api/meets'),
        fetch('http://localhost:8000/api/events')
      ]);
      
      if (!resultsResponse.ok) throw new Error('Failed to fetch results');
      if (!statsResponse.ok) throw new Error('Failed to fetch stats');
      if (!meetsResponse.ok) throw new Error('Failed to fetch meets');
      if (!eventsResponse.ok) throw new Error('Failed to fetch events');
      
      const [resultsData, statsData, meetsData, eventsData] = await Promise.all([
        resultsResponse.json(),
        statsResponse.json(),
        meetsResponse.json(),
        eventsResponse.json()
      ]);
      
      setResults(resultsData.results);
      setStats(statsData);
      setMeets(meetsData.meets);
      setEvents(eventsData.events);
      
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>Malaysia Swimming Analytics</title>
        <meta name="description" content="Modern swimming analytics platform for Malaysian swimming competitions" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      
      <div style={{ fontFamily: 'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif', fontSize: '14px' }}>
        {/* Header with MAS logos */}
        <h1 style={{ textAlign: 'center', fontSize: '1.4rem' }}>
          <img src="/mas-logo.png" alt="MAS Logo" style={{ height: '1em', verticalAlign: 'middle', margin: '0 6px' }} />
          Welcome to the Malaysia Times Database
          <img src="/mas-logo.png" alt="MAS Logo" style={{ height: '1em', verticalAlign: 'middle', margin: '0 6px' }} />
            </h1>

        {/* Filters Section */}
        <div style={{ fontSize: '0.9em', margin: '6px 0 8px 0' }}>
          <form style={{ margin: 0 }}>
            {/* Meets */}
            <div style={{ margin: '2px 0' }}>
              <strong>Meets</strong>:
              {meets.map((meet) => (
                <label key={meet.id} style={{ marginRight: '10px', whiteSpace: 'nowrap' }}>
                  <input 
                    type="checkbox" 
                    name="meets" 
                    value={meet.id}
                    checked={selectedMeets.includes(meet.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedMeets([...selectedMeets, meet.id]);
                      } else {
                        setSelectedMeets(selectedMeets.filter(id => id !== meet.id));
                      }
                    }}
                    style={{ accentColor: '#cc0000', marginRight: '4px' }}
                  />
                  {meet.name}
                </label>
              ))}
                </div>
                
            {/* Gender */}
            <div style={{ margin: '2px 0' }}>
              <strong>Gender</strong>:
              <label style={{ marginRight: '10px', whiteSpace: 'nowrap' }}>
                <input 
                  type="checkbox" 
                  name="genders" 
                  value="M"
                  checked={selectedGenders.includes('M')}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedGenders([...selectedGenders, 'M']);
                    } else {
                      setSelectedGenders(selectedGenders.filter(g => g !== 'M'));
                    }
                  }}
                  style={{ accentColor: '#cc0000', marginRight: '4px' }}
                />
                Male
              </label>
              <label style={{ marginRight: '10px', whiteSpace: 'nowrap' }}>
                <input 
                  type="checkbox" 
                  name="genders" 
                  value="F"
                  checked={selectedGenders.includes('F')}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedGenders([...selectedGenders, 'F']);
                    } else {
                      setSelectedGenders(selectedGenders.filter(g => g !== 'F'));
                    }
                  }}
                  style={{ accentColor: '#cc0000', marginRight: '4px' }}
                />
                Female
              </label>
                </div>
                
            {/* State */}
            <div style={{ margin: '2px 0' }}>
              <strong>State</strong>:
              <select 
                name="state_code" 
                value={stateFilter}
                onChange={(e) => setStateFilter(e.target.value)}
                style={{ marginRight: '10px', whiteSpace: 'nowrap' }}
              >
                <option value="">All States</option>
                <option value="KUL">KUL</option>
                <option value="SEL">SEL</option>
                <option value="JHR">JHR</option>
                <option value="KED">KED</option>
                <option value="KEL">KEL</option>
                <option value="MEL">MEL</option>
                <option value="NSN">NSN</option>
                <option value="PHG">PHG</option>
                <option value="PRK">PRK</option>
                <option value="PER">PER</option>
                <option value="PEN">PEN</option>
                <option value="SBH">SBH</option>
                <option value="SWK">SWK</option>
                <option value="TRG">TRG</option>
              </select>
                </div>
                
            {/* Age Group */}
            <div style={{ margin: '2px 0' }}>
              <strong>Age Group</strong>:
              <label style={{ marginRight: '10px', whiteSpace: 'nowrap' }}>
                <input 
                  type="checkbox" 
                  name="age_groups" 
                  value="OPEN"
                  checked={selectedAgeGroups.includes('OPEN')}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedAgeGroups(['OPEN']);
                    } else {
                      setSelectedAgeGroups(selectedAgeGroups.filter(g => g !== 'OPEN'));
                    }
                  }}
                  style={{ accentColor: '#cc0000', marginRight: '4px' }}
                />
                Open
              </label>
              <label style={{ marginRight: '10px', whiteSpace: 'nowrap' }}>
                <input 
                  type="checkbox" 
                  name="age_groups" 
                  value="16-18"
                  checked={selectedAgeGroups.includes('16-18')}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedAgeGroups([...selectedAgeGroups.filter(g => g !== 'OPEN'), '16-18']);
                    } else {
                      setSelectedAgeGroups(selectedAgeGroups.filter(g => g !== '16-18'));
                    }
                  }}
                  style={{ accentColor: '#cc0000', marginRight: '4px' }}
                />
                16–18
              </label>
              <label style={{ marginRight: '10px', whiteSpace: 'nowrap' }}>
                <input 
                  type="checkbox" 
                  name="age_groups" 
                  value="14-15"
                  checked={selectedAgeGroups.includes('14-15')}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedAgeGroups([...selectedAgeGroups.filter(g => g !== 'OPEN'), '14-15']);
                    } else {
                      setSelectedAgeGroups(selectedAgeGroups.filter(g => g !== '14-15'));
                    }
                  }}
                  style={{ accentColor: '#cc0000', marginRight: '4px' }}
                />
                14–15
              </label>
              <label style={{ marginRight: '10px', whiteSpace: 'nowrap' }}>
                <input 
                  type="checkbox" 
                  name="age_groups" 
                  value="12-13"
                  checked={selectedAgeGroups.includes('12-13')}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedAgeGroups([...selectedAgeGroups.filter(g => g !== 'OPEN'), '12-13']);
                    } else {
                      setSelectedAgeGroups(selectedAgeGroups.filter(g => g !== '12-13'));
                    }
                  }}
                  style={{ accentColor: '#cc0000', marginRight: '4px' }}
                />
                12–13
              </label>
              <label style={{ marginRight: '10px', whiteSpace: 'nowrap' }}>
                <input 
                  type="checkbox" 
                  name="age_groups" 
                  value="13U"
                  checked={selectedAgeGroups.includes('13U')}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedAgeGroups([...selectedAgeGroups.filter(g => g !== 'OPEN'), '13U']);
                    } else {
                      setSelectedAgeGroups(selectedAgeGroups.filter(g => g !== '13U'));
                    }
                  }}
                  style={{ accentColor: '#cc0000', marginRight: '4px' }}
                />
                13 & Under
              </label>
              </div>
              
            {/* Events - 6x3 Grid */}
            <div style={{ margin: '2px 0' }}>
              <strong>Events</strong>:
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(6, max-content)', 
                gap: '1px 12px', 
                marginTop: '0', 
                alignItems: 'center' 
              }}>
                {/* Row 1: Free */}
                <label style={{ margin: 0, lineHeight: '1.0' }}>
                  <input 
                    type="checkbox" 
                    name="events" 
                    value="50 Free"
                    checked={selectedEvents.includes('50 Free')}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedEvents([...selectedEvents, '50 Free']);
                      } else {
                        setSelectedEvents(selectedEvents.filter(ev => ev !== '50 Free'));
                      }
                    }}
                    style={{ accentColor: '#cc0000', verticalAlign: 'middle', marginRight: '4px' }}
                  />
                  50 Free
                </label>
                <label style={{ margin: 0, lineHeight: '1.0' }}>
                  <input 
                    type="checkbox" 
                    name="events" 
                    value="100 Free"
                    checked={selectedEvents.includes('100 Free')}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedEvents([...selectedEvents, '100 Free']);
                      } else {
                        setSelectedEvents(selectedEvents.filter(ev => ev !== '100 Free'));
                      }
                    }}
                    style={{ accentColor: '#cc0000', verticalAlign: 'middle', marginRight: '4px' }}
                  />
                  100 Free
                </label>
                <label style={{ margin: 0, lineHeight: '1.0' }}>
                  <input 
                    type="checkbox" 
                    name="events" 
                    value="200 Free"
                    checked={selectedEvents.includes('200 Free')}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedEvents([...selectedEvents, '200 Free']);
                      } else {
                        setSelectedEvents(selectedEvents.filter(ev => ev !== '200 Free'));
                      }
                    }}
                    style={{ accentColor: '#cc0000', verticalAlign: 'middle', marginRight: '4px' }}
                  />
                  200 Free
                </label>
                <label style={{ margin: 0, lineHeight: '1.0' }}>
                  <input 
                    type="checkbox" 
                    name="events" 
                    value="400 Free"
                    checked={selectedEvents.includes('400 Free')}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedEvents([...selectedEvents, '400 Free']);
                      } else {
                        setSelectedEvents(selectedEvents.filter(ev => ev !== '400 Free'));
                      }
                    }}
                    style={{ accentColor: '#cc0000', verticalAlign: 'middle', marginRight: '4px' }}
                  />
                  400 Free
                </label>
                <label style={{ margin: 0, lineHeight: '1.0' }}>
                  <input 
                    type="checkbox" 
                    name="events" 
                    value="800 Free"
                    checked={selectedEvents.includes('800 Free')}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedEvents([...selectedEvents, '800 Free']);
                      } else {
                        setSelectedEvents(selectedEvents.filter(ev => ev !== '800 Free'));
                      }
                    }}
                    style={{ accentColor: '#cc0000', verticalAlign: 'middle', marginRight: '4px' }}
                  />
                  800 Free
                </label>
                <label style={{ margin: 0, lineHeight: '1.0' }}>
                  <input 
                    type="checkbox" 
                    name="events" 
                    value="1500 Free"
                    checked={selectedEvents.includes('1500 Free')}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedEvents([...selectedEvents, '1500 Free']);
                      } else {
                        setSelectedEvents(selectedEvents.filter(ev => ev !== '1500 Free'));
                      }
                    }}
                    style={{ accentColor: '#cc0000', verticalAlign: 'middle', marginRight: '4px' }}
                  />
                  1500 Free
                </label>

                {/* Row 2: Back & Breast */}
                <label style={{ margin: 0, lineHeight: '1.0' }}>
                  <input 
                    type="checkbox" 
                    name="events" 
                    value="50 Back"
                    checked={selectedEvents.includes('50 Back')}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedEvents([...selectedEvents, '50 Back']);
                      } else {
                        setSelectedEvents(selectedEvents.filter(ev => ev !== '50 Back'));
                      }
                    }}
                    style={{ accentColor: '#cc0000', verticalAlign: 'middle', marginRight: '4px' }}
                  />
                  50 Back
                </label>
                <label style={{ margin: 0, lineHeight: '1.0' }}>
                  <input 
                    type="checkbox" 
                    name="events" 
                    value="100 Back"
                    checked={selectedEvents.includes('100 Back')}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedEvents([...selectedEvents, '100 Back']);
                      } else {
                        setSelectedEvents(selectedEvents.filter(ev => ev !== '100 Back'));
                      }
                    }}
                    style={{ accentColor: '#cc0000', verticalAlign: 'middle', marginRight: '4px' }}
                  />
                  100 Back
                </label>
                <label style={{ margin: 0, lineHeight: '1.0' }}>
                  <input 
                    type="checkbox" 
                    name="events" 
                    value="200 Back"
                    checked={selectedEvents.includes('200 Back')}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedEvents([...selectedEvents, '200 Back']);
                      } else {
                        setSelectedEvents(selectedEvents.filter(ev => ev !== '200 Back'));
                      }
                    }}
                    style={{ accentColor: '#cc0000', verticalAlign: 'middle', marginRight: '4px' }}
                  />
                  200 Back
                </label>
                <label style={{ margin: 0, lineHeight: '1.0' }}>
                  <input 
                    type="checkbox" 
                    name="events" 
                    value="50 Breast"
                    checked={selectedEvents.includes('50 Breast')}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedEvents([...selectedEvents, '50 Breast']);
                      } else {
                        setSelectedEvents(selectedEvents.filter(ev => ev !== '50 Breast'));
                      }
                    }}
                    style={{ accentColor: '#cc0000', verticalAlign: 'middle', marginRight: '4px' }}
                  />
                  50 Breast
                </label>
                <label style={{ margin: 0, lineHeight: '1.0' }}>
                  <input 
                    type="checkbox" 
                    name="events" 
                    value="100 Breast"
                    checked={selectedEvents.includes('100 Breast')}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedEvents([...selectedEvents, '100 Breast']);
                      } else {
                        setSelectedEvents(selectedEvents.filter(ev => ev !== '100 Breast'));
                      }
                    }}
                    style={{ accentColor: '#cc0000', verticalAlign: 'middle', marginRight: '4px' }}
                  />
                  100 Breast
                </label>
                <label style={{ margin: 0, lineHeight: '1.0' }}>
                  <input 
                    type="checkbox" 
                    name="events" 
                    value="200 Breast"
                    checked={selectedEvents.includes('200 Breast')}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedEvents([...selectedEvents, '200 Breast']);
                      } else {
                        setSelectedEvents(selectedEvents.filter(ev => ev !== '200 Breast'));
                      }
                    }}
                    style={{ accentColor: '#cc0000', verticalAlign: 'middle', marginRight: '4px' }}
                  />
                  200 Breast
                </label>

                {/* Row 3: Fly & IM */}
                <label style={{ margin: 0, lineHeight: '1.0' }}>
                  <input 
                    type="checkbox" 
                    name="events" 
                    value="50 Fly"
                    checked={selectedEvents.includes('50 Fly')}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedEvents([...selectedEvents, '50 Fly']);
                      } else {
                        setSelectedEvents(selectedEvents.filter(ev => ev !== '50 Fly'));
                      }
                    }}
                    style={{ accentColor: '#cc0000', verticalAlign: 'middle', marginRight: '4px' }}
                  />
                  50 Fly
                </label>
                <label style={{ margin: 0, lineHeight: '1.0' }}>
                  <input 
                    type="checkbox" 
                    name="events" 
                    value="100 Fly"
                    checked={selectedEvents.includes('100 Fly')}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedEvents([...selectedEvents, '100 Fly']);
                      } else {
                        setSelectedEvents(selectedEvents.filter(ev => ev !== '100 Fly'));
                      }
                    }}
                    style={{ accentColor: '#cc0000', verticalAlign: 'middle', marginRight: '4px' }}
                  />
                  100 Fly
                </label>
                <label style={{ margin: 0, lineHeight: '1.0' }}>
                  <input 
                    type="checkbox" 
                    name="events" 
                    value="200 Fly"
                    checked={selectedEvents.includes('200 Fly')}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedEvents([...selectedEvents, '200 Fly']);
                      } else {
                        setSelectedEvents(selectedEvents.filter(ev => ev !== '200 Fly'));
                      }
                    }}
                    style={{ accentColor: '#cc0000', verticalAlign: 'middle', marginRight: '4px' }}
                  />
                  200 Fly
                </label>
                <label style={{ margin: 0, lineHeight: '1.0' }}>
                  <input 
                    type="checkbox" 
                    name="events" 
                    value="200 IM"
                    checked={selectedEvents.includes('200 IM')}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedEvents([...selectedEvents, '200 IM']);
                      } else {
                        setSelectedEvents(selectedEvents.filter(ev => ev !== '200 IM'));
                      }
                    }}
                    style={{ accentColor: '#cc0000', verticalAlign: 'middle', marginRight: '4px' }}
                  />
                  200 IM
                </label>
                <label style={{ margin: 0, lineHeight: '1.0' }}>
                  <input 
                    type="checkbox" 
                    name="events" 
                    value="400 IM"
                    checked={selectedEvents.includes('400 IM')}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedEvents([...selectedEvents, '400 IM']);
                      } else {
                        setSelectedEvents(selectedEvents.filter(ev => ev !== '400 IM'));
                      }
                    }}
                    style={{ accentColor: '#cc0000', verticalAlign: 'middle', marginRight: '4px' }}
                  />
                  400 IM
                </label>
              </div>
            </div>

            {/* Include Foreign */}
            <div style={{ margin: '2px 0' }}>
              <label style={{ marginRight: '10px', whiteSpace: 'nowrap' }}>
                <input 
                  type="checkbox" 
                  name="include_foreign" 
                  value="1"
                  checked={includeForeign}
                  onChange={(e) => setIncludeForeign(e.target.checked)}
                  style={{ accentColor: '#cc0000', marginRight: '4px' }}
                />
                Include Non-Malaysian Swimmers
              </label>
            </div>

            {/* Results Mode */}
            <div style={{ margin: '2px 0' }}>
              <strong>Results</strong>:
              <label style={{ marginRight: '10px', whiteSpace: 'nowrap' }}>
                <input 
                  type="radio" 
                  name="results_mode" 
                  value="all"
                  checked={resultsMode === 'all'}
                  onChange={(e) => setResultsMode(e.target.value)}
                  style={{ accentColor: '#cc0000', marginRight: '4px' }}
                />
                Show all times
              </label>
              <label style={{ marginRight: '10px', whiteSpace: 'nowrap' }}>
                <input 
                  type="radio" 
                  name="results_mode" 
                  value="best"
                  checked={resultsMode === 'best'}
                  onChange={(e) => setResultsMode(e.target.value)}
                  style={{ accentColor: '#cc0000', marginRight: '4px' }}
                />
                Show best times only
              </label>
            </div>

            {/* Buttons */}
            <div style={{ margin: '2px 0' }}>
              <button 
                type="submit" 
                style={{ 
                  fontSize: '0.9em', 
                  padding: '2px 10px', 
                  backgroundColor: '#cc0000', 
                  color: 'white', 
                  border: 'none', 
                  borderRadius: '4px',
                  marginRight: '8px'
                }}
              >
                Apply Selection
              </button>
              <button 
                type="button" 
                style={{ 
                  fontSize: '0.9em', 
                  padding: '2px 10px', 
                  backgroundColor: '#cc0000', 
                  color: 'white', 
                  border: 'none', 
                  borderRadius: '4px',
                  marginRight: '8px'
                }}
              >
                Download XLSX
              </button>
              <button 
                type="button" 
                style={{ 
                  fontSize: '0.9em', 
                  padding: '2px 10px', 
                  backgroundColor: '#cc0000', 
                  color: 'white', 
                  border: 'none', 
                  borderRadius: '4px'
                }}
                onClick={() => {
                  setSelectedMeets([]);
                  setSelectedGenders(['M']);
                  setSelectedEvents(['50 Free']);
                  setSelectedAgeGroups(['OPEN']);
                  setStateFilter('');
                  setIncludeForeign(true);
                  setResultsMode('all');
                }}
              >
                Reset Filters
              </button>
            </div>
          </form>
        </div>

        {/* Results Table */}
        <table style={{ borderCollapse: 'collapse', width: '100%', marginTop: '12px', tableLayout: 'fixed', fontSize: '0.9em' }}>
          <thead>
            <tr>
              <th style={{ border: '1px solid #ccc', padding: '4px 6px', textAlign: 'center', background: '#f5f5f5', width: '6ch', maxWidth: '6ch', whiteSpace: 'normal', wordWrap: 'break-word' }}>Gender</th>
              <th style={{ border: '1px solid #ccc', padding: '4px 6px', textAlign: 'center', background: '#f5f5f5', width: '10ch', maxWidth: '10ch', whiteSpace: 'normal', wordWrap: 'break-word' }}>Event</th>
              <th style={{ border: '1px solid #ccc', padding: '4px 6px', textAlign: 'center', background: '#f5f5f5', width: '20ch', maxWidth: '20ch', whiteSpace: 'normal', wordWrap: 'break-word' }}>Name</th>
              <th style={{ border: '1px solid #ccc', padding: '4px 6px', textAlign: 'center', background: '#f5f5f5', width: '6ch', maxWidth: '6ch', whiteSpace: 'normal', wordWrap: 'break-word' }}>Team</th>
              <th style={{ border: '1px solid #ccc', padding: '4px 6px', textAlign: 'center', background: '#f5f5f5', width: '3ch', maxWidth: '3ch', whiteSpace: 'normal', wordWrap: 'break-word' }}>Age</th>
              <th style={{ border: '1px solid #ccc', padding: '4px 6px', textAlign: 'center', background: '#f5f5f5', width: '6ch', maxWidth: '6ch', whiteSpace: 'normal', wordWrap: 'break-word' }}>Meet</th>
              <th style={{ border: '1px solid #ccc', padding: '4px 6px', textAlign: 'center', background: '#f5f5f5', width: '7ch', maxWidth: '7ch', whiteSpace: 'normal', wordWrap: 'break-word' }}>Time</th>
              <th style={{ border: '1px solid #ccc', padding: '4px 6px', textAlign: 'center', background: '#f5f5f5', width: '6ch', maxWidth: '6ch', whiteSpace: 'normal', wordWrap: 'break-word' }}>AQUA</th>
              <th style={{ border: '1px solid #ccc', padding: '4px 6px', textAlign: 'center', background: '#f5f5f5', width: '4ch', maxWidth: '4ch', whiteSpace: 'normal', wordWrap: 'break-word' }}>Place</th>
              <th style={{ border: '1px solid #ccc', padding: '4px 6px', textAlign: 'center', background: '#f5f5f5', width: '6.5ch', maxWidth: '6.5ch', whiteSpace: 'normal', wordWrap: 'break-word' }}>On Track Target Time</th>
              <th style={{ border: '1px solid #ccc', padding: '4px 6px', textAlign: 'center', background: '#f5f5f5', width: '8ch', maxWidth: '8ch', whiteSpace: 'normal', wordWrap: 'break-word' }}>On Track AQUA</th>
              <th style={{ border: '1px solid #ccc', padding: '4px 6px', textAlign: 'center', background: '#f5f5f5', width: '7ch', maxWidth: '7ch', whiteSpace: 'normal', wordWrap: 'break-word' }}>Track Gap</th>
              <th style={{ border: '1px solid #ccc', padding: '4px 6px', textAlign: 'center', background: '#f5f5f5', width: '6ch', maxWidth: '6ch', whiteSpace: 'normal', wordWrap: 'break-word' }}>Age Points</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={13} style={{ border: '1px solid #ccc', padding: '4px 6px', textAlign: 'center' }}>
                  Loading results...
                </td>
              </tr>
            ) : error ? (
              <tr>
                <td colSpan={13} style={{ border: '1px solid #ccc', padding: '4px 6px', textAlign: 'center', color: '#cc0000' }}>
                  Error loading data: {error}
                </td>
              </tr>
            ) : results.length === 0 ? (
              <tr>
                <td colSpan={13} style={{ border: '1px solid #ccc', padding: '4px 6px', textAlign: 'center' }}>
                  No data yet.
                </td>
              </tr>
            ) : (
              results.map((result, index) => (
                <tr key={index}>
                  <td style={{ border: '1px solid #ccc', padding: '4px 6px', textAlign: 'center' }}>{result.gender}</td>
                  <td style={{ border: '1px solid #ccc', padding: '4px 6px', textAlign: 'center' }}>{result.distance}m {result.stroke}</td>
                  <td style={{ border: '1px solid #ccc', padding: '4px 6px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={result.name}>{result.name}</td>
                  <td style={{ border: '1px solid #ccc', padding: '4px 6px', textAlign: 'center' }}>-</td>
                  <td style={{ border: '1px solid #ccc', padding: '4px 6px', textAlign: 'center' }}>{result.age}</td>
                  <td style={{ border: '1px solid #ccc', padding: '4px 6px', textAlign: 'center' }}>{result.meet}</td>
                  <td style={{ border: '1px solid #ccc', padding: '4px 6px', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{result.time}</td>
                  <td style={{ border: '1px solid #ccc', padding: '4px 6px', textAlign: 'center' }}>{result.aqua_points}</td>
                  <td style={{ border: '1px solid #ccc', padding: '4px 6px', textAlign: 'center' }}>{result.place}</td>
                  <td style={{ border: '1px solid #ccc', padding: '4px 6px', textAlign: 'right' }}>-</td>
                  <td style={{ border: '1px solid #ccc', padding: '4px 6px', textAlign: 'center' }}>-</td>
                  <td style={{ border: '1px solid #ccc', padding: '4px 6px', textAlign: 'center' }}>-</td>
                  <td style={{ border: '1px solid #ccc', padding: '4px 6px', textAlign: 'center' }}>-</td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        {/* Sidebar */}
        <div style={{ position: 'absolute', right: '12px', top: '96px', width: '220px', zIndex: 1 }}>
          <div style={{ border: '1px solid #ddd', borderRadius: '10px', padding: '10px', background: '#fafafa', boxShadow: '0 6px 16px rgba(0,0,0,0.15)' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '8px' }}>
              <a href="/map" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '28px', padding: '4px 10px', borderRadius: '8px', background: '#cc0000', color: '#fff', textDecoration: 'none' }}>
                <span style={{ fontWeight: '800', letterSpacing: '0.3px', fontSize: '0.9rem', color: '#fff', lineHeight: '1.05' }}>MAP</span>
                <span style={{ color: '#fff', fontSize: '0.68rem', lineHeight: '1.05', textAlign: 'center', whiteSpace: 'nowrap' }}>Malaysia Age Points</span>
              </a>
              <a href="/mot" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '28px', padding: '4px 10px', borderRadius: '8px', background: '#cc0000', color: '#fff', textDecoration: 'none' }}>
                <span style={{ fontWeight: '800', letterSpacing: '0.3px', fontSize: '0.9rem', color: '#fff', lineHeight: '1.05' }}>MOT</span>
                <span style={{ color: '#fff', fontSize: '0.68rem', lineHeight: '1.05', textAlign: 'center', whiteSpace: 'nowrap' }}>Malaysia On Track Tables</span>
              </a>
              <a href="/ltad" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '28px', padding: '4px 10px', borderRadius: '8px', background: '#cc0000', color: '#fff', textDecoration: 'none' }}>
                <span style={{ fontWeight: '800', letterSpacing: '0.3px', fontSize: '0.9rem', color: '#fff', lineHeight: '1.05' }}>LTAD</span>
                <span style={{ color: '#fff', fontSize: '0.68rem', lineHeight: '1.05', textAlign: 'center', whiteSpace: 'nowrap' }}>Long Term Athletic Development</span>
              </a>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}


