import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';

interface Result {
  name: string;
  gender: string;
  age: number;
  year_age?: number;
  distance: number;
  stroke: string;
  time: string;
  place: number | string;  // Can be number or status (DQ, DNS, etc.)
  aqua_points: number;
  map_points?: number;
  mot?: string;        // MOT target time
  mot_aqua?: number;   // MOT AQUA points
  mot_gap?: number;    // Gap to MOT target
  sort_place?: number; // For sorting place column
  meet_id?: string;
  meet: string;
  meet_code: string;
  club_code?: string;
  club_name?: string;
  state_code?: string;
  nation?: string;
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
  meet_date?: string;
  meet_type?: string;
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
  const [clubFilter, setClubFilter] = useState<string>('');
  const [clubsForState, setClubsForState] = useState<{code: string, name: string}[]>([]);
  const [includeForeign, setIncludeForeign] = useState<boolean>(true);
  const [resultsMode, setResultsMode] = useState<string>('all');
  const [mounted, setMounted] = useState(false);

  // Year filter and modal states
  const [availableYears, setAvailableYears] = useState<number[]>([]);
  const [selectedYear, setSelectedYear] = useState<number | null>(null);
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]); // OPEN, MAST, PARA
  const [selectedScopes, setSelectedScopes] = useState<string[]>([]); // I, D
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);

  // Date range filters
  const [startDay, setStartDay] = useState<string>('');
  const [startMonth, setStartMonth] = useState<string>('');
  const [startYear, setStartYear] = useState<string>('');
  const [endDay, setEndDay] = useState<string>('');
  const [endMonth, setEndMonth] = useState<string>('');
  const [endYear, setEndYear] = useState<string>('');

  // Month names for dropdowns
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const monthMap: {[key: string]: string} = { 'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12' };
  
  // Applied filters (what's actually being used for filtering)
  const [appliedMeets, setAppliedMeets] = useState<string[]>([]);
  const [appliedGenders, setAppliedGenders] = useState<string[]>([]);
  const [appliedEvents, setAppliedEvents] = useState<string[]>([]);
  const [appliedAgeGroups, setAppliedAgeGroups] = useState<string[]>([]);
  const [isAutoLoading, setIsAutoLoading] = useState<boolean>(false);

  // Sorting state
  const [sortColumn, setSortColumn] = useState<string>('aqua_points');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

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

  // Fetch available years on mount
  useEffect(() => {
    fetch('http://localhost:8000/api/available-years')
      .then(res => res.json())
      .then(data => {
        const years = data.years || [];
        setAvailableYears(years);
        // Default to current year if available, otherwise first year in list
        const currentYear = new Date().getFullYear();
        if (years.includes(currentYear)) {
          setSelectedYear(currentYear);
        } else if (years.length > 0) {
          setSelectedYear(years[0]);
        }
      })
      .catch(err => {
        console.error('Error fetching available years:', err);
        // Fallback to current and previous year
        const currentYear = new Date().getFullYear();
        setAvailableYears([currentYear, currentYear - 1]);
        setSelectedYear(currentYear);
      });
  }, []);

  // Clear results and meet selections when Year/Type/Scope/Date filters change
  useEffect(() => {
    setSelectedMeets([]);
    setResults([]);
    setAppliedMeets([]);
  }, [selectedYear, selectedTypes, selectedScopes, startDay, startMonth, startYear, endDay, endMonth, endYear]);

  // Fetch clubs when state filter changes
  useEffect(() => {
    if (stateFilter) {
      fetch(`http://localhost:8000/api/clubs?state_code=${stateFilter}`)
        .then(res => res.json())
        .then(data => {
          setClubsForState(data.clubs || []);
          setClubFilter(''); // Reset club filter when state changes
        })
        .catch(err => {
          console.error('Error fetching clubs:', err);
          setClubsForState([]);
        });
    } else {
      setClubsForState([]);
      setClubFilter('');
    }
  }, [stateFilter]);

  const fetchData = async () => {
    try {
      setLoading(true);

      // Health check before fetching data
      const healthResponse = await fetch('http://localhost:8000/health');
      if (!healthResponse.ok) {
        throw new Error('Backend is not available');
      }

      // Fetch metadata only on page load (not results - those load when filters are applied)
      const timestamp = Date.now();
      const fetchOptions = {
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      };

      const [statsResponse, meetsResponse, eventsResponse] = await Promise.all([
        fetch(`http://localhost:8000/api/results/stats?t=${timestamp}`, fetchOptions),
        fetch(`http://localhost:8000/api/meets?t=${timestamp}`, fetchOptions),
        fetch(`http://localhost:8000/api/events?t=${timestamp}`, fetchOptions)
      ]);

      if (!statsResponse.ok) throw new Error('Failed to fetch stats');
      if (!meetsResponse.ok) throw new Error('Failed to fetch meets');
      if (!eventsResponse.ok) throw new Error('Failed to fetch events');

      const [statsData, meetsData, eventsData] = await Promise.all([
        statsResponse.json(),
        meetsResponse.json(),
        eventsResponse.json()
      ]);

      console.log('Fetched metadata:', { statsData, meetsData, eventsData });
      console.log('Meets received:', meetsData.meets);
      console.log('Meets count:', meetsData.meets?.length || 0);
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
      if (clubFilter) {
        params.append('club_code', clubFilter);
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

  // Export SXL GF - Top 100 per event to Excel workbook
  const exportSxlGf = async () => {
    try {
      setLoading(true);

      const params = new URLSearchParams();
      if (selectedMeets.length > 0) {
        params.append('meet_ids', selectedMeets.join(','));
      }
      if (selectedGenders.length > 0) {
        params.append('genders', selectedGenders.join(','));
      }
      if (selectedAgeGroups.length > 0 && !selectedAgeGroups.includes('OPEN')) {
        params.append('age_groups', selectedAgeGroups.join(','));
      }
      if (!includeForeign) {
        params.append('include_foreign', 'false');
      }

      const response = await fetch(`http://localhost:8000/api/results/export-sxl-gf?${params.toString()}`);

      if (!response.ok) throw new Error('Failed to export SXL GF');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'SXL_GF_Top100.xlsx';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed');
    } finally {
      setLoading(false);
    }
  };

  // Auto-fetch filtered results when meet + gender + age group + event are ALL selected
  useEffect(() => {
    const shouldAutoLoad = selectedMeets.length > 0 && selectedGenders.length > 0 && selectedAgeGroups.length > 0 && selectedEvents.length > 0;

    console.log('Auto-loading check:', {
      selectedMeets: selectedMeets,
      selectedGenders: selectedGenders,
      selectedAgeGroups: selectedAgeGroups,
      selectedEvents: selectedEvents,
      shouldAutoLoad: shouldAutoLoad
    });

    // Auto-fetch if meet(s) AND gender(s) AND age group(s) AND event(s) are ALL selected
    if (shouldAutoLoad) {
      console.log('Auto-loading triggered - fetching from server');
      setIsAutoLoading(true);
      setAppliedMeets(selectedMeets);
      setAppliedGenders(selectedGenders);
      setAppliedAgeGroups(selectedAgeGroups);
      setAppliedEvents(selectedEvents);

      // Build query params and fetch from server
      const params = new URLSearchParams();
      params.append('meet_ids', selectedMeets.join(','));
      params.append('genders', selectedGenders.join(','));
      if (!selectedEvents.includes('ALL_EVENTS')) {
        params.append('events', selectedEvents.join(','));
      }
      if (!selectedAgeGroups.includes('OPEN')) {
        params.append('age_groups', selectedAgeGroups.join(','));
      }
      if (!includeForeign) {
        params.append('include_foreign', 'false');
      }
      if (clubFilter) {
        params.append('club_code', clubFilter);
      }

      const timestamp = Date.now();
      const url = `http://localhost:8000/api/results/filtered?${params.toString()}&t=${timestamp}`;
      console.log('Fetching filtered results from:', url);
      fetch(url)
        .then(response => {
          if (!response.ok) throw new Error('Failed to fetch filtered results');
          return response.json();
        })
        .then(data => {
          console.log('Fetched filtered results:', data);
          console.log('Results count:', data.count, 'Results array length:', data.results?.length);
          if (data.error) {
            console.error('API returned error:', data.error);
          }
          setResults(data.results || []);
          setIsAutoLoading(false);
        })
        .catch(err => {
          console.error('Error fetching filtered results:', err);
          setError(err.message);
          setIsAutoLoading(false);
        });
    }
    // Clear results if conditions not met
    else {
      console.log('Clearing filters and results');
      setAppliedMeets([]);
      setAppliedGenders([]);
      setAppliedAgeGroups([]);
      setAppliedEvents([]);
      setResults([]);
    }
  }, [selectedMeets, selectedGenders, selectedAgeGroups, selectedEvents, includeForeign, clubFilter]);

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

  // Helper to build date string from dropdowns
  const buildDateString = (day: string, month: string, year: string): string | null => {
    if (!day || !month || !year) return null;
    const monthNum = monthMap[month];
    return `${year}-${monthNum}-${day.padStart(2, '0')}`;
  };

  // Compute filteredMeets based on year, type, scope, and date range filters
  const filteredMeets = meets.filter(meet => {
    if (!meet.meet_date) {
      return false; // Exclude meets without dates
    }

    try {
      const meetDate = new Date(meet.meet_date);
      const meetYear = meetDate.getFullYear();

      // Year filter (dropdown selection)
      if (selectedYear && meetYear !== selectedYear) {
        return false;
      }

      // Date range filter - Start date
      const startDateStr = buildDateString(startDay, startMonth, startYear);
      if (startDateStr) {
        const startDate = new Date(startDateStr);
        if (meetDate < startDate) {
          return false;
        }
      }

      // Date range filter - End date
      const endDateStr = buildDateString(endDay, endMonth, endYear);
      if (endDateStr) {
        const endDate = new Date(endDateStr);
        if (meetDate > endDate) {
          return false;
        }
      }
    } catch {
      return false;
    }

    // Type filter (OPEN, MAST, PARA)
    if (selectedTypes.length > 0) {
      const meetTypeValue = meet.meet_type || '';
      const meetTypeCode = meetTypeValue.split('-')[0] || '';
      if (!selectedTypes.includes(meetTypeCode)) {
        return false;
      }
    }

    // Scope filter (I = International, D = Domestic)
    if (selectedScopes.length > 0) {
      const meetTypeValue = meet.meet_type || '';
      const meetScope = meetTypeValue.split('-')[1] || '';
      if (!selectedScopes.includes(meetScope)) {
        return false;
      }
    }

    return true;
  });

  // Note: Results are now fetched server-side with filters applied
  // No client-side filtering needed - results state contains pre-filtered data

  // Handle column header click for sorting
  const handleSort = (column: string) => {
    if (sortColumn === column) {
      // Toggle direction if same column
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      // New column - set appropriate default direction
      setSortColumn(column);
      // AQUA points, MAP points, and MOT gap default to descending (highest/best first)
      if (column === 'aqua_points' || column === 'map_points' || column === 'mot_gap') {
        setSortDirection('desc');
      } else {
        setSortDirection('asc');
      }
    }
  };

  // Sort indicator component
  const SortIndicator = ({ column }: { column: string }) => {
    if (sortColumn !== column) return <span style={{ opacity: 0.3 }}> ▲</span>;
    return <span> {sortDirection === 'asc' ? '▲' : '▼'}</span>;
  };

  // Parse time string to seconds for sorting (e.g., "1:23.45" -> 83.45)
  const parseTimeToSeconds = (timeStr: string): number => {
    if (!timeStr) return 999999;
    const parts = timeStr.split(':');
    if (parts.length === 2) {
      return parseFloat(parts[0]) * 60 + parseFloat(parts[1]);
    }
    return parseFloat(timeStr) || 999999;
  };

  // Format time to always show two decimal places (24.1 -> 24.10)
  const formatTime = (timeStr: string): string => {
    if (!timeStr) return '-';
    // Check if time has a decimal point
    if (timeStr.includes('.')) {
      const parts = timeStr.split('.');
      const decimals = parts[parts.length - 1];
      if (decimals.length === 1) {
        return timeStr + '0';
      }
    }
    return timeStr;
  };

  // Check if multiple events are selected (for sorting logic)
  const multipleEventsSelected = selectedEvents.filter(e => e !== 'ALL_EVENTS').length > 1 || selectedEvents.includes('ALL_EVENTS');

  // Determine default sort for multiple events based on age group selection
  // Open = AQUA points, Age groups (16-18, 14-15, 12-13, 13U) = MAP points
  const isOpenSelected = selectedAgeGroups.includes('OPEN');
  const defaultMultiEventSort = isOpenSelected ? 'aqua_points' : 'map_points';

  // Sorted results - default to AQUA/MAP points when multiple events selected, otherwise time
  const effectiveSortColumn = (sortColumn === 'time' && multipleEventsSelected) ? defaultMultiEventSort : sortColumn;
  // When auto-switching to points, use descending (highest first)
  const effectiveSortDirection = (sortColumn === 'time' && multipleEventsSelected) ? 'desc' : sortDirection;

  // Filter to best times per athlete per event if "best" mode selected
  const resultsToSort = resultsMode === 'best'
    ? (() => {
        const bestByAthleteEvent = new Map<string, Result>();
        for (const result of results) {
          // Key by athlete name + event (distance + stroke)
          const key = `${result.name}_${result.distance}_${result.stroke}`;
          const existing = bestByAthleteEvent.get(key);
          const currentTime = parseTimeToSeconds(result.time);
          const existingTime = existing ? parseTimeToSeconds(existing.time) : Infinity;
          // Keep the faster time (lower seconds)
          if (currentTime < existingTime) {
            bestByAthleteEvent.set(key, result);
          }
        }
        return Array.from(bestByAthleteEvent.values());
      })()
    : results;

  const sortedResults = [...resultsToSort].sort((a, b) => {
    let aVal: number, bVal: number;

    switch (effectiveSortColumn) {
      case 'time':
        aVal = parseTimeToSeconds(a.time);
        bVal = parseTimeToSeconds(b.time);
        break;
      case 'aqua_points':
        aVal = a.aqua_points ?? 0;
        bVal = b.aqua_points ?? 0;
        break;
      case 'age':
        aVal = a.age ?? 0;
        bVal = b.age ?? 0;
        break;
      case 'place':
        // Use sort_place for numeric sorting (handles DQ, DNS, etc.)
        aVal = a.sort_place ?? (typeof a.place === 'number' ? a.place : 9999);
        bVal = b.sort_place ?? (typeof b.place === 'number' ? b.place : 9999);
        break;
      case 'map_points':
        aVal = a.map_points ?? 0;
        bVal = b.map_points ?? 0;
        break;
      case 'mot_gap':
        // Special sorting: those with MOT gap first (by gap), then those without (by MAP desc)
        const aHasMot = a.mot_gap !== undefined && a.mot_gap !== null;
        const bHasMot = b.mot_gap !== undefined && b.mot_gap !== null;

        if (aHasMot && bHasMot) {
          // Both have MOT - sort by gap value (direction applies)
          aVal = a.mot_gap!;
          bVal = b.mot_gap!;
        } else if (aHasMot && !bHasMot) {
          // a has MOT, b doesn't - a comes first
          return -1;
        } else if (!aHasMot && bHasMot) {
          // b has MOT, a doesn't - b comes first
          return 1;
        } else {
          // Neither has MOT - sort by MAP points descending (highest first)
          aVal = a.map_points ?? 0;
          bVal = b.map_points ?? 0;
          return bVal - aVal; // Always descending for non-MOT
        }
        break;
      default:
        return 0;
    }

    const diff = aVal - bVal;
    return effectiveSortDirection === 'asc' ? diff : -diff;
  });

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

        {/* Reference Buttons */}
        <div style={{ textAlign: 'center', marginBottom: '20px' }}>
          <div style={{ display: 'flex', flexDirection: 'row', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <a href="/map/index.html" style={{ width: '150px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '28px', padding: '4px 10px', borderRadius: '8px', background: '#cc0000', color: '#fff', textDecoration: 'none' }}>
              <span style={{ fontWeight: '800', letterSpacing: '0.3px', fontSize: '0.9rem', color: '#fff', lineHeight: '1.05' }}>MAP</span>
              <span style={{ color: '#fff', fontSize: '0.68rem', lineHeight: '1.05', textAlign: 'center', whiteSpace: 'nowrap' }}>Malaysia Age Points</span>
            </a>
            <a href="/mot/index.html" style={{ width: '150px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '28px', padding: '4px 10px', borderRadius: '8px', background: '#cc0000', color: '#fff', textDecoration: 'none' }}>
              <span style={{ fontWeight: '800', letterSpacing: '0.3px', fontSize: '0.9rem', color: '#fff', lineHeight: '1.05' }}>MOT</span>
              <span style={{ color: '#fff', fontSize: '0.68rem', lineHeight: '1.05', textAlign: 'center', whiteSpace: 'nowrap' }}>Malaysia On Track Tables</span>
            </a>
            <a href="/ltad" style={{ width: '150px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '28px', padding: '4px 10px', borderRadius: '8px', background: '#cc0000', color: '#fff', textDecoration: 'none' }}>
              <span style={{ fontWeight: '800', letterSpacing: '0.3px', fontSize: '0.9rem', color: '#fff', lineHeight: '1.05' }}>LTAD</span>
              <span style={{ color: '#fff', fontSize: '0.68rem', lineHeight: '1.05', textAlign: 'center', whiteSpace: 'nowrap' }}>Long Term Athletic Development</span>
            </a>
            <a href="/aqua/index.html" style={{ width: '150px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '28px', padding: '4px 10px', borderRadius: '8px', background: '#cc0000', color: '#fff', textDecoration: 'none' }}>
              <span style={{ fontWeight: '800', letterSpacing: '0.3px', fontSize: '0.9rem', color: '#fff', lineHeight: '1.05' }}>AQUA</span>
              <span style={{ color: '#fff', fontSize: '0.68rem', lineHeight: '1.05', textAlign: 'center', whiteSpace: 'nowrap' }}>World Aquatics Points</span>
            </a>
          </div>
        </div>
        {/* Filters Container */}
        <div style={{ display: 'block' }}>
          <div style={{ width: '100%', minWidth: '0', boxSizing: 'border-box' }}>
            {/* All Controls Container */}
            <div style={{ fontSize: '0.9em', margin: '6px 0 8px 0', border: '1px solid #ddd', borderRadius: '8px', padding: '15px' }}>
              <form style={{ margin: 0 }}>
                {/* Row 1: Year and Date Range */}
                <div style={{ margin: '2px 0', display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '15px' }}>
                  {/* Year Filter - Dropdown */}
                  <span>
                    <strong>Year</strong>:{' '}
                    <select
                      value={selectedYear || ''}
                      onChange={(e) => setSelectedYear(e.target.value ? parseInt(e.target.value) : null)}
                      style={{ marginLeft: '4px', padding: '1px 4px', borderRadius: '3px', border: '1px solid #ccc', fontSize: 'inherit' }}
                    >
                      <option value="">All</option>
                      {availableYears.map((year) => (
                        <option key={year} value={year}>{year}</option>
                      ))}
                    </select>
                  </span>

                  {/* Start Date */}
                  <span>
                    <strong>Start</strong>:{' '}
                    <select
                      value={startDay}
                      onChange={(e) => setStartDay(e.target.value)}
                      style={{ marginLeft: '4px', padding: '1px 2px', borderRadius: '3px', border: '1px solid #ccc', fontSize: 'inherit' }}
                    >
                      <option value="">dd</option>
                      {Array.from({ length: 31 }, (_, i) => i + 1).map((d) => (
                        <option key={d} value={d.toString()}>{d}</option>
                      ))}
                    </select>
                    <select
                      value={startMonth}
                      onChange={(e) => setStartMonth(e.target.value)}
                      style={{ marginLeft: '2px', padding: '1px 2px', borderRadius: '3px', border: '1px solid #ccc', fontSize: 'inherit' }}
                    >
                      <option value="">mmm</option>
                      {months.map((m) => (
                        <option key={m} value={m}>{m}</option>
                      ))}
                    </select>
                    <select
                      value={startYear}
                      onChange={(e) => setStartYear(e.target.value)}
                      style={{ marginLeft: '2px', padding: '1px 2px', borderRadius: '3px', border: '1px solid #ccc', fontSize: 'inherit' }}
                    >
                      <option value="">yyyy</option>
                      {availableYears.map((y) => (
                        <option key={y} value={y.toString()}>{y}</option>
                      ))}
                    </select>
                  </span>

                  {/* End Date */}
                  <span>
                    <strong>Finish</strong>:{' '}
                    <select
                      value={endDay}
                      onChange={(e) => setEndDay(e.target.value)}
                      style={{ marginLeft: '4px', padding: '1px 2px', borderRadius: '3px', border: '1px solid #ccc', fontSize: 'inherit' }}
                    >
                      <option value="">dd</option>
                      {Array.from({ length: 31 }, (_, i) => i + 1).map((d) => (
                        <option key={d} value={d.toString()}>{d}</option>
                      ))}
                    </select>
                    <select
                      value={endMonth}
                      onChange={(e) => setEndMonth(e.target.value)}
                      style={{ marginLeft: '2px', padding: '1px 2px', borderRadius: '3px', border: '1px solid #ccc', fontSize: 'inherit' }}
                    >
                      <option value="">mmm</option>
                      {months.map((m) => (
                        <option key={m} value={m}>{m}</option>
                      ))}
                    </select>
                    <select
                      value={endYear}
                      onChange={(e) => setEndYear(e.target.value)}
                      style={{ marginLeft: '2px', padding: '1px 2px', borderRadius: '3px', border: '1px solid #ccc', fontSize: 'inherit' }}
                    >
                      <option value="">yyyy</option>
                      {availableYears.map((y) => (
                        <option key={y} value={y.toString()}>{y}</option>
                      ))}
                    </select>
                  </span>

                  {/* Clear Date Range Button */}
                  {(startDay || startMonth || startYear || endDay || endMonth || endYear) && (
                    <button
                      type="button"
                      onClick={() => {
                        setStartDay(''); setStartMonth(''); setStartYear('');
                        setEndDay(''); setEndMonth(''); setEndYear('');
                      }}
                      style={{ padding: '1px 6px', fontSize: 'inherit', cursor: 'pointer', borderRadius: '3px', border: '1px solid #ccc', background: '#f5f5f5' }}
                    >
                      Clear
                    </button>
                  )}
                </div>

                {/* Row 2: Type and Scope Filters */}
                <div style={{ margin: '6px 0 2px 0', display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '15px' }}>
                  {/* Type Filter */}
                  <span>
                    <strong>Type</strong>:{' '}
                    {[
                      { value: 'OPEN', label: 'Open' },
                      { value: 'MAST', label: 'Masters' },
                      { value: 'PARA', label: 'Para' }
                    ].map(({ value, label }) => (
                      <label key={value} style={{ marginLeft: '8px', whiteSpace: 'nowrap' }}>
                        <input
                          type="checkbox"
                          checked={selectedTypes.includes(value)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedTypes([...selectedTypes, value]);
                            } else {
                              setSelectedTypes(selectedTypes.filter(t => t !== value));
                            }
                          }}
                          style={{ accentColor: '#cc0000', marginRight: '3px' }}
                        />
                        {label}
                      </label>
                    ))}
                  </span>

                  {/* Scope Filter */}
                  <span>
                    <strong>Scope</strong>:{' '}
                    {[
                      { value: 'D', label: 'Domestic' },
                      { value: 'I', label: 'International' },
                      { value: 'N', label: 'National Team' }
                    ].map(({ value, label }) => (
                      <label key={value} style={{ marginLeft: '8px', whiteSpace: 'nowrap' }}>
                        <input
                          type="checkbox"
                          checked={selectedScopes.includes(value)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedScopes([...selectedScopes, value]);
                            } else {
                              setSelectedScopes(selectedScopes.filter(s => s !== value));
                            }
                          }}
                          style={{ accentColor: '#cc0000', marginRight: '3px' }}
                        />
                        {label}
                      </label>
                    ))}
                  </span>
                </div>

                {/* Meets - only show when Type and Scope filters are selected */}
                {selectedTypes.length > 0 && selectedScopes.length > 0 && (
                  <div style={{ margin: '8px 0 2px 0' }}>
                    <strong>Meets:</strong>
                    <button
                      type="button"
                      onClick={() => setIsModalOpen(true)}
                      style={{
                        marginLeft: '8px',
                        padding: '2px 8px',
                        backgroundColor: '#cc0000',
                        color: 'white',
                        border: 'none',
                        borderRadius: '3px',
                        cursor: 'pointer',
                        fontSize: '0.85em',
                        fontWeight: 'normal'
                      }}
                    >
                      Lookup Aliases
                    </button>
                    {filteredMeets.length === 0 ? (
                      <div style={{ color: '#666', fontStyle: 'italic', marginTop: '4px' }}>
                        No meets match the selected criteria
                      </div>
                    ) : (
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, 80px)', gap: '2px 6px' }}>
                        {/* Select All checkbox */}
                        <label style={{ marginRight: '10px', whiteSpace: 'nowrap', fontWeight: 'bold' }}>
                          <input
                            type="checkbox"
                            checked={filteredMeets.length > 0 && filteredMeets.every(m => selectedMeets.includes(m.id))}
                            onChange={(e) => {
                              if (e.target.checked) {
                                // Add all filtered meets to selection
                                const allFilteredIds = filteredMeets.map(m => m.id);
                                const combined = [...selectedMeets, ...allFilteredIds];
                                setSelectedMeets(Array.from(new Set(combined)));
                              } else {
                                // Remove all filtered meets from selection
                                const filteredIds = filteredMeets.map(m => m.id);
                                setSelectedMeets(selectedMeets.filter(id => !filteredIds.includes(id)));
                              }
                            }}
                            style={{ accentColor: '#cc0000', marginRight: '4px' }}
                          />
                          All
                        </label>
                        {filteredMeets.map((meet) => (
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
                    )}
                  </div>
                )}
                
                {/* Gender */}
                <div style={{ margin: '2px 0' }}>
                  <strong>Gender:</strong>
                  <label style={{ marginLeft: '8px', marginRight: '10px', whiteSpace: 'nowrap' }}>
                    <input
                      type="radio"
                      name="gender"
                      checked={selectedGenders.length === 1 && selectedGenders.includes('M')}
                      onChange={() => setSelectedGenders(['M'])}
                      style={{ accentColor: '#cc0000', marginRight: '4px' }}
                    />
                    Male
                  </label>
                  <label style={{ marginRight: '10px', whiteSpace: 'nowrap' }}>
                    <input
                      type="radio"
                      name="gender"
                      checked={selectedGenders.length === 1 && selectedGenders.includes('F')}
                      onChange={() => setSelectedGenders(['F'])}
                      style={{ accentColor: '#cc0000', marginRight: '4px' }}
                    />
                    Female
                  </label>
                  <label style={{ marginRight: '10px', whiteSpace: 'nowrap' }}>
                    <input
                      type="radio"
                      name="gender"
                      checked={selectedGenders.length === 2 && selectedGenders.includes('M') && selectedGenders.includes('F')}
                      onChange={() => setSelectedGenders(['M', 'F'])}
                      style={{ accentColor: '#cc0000', marginRight: '4px' }}
                    />
                    Both
                  </label>
                </div>
                
                {/* State and Club */}
                <div style={{ margin: '2px 0' }}>
                  <span style={{ marginRight: '8px' }}>
                    <strong>State</strong>:
                  </span>
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
                  {stateFilter && (
                    <>
                      <span style={{ marginRight: '8px' }}>
                        <strong>Club</strong>:
                      </span>
                      <select
                        name="club_code"
                        value={clubFilter}
                        onChange={(e) => setClubFilter(e.target.value)}
                        style={{ marginRight: '10px', whiteSpace: 'nowrap' }}
                      >
                        <option value="">All Clubs</option>
                        {clubsForState.map(club => (
                          <option key={club.code} value={club.code}>
                            {club.code} - {club.name}
                          </option>
                        ))}
                      </select>
                    </>
                  )}
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
                      value="17+"
                      checked={selectedAgeGroups.includes('17+')}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedAgeGroups([...selectedAgeGroups.filter(g => g !== 'OPEN'), '17+']);
                        } else {
                          setSelectedAgeGroups(selectedAgeGroups.filter(g => g !== '17+'));
                        }
                      }}
                      style={{ accentColor: '#cc0000', marginRight: '4px' }}
                    />
                    17+
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
                
                <div style={{ margin: '2px 0' }}>
                  <strong>Events:</strong>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(50px, 1fr))', gap: '0px 6px' }}>
                    <label style={{ margin: 0, lineHeight: '1.0', display: 'inline-block', whiteSpace: 'nowrap', fontWeight: 'bold' }}>
                      <input
                        type="checkbox"
                        name="events"
                        value="ALL_EVENTS"
                        checked={selectedEvents.includes('ALL_EVENTS')}
                        onChange={(e) => handleEventChange('ALL_EVENTS', e.target.checked)}
                        style={{ accentColor: '#cc0000', marginRight: '4px' }}
                      />
                      All
                    </label>
                    <label style={{ margin: 0, lineHeight: '1.0', display: 'inline-block', whiteSpace: 'nowrap' }}>
                      <input
                        type="checkbox"
                        name="events"
                        value="50m FR"
                        checked={selectedEvents.includes('ALL_EVENTS') || selectedEvents.includes('50m FR')}
                        onChange={(e) => handleEventChange('50m FR', e.target.checked)}
                        style={{ accentColor: '#cc0000', marginRight: '4px' }}
                      />
                      50 Fr
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
                      100 Fr
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
                      200 Fr
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
                      400 Fr
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
                      800 Fr
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
                      1500 Fr
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
                      50 Bk
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
                      100 Bk
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
                      200 Bk
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
                      50 Br
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
                      100 Br
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
                      200 Br
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
                      50 Fl
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
                      100 Fl
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
                      200 Fl
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
                  <button
                    type="button"
                    onClick={exportSxlGf}
                    style={{
                      fontSize: '0.9em',
                      padding: '2px 10px',
                      backgroundColor: '#cc0000',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      marginLeft: '8px'
                    }}
                  >
                    SXL GF
                  </button>
                </div>
              </form>

              {/* Meet Aliases Lookup Modal */}
              {isModalOpen && (
                <div
                  style={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    backgroundColor: 'rgba(0, 0, 0, 0.5)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    zIndex: 1000
                  }}
                >
                  <div
                    style={{
                      backgroundColor: 'white',
                      borderRadius: '8px',
                      padding: '20px',
                      maxWidth: '600px',
                      maxHeight: '80vh',
                      overflow: 'auto',
                      boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        marginBottom: '15px',
                        paddingBottom: '10px',
                        borderBottom: '1px solid #ddd'
                      }}
                    >
                      <h2 style={{ margin: 0, fontSize: '1.2em' }}>Meet Aliases Lookup</h2>
                      <button
                        type="button"
                        onClick={() => setIsModalOpen(false)}
                        style={{
                          backgroundColor: 'transparent',
                          border: 'none',
                          fontSize: '1.5em',
                          cursor: 'pointer',
                          color: '#666'
                        }}
                      >
                        ×
                      </button>
                    </div>

                    <div style={{ fontSize: '0.9em' }}>
                      {meets.length === 0 ? (
                        <p style={{ color: '#666' }}>No meets available</p>
                      ) : (
                        <table
                          style={{
                            width: '100%',
                            borderCollapse: 'collapse'
                          }}
                        >
                          <thead>
                            <tr style={{ backgroundColor: '#f5f5f5' }}>
                              <th
                                style={{
                                  border: '1px solid #ddd',
                                  padding: '8px',
                                  textAlign: 'left',
                                  fontWeight: 'bold'
                                }}
                              >
                                Code
                              </th>
                              <th
                                style={{
                                  border: '1px solid #ddd',
                                  padding: '8px',
                                  textAlign: 'left',
                                  fontWeight: 'bold'
                                }}
                              >
                                Name
                              </th>
                            </tr>
                          </thead>
                          <tbody>
                            {meets.map((meet, index) => (
                              <tr
                                key={meet.id}
                                style={{
                                  backgroundColor: index % 2 === 0 ? '#f9f9f9' : 'white'
                                }}
                              >
                                <td
                                  style={{
                                    border: '1px solid #ddd',
                                    padding: '8px',
                                    fontWeight: '500'
                                  }}
                                >
                                  {meet.meet_code || '-'}
                                </td>
                                <td
                                  style={{
                                    border: '1px solid #ddd',
                                    padding: '8px'
                                  }}
                                >
                                  {meet.name}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      )}
                    </div>
                  </div>
                </div>
              )}
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
                  <th
                    onClick={() => handleSort('age')}
                    style={{
                    border: '1px solid #ccc',
                    padding: '1px 3px',
                    textAlign: 'center',
                    background: '#f5f5f5',
                    width: '3ch',
                    whiteSpace: 'normal',
                    lineHeight: '1.0',
                    cursor: 'pointer'
                  }}>
                    <div>Year</div>
                    <div>Age<SortIndicator column="age" /></div>
                  </th>
                  <th style={{ 
                    border: '1px solid #ccc', 
                    padding: '1px 3px', 
                    textAlign: 'center', 
                    background: '#f5f5f5', 
                    width: '6ch', 
                    whiteSpace: 'normal'
                  }}>Meet</th>
                  <th
                    onClick={() => handleSort('time')}
                    style={{
                    border: '1px solid #ccc',
                    padding: '1px 3px',
                    textAlign: 'center',
                    background: '#f5f5f5',
                    width: '7ch',
                    maxWidth: '7ch',
                    whiteSpace: 'normal',
                    wordWrap: 'break-word',
                    cursor: 'pointer'
                  }}>Time<SortIndicator column="time" /></th>
                  <th
                    onClick={() => handleSort('aqua_points')}
                    style={{
                    border: '1px solid #ccc',
                    padding: '1px 3px',
                    textAlign: 'center',
                    background: '#f5f5f5',
                    width: '6ch',
                    whiteSpace: 'normal',
                    cursor: 'pointer'
                  }}>AQUA<SortIndicator column="aqua_points" /></th>
                  <th
                    onClick={() => handleSort('place')}
                    style={{
                    border: '1px solid #ccc',
                    padding: '1px 3px',
                    textAlign: 'center',
                    background: '#f5f5f5',
                    width: '4ch',
                    maxWidth: '4ch',
                    whiteSpace: 'normal',
                    wordWrap: 'break-word',
                    cursor: 'pointer'
                  }}>Comp Place<SortIndicator column="place" /></th>
                  <th style={{
                    border: '1px solid #ccc',
                    padding: '1px 3px',
                    textAlign: 'center',
                    background: '#f5f5f5',
                    width: '6.5ch',
                    maxWidth: '6.5ch',
                    whiteSpace: 'normal',
                    wordWrap: 'break-word'
                  }}>MOT</th>
                  <th style={{
                    border: '1px solid #ccc',
                    padding: '1px 3px',
                    textAlign: 'center',
                    background: '#f5f5f5',
                    width: '8ch',
                    maxWidth: '8ch',
                    whiteSpace: 'normal',
                    wordWrap: 'break-word'
                  }}>MOT Aqua</th>
                  <th
                    onClick={() => handleSort('mot_gap')}
                    style={{
                    border: '1px solid #ccc',
                    padding: '1px 3px',
                    textAlign: 'center',
                    background: '#f5f5f5',
                    width: '7ch',
                    maxWidth: '7ch',
                    whiteSpace: 'normal',
                    wordWrap: 'break-word',
                    cursor: 'pointer'
                  }}>MOT Gap<SortIndicator column="mot_gap" /></th>
                  <th
                    onClick={() => handleSort('map_points')}
                    style={{
                    border: '1px solid #ccc',
                    padding: '1px 3px',
                    textAlign: 'center',
                    background: '#f5f5f5',
                    width: '6ch',
                    maxWidth: '6ch',
                    whiteSpace: 'normal',
                    wordWrap: 'break-word',
                    cursor: 'pointer'
                  }}>MAP<SortIndicator column="map_points" /></th>
                </tr>
              </thead>
              <tbody>
                {(loading || isAutoLoading) ? (
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
                ) : sortedResults.length === 0 ? (
                  <tr>
                    <td colSpan={13} style={{ border: '1px solid #ccc', padding: '1px 3px', textAlign: 'center' }}>
                      Select a meet, gender, age group, and event to load results.
                    </td>
                  </tr>
                ) : (
                  sortedResults.map((result, index) => (
                    <tr key={index}>
                      <td style={{ border: '1px solid #ccc', padding: '1px 3px', textAlign: 'center' }}>{result.gender}</td>
                      <td style={{ border: '1px solid #ccc', padding: '1px 3px', textAlign: 'center' }}>{result.distance} {result.stroke === 'Medley' ? 'IM' : result.stroke}</td>
                      <td style={{
                        border: '1px solid #ccc',
                        padding: '1px 3px',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                      }} title={result.name}>{result.name}</td>
                      <td style={{ border: '1px solid #ccc', padding: '1px 3px', textAlign: 'center' }} title={result.club_name || ''}>{result.club_code || '-'}</td>
                      <td style={{ border: '1px solid #ccc', padding: '1px 3px', textAlign: 'center' }}>{result.age ?? '-'}</td>
                      <td style={{ border: '1px solid #ccc', padding: '1px 3px', textAlign: 'center' }}>{result.meet_code}</td>
                      <td style={{
                        border: '1px solid #ccc',
                        padding: '1px 3px',
                        textAlign: 'right',
                        fontVariantNumeric: 'tabular-nums'
                      }}>{formatTime(result.time)}</td>
                      <td style={{ border: '1px solid #ccc', padding: '1px 3px', textAlign: 'center' }}>{result.aqua_points ?? '-'}</td>
                      <td style={{ border: '1px solid #ccc', padding: '1px 3px', textAlign: 'center' }}>{result.place}</td>
                      <td style={{ border: '1px solid #ccc', padding: '1px 3px', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{result.mot ?? '-'}</td>
                      <td style={{ border: '1px solid #ccc', padding: '1px 3px', textAlign: 'center' }}>{result.mot_aqua ?? '-'}</td>
                      <td style={{
                        border: '1px solid #ccc',
                        padding: '1px 3px',
                        textAlign: 'center',
                        color: result.mot_gap !== undefined && result.mot_gap !== null
                          ? (result.mot_gap >= 0 ? '#16a34a' : '#dc2626')
                          : 'inherit'
                      }}>{result.mot_gap !== undefined && result.mot_gap !== null ? (result.mot_gap >= 0 ? '+' : '') + result.mot_gap : '-'}</td>
                      <td style={{ border: '1px solid #ccc', padding: '1px 3px', textAlign: 'center' }}>{result.map_points ?? '-'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </>
  );
}