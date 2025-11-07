import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';

interface Result {
  name: string;
  gender: string;
  age: number;
  distance: number;
  stroke: string;
  time: string;
  place: number;
  aqua_points: number;
  meet_id?: string;
  meet: string;
  meet_code: string;
}

interface Stats {
  total_results: number;
  total_athletes: number;
  total_meets: number;
}

interface Meet {
  id: string;
  name: string;
  meet_code?: string;
  state_meet_ids?: string[];
}

interface Event {
  id: string;
  name: string;
}

export default function Home() {
  const router = useRouter();
  
  const [results, setResults] = useState<Result[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [meets, setMeets] = useState<Meet[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filter states
  const [selectedMeets, setSelectedMeets] = useState<string[]>([]);
  const [selectedGenders, setSelectedGenders] = useState<string[]>([]);
  const [selectedEvents, setSelectedEvents] = useState<string[]>([]);
  const [selectedAgeGroups, setSelectedAgeGroups] = useState<string[]>(['OPEN']);
  const [stateFilter, setStateFilter] = useState<string>('');
  const [includeForeign, setIncludeForeign] = useState<boolean>(true);
  const [resultsMode, setResultsMode] = useState<string>('all');
  const [mounted, setMounted] = useState(false);
  
  // Applied filters (what's actually being used for filtering)
  const [appliedMeets, setAppliedMeets] = useState<string[]>([]);
  const [appliedGenders, setAppliedGenders] = useState<string[]>([]);
  const [appliedEvents, setAppliedEvents] = useState<string[]>([]);

  // Fix hydration issue
  useEffect(() => {
    setMounted(true);
  }, []);

  // Scroll to top on page load/refresh
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch all data in parallel with cache-busting
      const timestamp = Date.now();
      const fetchOptions = {
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      };
      
      const [resultsResponse, statsResponse, meetsResponse, eventsResponse] = await Promise.all([
        fetch(`http://localhost:8000/api/results/simple?t=${timestamp}`, fetchOptions),
        fetch(`http://localhost:8000/api/results/stats?t=${timestamp}`, fetchOptions),
        fetch(`http://localhost:8000/api/meets?t=${timestamp}`, fetchOptions),
        fetch(`http://localhost:8000/api/events?t=${timestamp}`, fetchOptions)
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
      
      console.log('Fetched data:', { resultsData, statsData, meetsData, eventsData });
      console.log('Sample result:', resultsData.results[0]);
      console.log('Total results:', resultsData.results.length);
      console.log('Meets received:', meetsData.meets);
      console.log('Meets count:', meetsData.meets?.length || 0);
      setResults(resultsData.results || []);
      setStats(statsData);
      setMeets(meetsData.meets || []);
      setEvents(eventsData.events || []);
      console.log('Meets state set to:', meetsData.meets || []);
      
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const fetchFilteredData = async () => {
    try {
      setLoading(true);
      
      // Build query params from selected filters
      const params = new URLSearchParams();
      
      if (selectedMeets.length > 0) {
        params.append('meet_ids', selectedMeets.join(','));
      }
      if (selectedGenders.length > 0) {
        params.append('genders', selectedGenders.join(','));
      }
      if (selectedEvents.length > 0 && !selectedEvents.includes('ALL_EVENTS')) {
        params.append('events', selectedEvents.join(','));
      }
      if (selectedAgeGroups.length > 0 && !selectedAgeGroups.includes('OPEN')) {
        params.append('age_groups', selectedAgeGroups.join(','));
      }
      if (!includeForeign) {
        params.append('include_foreign', 'false');
      }
      
      const timestamp = Date.now();
      const fetchOptions = {
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      };
      
      const response = await fetch(`http://localhost:8000/api/results/filtered?${params.toString()}&t=${timestamp}`, fetchOptions);
      
      if (!response.ok) throw new Error('Failed to fetch filtered results');
      
      const data = await response.json();
      
      console.log('Fetched filtered data:', data);
      console.log('Filtered results count:', data.results?.length || 0);
      setResults(data.results || []);
      setAppliedMeets(selectedMeets);
      setAppliedGenders(selectedGenders);
      setAppliedEvents(selectedEvents);
      
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  // Auto-apply filters when meet + gender + event are ALL selected
  useEffect(() => {
    console.log('Auto-loading check:', {
      selectedMeets: selectedMeets,
      selectedGenders: selectedGenders, 
      selectedEvents: selectedEvents,
      shouldAutoLoad: selectedMeets.length > 0 && selectedGenders.length > 0 && selectedEvents.length > 0
    });
    
    // Auto-apply if meet(s) AND gender(s) AND event(s) are ALL selected
    if (selectedMeets.length > 0 && selectedGenders.length > 0 && selectedEvents.length > 0) {
      console.log('Auto-loading triggered with:', {
        appliedMeets: selectedMeets,
        appliedGenders: selectedGenders,
        appliedEvents: selectedEvents
      });
      console.log('Actual values:', {
        meet: selectedMeets[0],
        gender: selectedGenders[0],
        event: selectedEvents[0]
      });
      
      // Debug STATE25 meets
      if (selectedMeets.includes('STATE25')) {
        const stateMeetGroup = meets.find(m => m.id === "STATE25");
        const stateMeetIds = stateMeetGroup && (stateMeetGroup as any).state_meet_ids ? (stateMeetGroup as any).state_meet_ids : [];
        
        // Get all state meet results
        const allStateResults = results.filter(r => stateMeetIds.includes(r.meet_id));
        // Check what gender values actually exist in state results
        const genderValues = Array.from(new Set(allStateResults.map(r => r.gender)));
        const stateMaleResults = allStateResults.filter(r => r.gender === 'M' || r.gender === 'Male' || r.gender === 'MALE');
        const state50FreeResults = allStateResults.filter(r => r.distance === 50 && r.stroke === 'FR');
        const state50FreeMaleResults = allStateResults.filter(r => (r.gender === 'M' || r.gender === 'Male' || r.gender === 'MALE') && r.distance === 50 && r.stroke === 'FR');
        
        console.log('🔍 STATE25 debug:', {
          totalStateResults: allStateResults.length,
          uniqueGenderValues: genderValues,
          stateMaleResults: stateMaleResults.length,
          state50FreeResults: state50FreeResults.length,
          state50FreeMaleResults: state50FreeMaleResults.length,
          stateMeetIds: stateMeetIds,
          sampleStateResult: allStateResults[0],
          sampleStateMaleResult: stateMaleResults[0],
          sampleState50FreeResult: state50FreeResults[0],
          sampleState50FreeMaleResult: state50FreeMaleResults[0],
          appliedGender: selectedGenders[0],
          appliedEvent: selectedEvents[0]
        });
      }
      
      setAppliedMeets(selectedMeets);
      setAppliedGenders(selectedGenders);
      setAppliedEvents(selectedEvents);
      
      // Debug: Check filtered results count after a brief delay
      setTimeout(() => {
        const filtered = results.filter((result) => {
          // Gender filter
          if (selectedGenders.length > 0 && !selectedGenders.includes(result.gender)) {
            return false;
          }
          
          // Meet filter - simplified check
          if (selectedMeets.length > 0) {
            const isStateSelected = selectedMeets.includes("STATE25");
            if (isStateSelected) {
              const stateMeetGroup = meets.find(m => m.id === "STATE25");
              const stateMeetIds = stateMeetGroup && (stateMeetGroup as any).state_meet_ids ? (stateMeetGroup as any).state_meet_ids : [];
              if (!stateMeetIds.includes(result.meet_id)) {
                return false;
              }
            } else {
              if (!result.meet_id || !selectedMeets.includes(result.meet_id)) {
                return false;
              }
            }
          }
          
          // Event filter
          if (selectedEvents.length > 0) {
            const strokeMap: { [key: string]: { full: string; abbr: string } } = {
              "FR": { full: "Free", abbr: "FR" },
              "BK": { full: "Back", abbr: "BK" },
              "BR": { full: "Breast", abbr: "BR" },
              "BU": { full: "Fly", abbr: "BU" },
              "ME": { full: "IM", abbr: "ME" },
            };
            const strokeInfo = strokeMap[result.stroke] || { full: result.stroke, abbr: result.stroke };
            const eventStringFull = `${result.distance}m ${strokeInfo.full}`;
            const eventStringAbbr = `${result.distance}m ${strokeInfo.abbr}`;
            const eventStringShort = `${result.distance} ${strokeInfo.full}`;
            const eventStringShortAbbr = `${result.distance} ${strokeInfo.abbr}`;
            
            if (!selectedEvents.includes(eventStringFull) &&
                !selectedEvents.includes(eventStringAbbr) &&
                !selectedEvents.includes(eventStringShort) &&
                !selectedEvents.includes(eventStringShortAbbr)) {
              return false;
            }
          }
          
          return true;
        });
        console.log(`Filtered results count: ${filtered.length}`);
        console.log('Sample filtered result:', filtered[0]);
      }, 100);
    }
    // Clear applied filters if conditions not met
    else {
      console.log('Clearing applied filters');
      setAppliedMeets([]);
      setAppliedGenders([]);
      setAppliedEvents([]);
    }
  }, [selectedMeets, selectedGenders, selectedEvents, results, meets]);

  // All available events (must match the checkbox values)
  const allEventValues = [
    '50m FR', '100 Free', '200 Free', '400 Free', '800 Free', '1500 Free',
    '50 Back', '100 Back', '200 Back',
    '50 Breast', '100 Breast', '200 Breast',
    '50 Fly', '100 Fly', '200 Fly',
    '200 IM', '400 IM'
  ];

  // Helper function to handle event checkbox changes
  const handleEventChange = (eventValue: string, checked: boolean) => {
    if (eventValue === 'ALL_EVENTS') {
      if (checked) {
        // Check all individual events
        setSelectedEvents(['ALL_EVENTS', ...allEventValues]);
      } else {
        // Uncheck all events
        setSelectedEvents([]);
      }
    } else {
      // Individual event
      let newEvents = checked 
        ? selectedEvents.filter(ev => ev !== 'ALL_EVENTS').concat([eventValue])
        : selectedEvents.filter(ev => ev !== eventValue);
      
      // If all events are now selected (except ALL_EVENTS), also check "All Events"
      const selectedIndividualEvents = newEvents.filter(ev => ev !== 'ALL_EVENTS');
      if (selectedIndividualEvents.length === allEventValues.length) {
        newEvents = ['ALL_EVENTS', ...newEvents];
      }
      
      setSelectedEvents(newEvents);
    }
  };

  // Filter results based on applied selections
  
  const filteredResults = results.filter(result => {
    // If no filters are applied, show no results
    if (appliedGenders.length === 0 && appliedMeets.length === 0 && appliedEvents.length === 0) {
      return false;
    }
    
    // Gender filter - only apply if genders are selected
    if (appliedGenders.length > 0) {
      // Normalize gender values for comparison
      const resultGender = result.gender?.toUpperCase() || '';
      const normalizedAppliedGenders = appliedGenders.map(g => g.toUpperCase());
      // Check both exact match and common variations
      const genderMatches = normalizedAppliedGenders.includes(resultGender) ||
                           (resultGender === 'M' && normalizedAppliedGenders.includes('MALE')) ||
                           (resultGender === 'MALE' && normalizedAppliedGenders.includes('M')) ||
                           (resultGender === 'F' && normalizedAppliedGenders.includes('FEMALE')) ||
                           (resultGender === 'FEMALE' && normalizedAppliedGenders.includes('F'));
      if (!genderMatches) {
        return false;
      }
    }
    
    // Meet filter
    if (appliedMeets.length > 0) {
      // Check if STATE25 is selected (state meets group)
      const isStateSelected = appliedMeets.includes("STATE25");
      
      // State meet patterns to identify state meets (exclude national meets)
      // Get the state meet IDs from the meets array if STATE25 is selected
      const stateMeetGroup = meets.find(m => m.id === "STATE25");
      const stateMeetIds = stateMeetGroup && (stateMeetGroup as any).state_meet_ids ? (stateMeetGroup as any).state_meet_ids : [];
      
      
      // Check if this result is from a state meet by checking meet_id
      const isStateMeet = stateMeetIds.length > 0 && result.meet_id && stateMeetIds.includes(result.meet_id);
      
      // If STATE25 is selected
      if (isStateSelected) {
        // Must be a state meet to pass
        if (!isStateMeet) {
          return false;
        }
        // If it's a state meet, continue to other filters (don't return false)
      } else {
        // STATE25 not selected - check if this result's meet_id matches any selected meet IDs
        if (result.meet_id && !appliedMeets.includes(result.meet_id)) {
          return false;
        } else if (!result.meet_id) {
          // Fallback: match by meet code or name if no meet_id
          const resultMeetCode = result.meet_code || "";
          const resultMeetName = result.meet || "";
          
          // Check if any selected meet matches this result
          const matches = meets.some(meet => {
            if (appliedMeets.includes(meet.id)) {
              return meet.meet_code === resultMeetCode || meet.name === resultMeetName;
            }
            return false;
          });
          
          if (!matches) {
            return false;
          }
        }
      }
    }
    
    // Event filter - only apply if events are selected
    if (appliedEvents.length > 0) {
      // Check if "All Events" is selected - if so, skip event filtering
      if (appliedEvents.includes('ALL_EVENTS')) {
        // Allow all events through - don't filter by event
      } else {
        // Map stroke abbreviations to full names and abbreviations
        const strokeMap: { [key: string]: { full: string; abbr: string } } = {
          "FR": { full: "Free", abbr: "FR" },
          "BK": { full: "Back", abbr: "BK" }, 
          "BR": { full: "Breast", abbr: "BR" },
          "BU": { full: "Fly", abbr: "BU" },
          "ME": { full: "IM", abbr: "ME" },
          "IM": { full: "IM", abbr: "IM" },
        };
        const strokeInfo = strokeMap[result.stroke] || { full: result.stroke, abbr: result.stroke };
        
        // Check both formats: "50m Free" and "50m FR"
        const eventStringFull = `${result.distance}m ${strokeInfo.full}`;
        const eventStringAbbr = `${result.distance}m ${strokeInfo.abbr}`;
        
        // Also check formats like "50 Free" (without 'm')
        const eventStringShort = `${result.distance} ${strokeInfo.full}`;
        const eventStringShortAbbr = `${result.distance} ${strokeInfo.abbr}`;
        
        // Debug for event matching
        const eventMatches = appliedEvents.includes(eventStringFull) || 
                            appliedEvents.includes(eventStringAbbr) ||
                            appliedEvents.includes(eventStringShort) ||
                            appliedEvents.includes(eventStringShortAbbr);
        
        if (!eventMatches) {
          return false;
        }
      }
    }
    
    return true;
  });
  
  // Debug: Log filtered results count - run immediately when STATE25 is selected
  useEffect(() => {
    if (appliedMeets.length > 0 && appliedMeets.includes('STATE25') && appliedGenders.length > 0 && appliedEvents.length > 0) {
      const stateMeetGroup = meets.find(m => m.id === "STATE25");
      const stateMeetIds = stateMeetGroup && (stateMeetGroup as any).state_meet_ids ? (stateMeetGroup as any).state_meet_ids : [];
      
      const stateResults = results.filter(r => 
        stateMeetIds.includes(r.meet_id) && 
        appliedGenders.includes(r.gender) && 
        r.distance === 50 && 
        r.stroke === 'FR'
      );
      
      console.log('🔍 === STATE25 FILTERING DEBUG ===');
      console.log('State Meet IDs:', stateMeetIds);
      console.log('State results matching (M, 50, FR):', stateResults.length);
      if (stateResults.length > 0) {
        console.log('Sample state result:', stateResults[0]);
      }
      console.log('Applied Events:', appliedEvents);
      console.log('Applied Genders:', appliedGenders);
      console.log('All filtered results:', filteredResults.length);
      console.log('================================');
    }
    
    console.log('Filtered results count:', filteredResults.length, {
      appliedMeets: appliedMeets.length,
      appliedGenders: appliedGenders.length,
      appliedEvents: appliedEvents.length
    });
    if (filteredResults.length > 0) {
      console.log('Sample filtered result:', filteredResults[0]);
    }
  }, [filteredResults.length, appliedMeets, appliedGenders, appliedEvents, meets, results]);


  // Prevent hydration mismatch
  if (!mounted) {
    return (
      <>
        <Head>
          <title>Malaysia Swimming Analytics</title>
          <meta name="description" content="Modern swimming analytics platform for Malaysian swimming competitions" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <link rel="icon" href="/favicon.ico" />
        </Head>
        <div style={{ fontFamily: 'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif', fontSize: '14px', minHeight: '100vh', width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div>Loading...</div>
        </div>
      </>
    );
  }

  return (
    <>
      <Head>
        <title>Malaysia Swimming Analytics</title>
        <meta name="description" content="Modern swimming analytics platform for Malaysian swimming competitions" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      
      <div style={{ fontFamily: 'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif', fontSize: '14px', minHeight: '100vh', width: '100%' }}>
        {/* Header Container */}
        <div style={{ position: 'relative', textAlign: 'center', marginBottom: '20px' }}>
          <h1 style={{ fontSize: '1.4rem', margin: '0' }}>
            <img src="/mas-logo.png" alt="MAS Logo" style={{ height: '1em', verticalAlign: 'middle', margin: '0 6px' }} />
            Welcome to the Malaysia Times Database
            <img src="/mas-logo.png" alt="MAS Logo" style={{ height: '1em', verticalAlign: 'middle', margin: '0 6px' }} />
          </h1>
          <button
            onClick={() => router.push('/admin')}
            style={{
              position: 'absolute',
              top: '0',
              right: '0',
              padding: '8px 16px',
              backgroundColor: '#cc0000',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontSize: '0.9rem',
              cursor: 'pointer',
              fontWeight: '500'
            }}
          >
            Admin Panel
          </button>
        </div>

        {/* Page Layout - Main Content + Sidebar */}
        <div style={{ display: 'block' }}>
          <div style={{ width: '100%', minWidth: '0', boxSizing: 'border-box' }}>
            {/* All Controls Container */}
            <div style={{ fontSize: '0.9em', margin: '6px 0 8px 0', border: '1px solid #ddd', borderRadius: '8px', padding: '15px' }}>
              <form style={{ margin: 0 }}>
                {/* Meets */}
                <div style={{ margin: '2px 0' }}>
                  <strong>Meets:</strong>
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
                      {meet.meet_code || meet.name}
                    </label>
                  ))}
                </div>
                
                {/* Gender */}
                <div style={{ margin: '2px 0' }}>
                  <strong>Gender:</strong>
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
                    {/* All Events checkbox - must be first */}
                    <label style={{ margin: 0, lineHeight: '1.0', display: 'inline-block', whiteSpace: 'nowrap', fontWeight: 'bold' }}>
                      <input 
                        type="checkbox" 
                        name="events" 
                        value="ALL_EVENTS"
                        checked={selectedEvents.includes('ALL_EVENTS')}
                        onChange={(e) => handleEventChange('ALL_EVENTS', e.target.checked)}
                        style={{ accentColor: '#cc0000', marginRight: '4px' }}
                      />
                      All Events
                    </label>
                    {/* Row 1: Free */}
                    <label style={{ margin: 0, lineHeight: '1.0', display: 'inline-block', whiteSpace: 'nowrap' }}>
                      <input 
                        type="checkbox" 
                        name="events" 
                        value="50m FR"
                        checked={selectedEvents.includes('ALL_EVENTS') || selectedEvents.includes('50m FR')}
                        onChange={(e) => handleEventChange('50m FR', e.target.checked)}
                        style={{ accentColor: '#cc0000', marginRight: '4px' }}
                      />
                      50 Free
                    </label>
                    <label style={{ margin: 0, lineHeight: '1.0', display: 'inline-block', whiteSpace: 'nowrap' }}>
                      <input 
                        type="checkbox" 
                        name="events" 
                        value="100 Free"
                        checked={selectedEvents.includes('ALL_EVENTS') || selectedEvents.includes('100 Free')}
                        onChange={(e) => handleEventChange('100 Free', e.target.checked)}
                        style={{ accentColor: '#cc0000', marginRight: '4px' }}
                      />
                      100 Free
                    </label>
                    <label style={{ margin: 0, lineHeight: '1.0', display: 'inline-block', whiteSpace: 'nowrap' }}>
                      <input 
                        type="checkbox" 
                        name="events" 
                        value="200 Free"
                        checked={selectedEvents.includes('ALL_EVENTS') || selectedEvents.includes('200 Free')}
                        onChange={(e) => handleEventChange('200 Free', e.target.checked)}
                        style={{ accentColor: '#cc0000', marginRight: '4px' }}
                      />
                      200 Free
                    </label>
                    <label style={{ margin: 0, lineHeight: '1.0', display: 'inline-block', whiteSpace: 'nowrap' }}>
                      <input 
                        type="checkbox" 
                        name="events" 
                        value="400 Free"
                        checked={selectedEvents.includes('ALL_EVENTS') || selectedEvents.includes('400 Free')}
                        onChange={(e) => handleEventChange('400 Free', e.target.checked)}
                        style={{ accentColor: '#cc0000', marginRight: '4px' }}
                      />
                      400 Free
                    </label>
                    <label style={{ margin: 0, lineHeight: '1.0', display: 'inline-block', whiteSpace: 'nowrap' }}>
                      <input 
                        type="checkbox" 
                        name="events" 
                        value="800 Free"
                        checked={selectedEvents.includes('ALL_EVENTS') || selectedEvents.includes('800 Free')}
                        onChange={(e) => handleEventChange('800 Free', e.target.checked)}
                        style={{ accentColor: '#cc0000', marginRight: '4px' }}
                      />
                      800 Free
                    </label>
                    <label style={{ margin: 0, lineHeight: '1.0', display: 'inline-block', whiteSpace: 'nowrap' }}>
                      <input 
                        type="checkbox" 
                        name="events" 
                        value="1500 Free"
                        checked={selectedEvents.includes('ALL_EVENTS') || selectedEvents.includes('1500 Free')}
                        onChange={(e) => handleEventChange('1500 Free', e.target.checked)}
                        style={{ accentColor: '#cc0000', marginRight: '4px' }}
                      />
                      1500 Free
                    </label>

                    {/* Row 2: Back & Breast */}
                    <label style={{ margin: 0, lineHeight: '1.0', display: 'inline-block', whiteSpace: 'nowrap' }}>
                      <input 
                        type="checkbox" 
                        name="events" 
                        value="50 Back"
                        checked={selectedEvents.includes('ALL_EVENTS') || selectedEvents.includes('50 Back')}
                        onChange={(e) => handleEventChange('50 Back', e.target.checked)}
                        style={{ accentColor: '#cc0000', marginRight: '4px' }}
                      />
                      50 Back
                    </label>
                    <label style={{ margin: 0, lineHeight: '1.0', display: 'inline-block', whiteSpace: 'nowrap' }}>
                      <input 
                        type="checkbox" 
                        name="events" 
                        value="100 Back"
                        checked={selectedEvents.includes('ALL_EVENTS') || selectedEvents.includes('100 Back')}
                        onChange={(e) => handleEventChange('100 Back', e.target.checked)}
                        style={{ accentColor: '#cc0000', marginRight: '4px' }}
                      />
                      100 Back
                    </label>
                    <label style={{ margin: 0, lineHeight: '1.0', display: 'inline-block', whiteSpace: 'nowrap' }}>
                      <input 
                        type="checkbox" 
                        name="events" 
                        value="200 Back"
                        checked={selectedEvents.includes('ALL_EVENTS') || selectedEvents.includes('200 Back')}
                        onChange={(e) => handleEventChange('200 Back', e.target.checked)}
                        style={{ accentColor: '#cc0000', marginRight: '4px' }}
                      />
                      200 Back
                    </label>
                    <label style={{ margin: 0, lineHeight: '1.0', display: 'inline-block', whiteSpace: 'nowrap' }}>
                      <input 
                        type="checkbox" 
                        name="events" 
                        value="50 Breast"
                        checked={selectedEvents.includes('ALL_EVENTS') || selectedEvents.includes('50 Breast')}
                        onChange={(e) => handleEventChange('50 Breast', e.target.checked)}
                        style={{ accentColor: '#cc0000', marginRight: '4px' }}
                      />
                      50 Breast
                    </label>
                    <label style={{ margin: 0, lineHeight: '1.0', display: 'inline-block', whiteSpace: 'nowrap' }}>
                      <input 
                        type="checkbox" 
                        name="events" 
                        value="100 Breast"
                        checked={selectedEvents.includes('ALL_EVENTS') || selectedEvents.includes('100 Breast')}
                        onChange={(e) => handleEventChange('100 Breast', e.target.checked)}
                        style={{ accentColor: '#cc0000', marginRight: '4px' }}
                      />
                      100 Breast
                    </label>
                    <label style={{ margin: 0, lineHeight: '1.0', display: 'inline-block', whiteSpace: 'nowrap' }}>
                      <input 
                        type="checkbox" 
                        name="events" 
                        value="200 Breast"
                        checked={selectedEvents.includes('ALL_EVENTS') || selectedEvents.includes('200 Breast')}
                        onChange={(e) => handleEventChange('200 Breast', e.target.checked)}
                        style={{ accentColor: '#cc0000', marginRight: '4px' }}
                      />
                      200 Breast
                    </label>

                    {/* Row 3: Fly & IM */}
                    <label style={{ margin: 0, lineHeight: '1.0', display: 'inline-block', whiteSpace: 'nowrap' }}>
                      <input 
                        type="checkbox" 
                        name="events" 
                        value="50 Fly"
                        checked={selectedEvents.includes('ALL_EVENTS') || selectedEvents.includes('50 Fly')}
                        onChange={(e) => handleEventChange('50 Fly', e.target.checked)}
                        style={{ accentColor: '#cc0000', marginRight: '4px' }}
                      />
                      50 Fly
                    </label>
                    <label style={{ margin: 0, lineHeight: '1.0', display: 'inline-block', whiteSpace: 'nowrap' }}>
                      <input 
                        type="checkbox" 
                        name="events" 
                        value="100 Fly"
                        checked={selectedEvents.includes('ALL_EVENTS') || selectedEvents.includes('100 Fly')}
                        onChange={(e) => handleEventChange('100 Fly', e.target.checked)}
                        style={{ accentColor: '#cc0000', marginRight: '4px' }}
                      />
                      100 Fly
                    </label>
                    <label style={{ margin: 0, lineHeight: '1.0', display: 'inline-block', whiteSpace: 'nowrap' }}>
                      <input 
                        type="checkbox" 
                        name="events" 
                        value="200 Fly"
                        checked={selectedEvents.includes('ALL_EVENTS') || selectedEvents.includes('200 Fly')}
                        onChange={(e) => handleEventChange('200 Fly', e.target.checked)}
                        style={{ accentColor: '#cc0000', marginRight: '4px' }}
                      />
                      200 Fly
                    </label>
                    <label style={{ margin: 0, lineHeight: '1.0', display: 'inline-block', whiteSpace: 'nowrap' }}>
                      <input 
                        type="checkbox" 
                        name="events" 
                        value="200 IM"
                        checked={selectedEvents.includes('ALL_EVENTS') || selectedEvents.includes('200 IM')}
                        onChange={(e) => handleEventChange('200 IM', e.target.checked)}
                        style={{ accentColor: '#cc0000', marginRight: '4px' }}
                      />
                      200 IM
                    </label>
                    <label style={{ margin: 0, lineHeight: '1.0', display: 'inline-block', whiteSpace: 'nowrap' }}>
                      <input 
                        type="checkbox" 
                        name="events" 
                        value="400 IM"
                        checked={selectedEvents.includes('ALL_EVENTS') || selectedEvents.includes('400 IM')}
                        onChange={(e) => handleEventChange('400 IM', e.target.checked)}
                        style={{ accentColor: '#cc0000', marginRight: '4px' }}
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

                {/* Action Buttons */}
                <div style={{ margin: '2px 0' }}>
                  <button 
                    type="button" 
                    onClick={fetchFilteredData}
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
                    onClick={() => {
                      setSelectedMeets([]);
                      setSelectedGenders([]);
                      setSelectedEvents([]);
                      setAppliedMeets([]);
                      setAppliedGenders([]);
                      setAppliedEvents([]);
                    }}
                    style={{ 
                      fontSize: '0.9em', 
                      padding: '2px 10px', 
                      backgroundColor: '#cc0000', 
                      color: 'white', 
                      border: 'none', 
                      borderRadius: '4px'
                    }}
                  >
                    Reset Filters
                  </button>
                </div>
              </form>
            </div>

            {/* Results Table - Improved Styling from Old Build */}
            <table style={{ 
              borderCollapse: 'collapse', 
              width: '100%', 
              marginTop: '12px', 
              tableLayout: 'fixed',
              fontSize: '12.6px'
            }}>
              <thead style={{ position: 'sticky', top: 0, zIndex: 10 }}>
                <tr>
                  <th style={{ 
                    border: '1px solid #ccc', 
                    padding: '1px 3px', 
                    textAlign: 'center', 
                    background: '#f5f5f5', 
                    width: '4ch', 
                    whiteSpace: 'normal'
                  }}>Gender</th>
                  <th style={{ 
                    border: '1px solid #ccc', 
                    padding: '1px 3px', 
                    textAlign: 'center', 
                    background: '#f5f5f5', 
                    width: '8ch', 
                    whiteSpace: 'normal'
                  }}>Event</th>
                  <th style={{ 
                    border: '1px solid #ccc', 
                    padding: '1px 3px', 
                    textAlign: 'center', 
                    background: '#f5f5f5', 
                    width: '20ch', 
                    maxWidth: '20ch', 
                    whiteSpace: 'normal', 
                    wordWrap: 'break-word' 
                  }}>Name</th>
                  <th style={{ 
                    border: '1px solid #ccc', 
                    padding: '1px 3px', 
                    textAlign: 'center', 
                    background: '#f5f5f5', 
                    width: '6ch', 
                    maxWidth: '6ch', 
                    whiteSpace: 'normal', 
                    wordWrap: 'break-word' 
                  }}>Team</th>
                  <th style={{ 
                    border: '1px solid #ccc', 
                    padding: '1px 3px', 
                    textAlign: 'center', 
                    background: '#f5f5f5', 
                    width: '3ch', 
                    whiteSpace: 'normal',
                    lineHeight: '1.0'
                  }}>
                    <div>Year</div>
                    <div>Age</div>
                  </th>
                  <th style={{ 
                    border: '1px solid #ccc', 
                    padding: '1px 3px', 
                    textAlign: 'center', 
                    background: '#f5f5f5', 
                    width: '6ch', 
                    whiteSpace: 'normal'
                  }}>Meet</th>
                  <th style={{ 
                    border: '1px solid #ccc', 
                    padding: '1px 3px', 
                    textAlign: 'center', 
                    background: '#f5f5f5', 
                    width: '7ch', 
                    maxWidth: '7ch', 
                    whiteSpace: 'normal', 
                    wordWrap: 'break-word' 
                  }}>Time</th>
                  <th style={{ 
                    border: '1px solid #ccc', 
                    padding: '1px 3px', 
                    textAlign: 'center', 
                    background: '#f5f5f5', 
                    width: '6ch', 
                    whiteSpace: 'normal'
                  }}>AQUA</th>
                  <th style={{ 
                    border: '1px solid #ccc', 
                    padding: '1px 3px', 
                    textAlign: 'center', 
                    background: '#f5f5f5', 
                    width: '4ch', 
                    maxWidth: '4ch', 
                    whiteSpace: 'normal', 
                    wordWrap: 'break-word' 
                  }}>Place</th>
                  <th style={{ 
                    border: '1px solid #ccc', 
                    padding: '1px 3px', 
                    textAlign: 'center', 
                    background: '#f5f5f5', 
                    width: '6.5ch', 
                    maxWidth: '6.5ch', 
                    whiteSpace: 'normal', 
                    wordWrap: 'break-word' 
                  }}>On Track Target Time</th>
                  <th style={{ 
                    border: '1px solid #ccc', 
                    padding: '1px 3px', 
                    textAlign: 'center', 
                    background: '#f5f5f5', 
                    width: '8ch', 
                    maxWidth: '8ch', 
                    whiteSpace: 'normal', 
                    wordWrap: 'break-word' 
                  }}>On Track AQUA</th>
                  <th style={{ 
                    border: '1px solid #ccc', 
                    padding: '1px 3px', 
                    textAlign: 'center', 
                    background: '#f5f5f5', 
                    width: '7ch', 
                    maxWidth: '7ch', 
                    whiteSpace: 'normal', 
                    wordWrap: 'break-word' 
                  }}>Track Gap</th>
                  <th style={{ 
                    border: '1px solid #ccc', 
                    padding: '1px 3px', 
                    textAlign: 'center', 
                    background: '#f5f5f5', 
                    width: '6ch', 
                    maxWidth: '6ch', 
                    whiteSpace: 'normal', 
                    wordWrap: 'break-word' 
                  }}>Age Points</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={13} style={{ border: '1px solid #ccc', padding: '1px 3px', textAlign: 'center' }}>
                      Loading results...
                    </td>
                  </tr>
                ) : error ? (
                  <tr>
                    <td colSpan={13} style={{ border: '1px solid #ccc', padding: '1px 3px', textAlign: 'center', color: '#cc0000' }}>
                      Error loading data: {error}
                    </td>
                  </tr>
                ) : results.length === 0 ? (
                  <tr>
                    <td colSpan={13} style={{ border: '1px solid #ccc', padding: '1px 3px', textAlign: 'center' }}>
                      No data yet.
                    </td>
                  </tr>
                ) : (
                  filteredResults.map((result, index) => (
                    <tr key={index}>
                      <td style={{ border: '1px solid #ccc', padding: '1px 3px', textAlign: 'center' }}>{result.gender}</td>
                      <td style={{ border: '1px solid #ccc', padding: '1px 3px', textAlign: 'center' }}>{result.distance} {result.stroke === 'FR' ? 'Free' : result.stroke === 'BK' ? 'Back' : result.stroke === 'BR' ? 'Breast' : result.stroke === 'BU' ? 'Fly' : result.stroke === 'ME' ? 'IM' : result.stroke}</td>
                      <td style={{ 
                        border: '1px solid #ccc', 
                        padding: '1px 3px', 
                        overflow: 'hidden', 
                        textOverflow: 'ellipsis', 
                        whiteSpace: 'nowrap' 
                      }} title={result.name}>{result.name}</td>
                      <td style={{ border: '1px solid #ccc', padding: '1px 3px', textAlign: 'center' }}>-</td>
                      <td style={{ border: '1px solid #ccc', padding: '1px 3px', textAlign: 'center' }}>{result.age ?? '-'}</td>
                      <td style={{ border: '1px solid #ccc', padding: '1px 3px', textAlign: 'center' }}>{result.meet_code}</td>
                      <td style={{ 
                        border: '1px solid #ccc', 
                        padding: '1px 3px', 
                        textAlign: 'right', 
                        fontVariantNumeric: 'tabular-nums' 
                      }}>{result.time}</td>
                      <td style={{ border: '1px solid #ccc', padding: '1px 3px', textAlign: 'center' }}>{result.aqua_points ?? '-'}</td>
                      <td style={{ border: '1px solid #ccc', padding: '1px 3px', textAlign: 'center' }}>{result.place}</td>
                      <td style={{ border: '1px solid #ccc', padding: '1px 3px', textAlign: 'right' }}>-</td>
                      <td style={{ border: '1px solid #ccc', padding: '1px 3px', textAlign: 'center' }}>-</td>
                      <td style={{ border: '1px solid #ccc', padding: '1px 3px', textAlign: 'center' }}>-</td>
                      <td style={{ border: '1px solid #ccc', padding: '1px 3px', textAlign: 'center' }}>-</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Sidebar with Reference Buttons - Ported from Old Build */}
          <div style={{ 
            position: 'absolute', 
            right: '12px', 
            top: '96px', 
            width: '220px', 
            zIndex: 1 
          }}>
            <div style={{ 
              border: '1px solid #ddd', 
              borderRadius: '10px', 
              padding: '10px', 
              background: '#fafafa', 
              boxShadow: '0 6px 16px rgba(0,0,0,0.15)' 
            }}>
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: '1fr', 
                gap: '8px' 
              }}>
                <a href="/map" style={{ 
                  display: 'flex', 
                  flexDirection: 'column', 
                  alignItems: 'center', 
                  justifyContent: 'center', 
                  minHeight: '28px', 
                  padding: '4px 10px', 
                  borderRadius: '8px', 
                  background: '#cc0000', 
                  color: '#fff', 
                  textDecoration: 'none' 
                }}>
                  <span style={{ 
                    fontWeight: '800', 
                    letterSpacing: '0.3px', 
                    fontSize: '0.9rem', 
                    color: '#fff', 
                    lineHeight: '1.05' 
                  }}>MAP</span>
                  <span style={{ 
                    color: '#fff', 
                    fontSize: '0.68rem', 
                    lineHeight: '1.05', 
                    textAlign: 'center', 
                    whiteSpace: 'nowrap' 
                  }}>Malaysia Age Points</span>
                </a>
                <a href="/mot/index.html" style={{ 
                  display: 'flex', 
                  flexDirection: 'column', 
                  alignItems: 'center', 
                  justifyContent: 'center', 
                  minHeight: '28px', 
                  padding: '4px 10px', 
                  borderRadius: '8px', 
                  background: '#cc0000', 
                  color: '#fff', 
                  textDecoration: 'none' 
                }}>
                  <span style={{ 
                    fontWeight: '800', 
                    letterSpacing: '0.3px', 
                    fontSize: '0.9rem', 
                    color: '#fff', 
                    lineHeight: '1.05' 
                  }}>MOT</span>
                  <span style={{ 
                    color: '#fff', 
                    fontSize: '0.68rem', 
                    lineHeight: '1.05', 
                    textAlign: 'center', 
                    whiteSpace: 'nowrap' 
                  }}>Malaysia On Track Tables</span>
                </a>
                <a href="/ltad" style={{ 
                  display: 'flex', 
                  flexDirection: 'column', 
                  alignItems: 'center', 
                  justifyContent: 'center', 
                  minHeight: '28px', 
                  padding: '4px 10px', 
                  borderRadius: '8px', 
                  background: '#cc0000', 
                  color: '#fff', 
                  textDecoration: 'none' 
                }}>
                  <span style={{ 
                    fontWeight: '800', 
                    letterSpacing: '0.3px', 
                    fontSize: '0.9rem', 
                    color: '#fff', 
                    lineHeight: '1.05' 
                  }}>LTAD</span>
                  <span style={{ 
                    color: '#fff', 
                    fontSize: '0.68rem', 
                    lineHeight: '1.05', 
                    textAlign: 'center', 
                    whiteSpace: 'nowrap' 
                  }}>Long Term Athletic Development</span>
                </a>
                <a href="/aqua" style={{ 
                  display: 'flex', 
                  flexDirection: 'column', 
                  alignItems: 'center', 
                  justifyContent: 'center', 
                  minHeight: '28px', 
                  padding: '4px 10px', 
                  borderRadius: '8px', 
                  background: '#cc0000', 
                  color: '#fff', 
                  textDecoration: 'none' 
                }}>
                  <span style={{ 
                    fontWeight: '800', 
                    letterSpacing: '0.3px', 
                    fontSize: '0.9rem', 
                    color: '#fff', 
                    lineHeight: '1.05' 
                  }}>AQUA</span>
                  <span style={{ 
                    color: '#fff', 
                    fontSize: '0.68rem', 
                    lineHeight: '1.05', 
                    textAlign: 'center', 
                    whiteSpace: 'nowrap' 
                  }}>World Aquatics Points</span>
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}