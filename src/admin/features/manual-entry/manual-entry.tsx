/**
 * Base Table Management Feature Component
 * Export and Update buttons for MAP, MOT, AQUA, and Podium Target Times tables
 */

import React, { useState, useEffect } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

interface EventTime {
  event_id: string;
  event_display: string;
  gender: string;
  time_string: string;
}

interface MapEventTime {
  event_id: string;
  event_display: string;
  gender: string;
  selectedAge: number;
  time_string: string;
  // Store all ages' times so we can switch without re-fetching
  timesByAge: Record<number, string>;
}

interface AquaEventTime {
  event_id: string;
  event_display: string;
  gender: string;
  selectedCourse: string;
  time_string: string;
  // Store times by course so we can switch without re-fetching
  timesByCourse: Record<string, string>;
}

interface CanadaEventTime {
  event_id: string;
  event_display: string;
  gender: string;
  selectedTrack: number;
  selectedAge: number;
  time_string: string;
  // Store times by track+age combo so we can switch without re-fetching
  timesByTrackAge: Record<string, string>;  // key: "track_age" e.g. "1_16"
  availableAges: number[];  // ages available for this event
  tracksByAge: Record<number, number[]>;  // which tracks are available for each age
}

interface MotEventTime {
  event_id: string;
  event_display: string;
  gender: string;
  selectedAge: number;
  time_string: string;
  is_50m: boolean;
  // Store all ages' times so we can switch without re-fetching
  timesByAge: Record<number, string>;
}

export interface ManualEntryProps {
  isAuthenticated: boolean;
}

export const ManualEntry: React.FC<ManualEntryProps> = ({
  isAuthenticated,
}) => {
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  // Podium Target Times Modal State
  const [showPodiumModal, setShowPodiumModal] = useState(false);
  const [podiumYear, setPodiumYear] = useState<number>(2025);
  const [podiumTimes, setPodiumTimes] = useState<EventTime[]>([]);
  const [availableYears, setAvailableYears] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);

  // MAP Base Times Modal State
  const [showMapModal, setShowMapModal] = useState(false);
  const [mapYear, setMapYear] = useState<number>(2025);
  const [availableMapYears, setAvailableMapYears] = useState<number[]>([]);
  const [mapTimes, setMapTimes] = useState<MapEventTime[]>([]);

  // AQUA Base Times Modal State
  const [showAquaModal, setShowAquaModal] = useState(false);
  const [aquaYear, setAquaYear] = useState<number>(2025);
  const [availableAquaYears, setAvailableAquaYears] = useState<number[]>([]);
  const [availableAquaCourses, setAvailableAquaCourses] = useState<string[]>([]);
  const [aquaTimes, setAquaTimes] = useState<AquaEventTime[]>([]);

  // Canada On Track Modal State
  const [showCanadaModal, setShowCanadaModal] = useState(false);
  const [canadaYear, setCanadaYear] = useState<number>(2025);
  const [availableCanadaYears, setAvailableCanadaYears] = useState<number[]>([]);
  const [canadaTimes, setCanadaTimes] = useState<CanadaEventTime[]>([]);

  // MOT Base Times Modal State
  const [showMotModal, setShowMotModal] = useState(false);
  const [motTimes, setMotTimes] = useState<MotEventTime[]>([]);

  // Generate years 2000-2029 for MAP
  const mapYearOptions: number[] = [];
  for (let year = 2029; year >= 2000; year--) {
    mapYearOptions.push(year);
  }

  // Generate years 2025-2029 for AQUA (no historical data)
  const aquaYearOptions = [2025, 2026, 2027, 2028, 2029];
  const aquaCourseOptions = ['LCM', 'SCM'];

  // Generate odd years from 1959 to current year + 4 (SEA Games are odd years)
  const seaGamesYears: number[] = [];
  const currentYear = new Date().getFullYear();
  for (let year = currentYear + 4; year >= 1959; year--) {
    if (year % 2 === 1) {
      seaGamesYears.push(year);
    }
  }

  // Ages for MAP times
  const mapAges = [12, 13, 14, 15, 16, 17, 18];

  // Ages for MOT times (15-23 for 100m+, 18-23 for 50m)
  const motAges = [15, 16, 17, 18, 19, 20, 21, 22, 23];
  const motAges50m = [18, 19, 20, 21, 22, 23];

  // Years and tracks for Canada On Track
  const canadaYearOptions = [2025, 2026, 2027, 2028, 2029];
  const canadaTracks = [1, 2, 3];

  const handleExport = async (tableType: 'map' | 'mot' | 'aqua' | 'podium' | 'canada') => {
    try {
      setError('');
      const response = await fetch(`${API_BASE}/api/admin/export-base-table/${tableType}`);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to export ${tableType.toUpperCase()} table: ${response.status} ${errorText}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${tableType}_base_times.xlsx`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.message);
      console.error('Export error:', err);
    }
  };

  const handleUpdate = (tableType: 'map' | 'mot' | 'aqua' | 'podium' | 'canada') => {
    setError('');
    setMessage('');

    if (tableType === 'podium') {
      setShowPodiumModal(true);
      loadPodiumData();
    } else if (tableType === 'map') {
      setShowMapModal(true);
      loadMapData();
    } else if (tableType === 'aqua') {
      setShowAquaModal(true);
      loadAquaData();
    } else if (tableType === 'canada') {
      setShowCanadaModal(true);
      loadCanadaData();
    } else if (tableType === 'mot') {
      setShowMotModal(true);
      loadMotData();
    }
  };

  const loadPodiumData = async () => {
    setLoading(true);
    setError('');
    try {
      // Get all events
      const eventsRes = await fetch(`${API_BASE}/api/admin/events-list`);
      if (!eventsRes.ok) {
        throw new Error(`Events API returned ${eventsRes.status}: ${await eventsRes.text()}`);
      }
      const eventsData = await eventsRes.json();

      if (!eventsData.events || eventsData.events.length === 0) {
        throw new Error('No events returned from API');
      }

      // Get existing times
      const timesRes = await fetch(`${API_BASE}/api/admin/podium-target-times`);
      if (!timesRes.ok) {
        throw new Error(`Times API returned ${timesRes.status}: ${await timesRes.text()}`);
      }
      const timesData = await timesRes.json();

      setAvailableYears(timesData.available_years || []);

      // Create a map of existing times by event_id and year
      const existingTimesMap: Record<string, Record<number, string>> = {};
      for (const t of timesData.times || []) {
        if (!existingTimesMap[t.event_id]) {
          existingTimesMap[t.event_id] = {};
        }
        existingTimesMap[t.event_id][t.sea_games_year] = t.target_time_string;
      }

      // Build the times array with all events
      const times: EventTime[] = eventsData.events.map((evt: any) => ({
        event_id: evt.event_id,
        event_display: evt.event_display,
        gender: evt.gender,
        time_string: existingTimesMap[evt.event_id]?.[podiumYear] || ''
      }));

      setPodiumTimes(times);
    } catch (err: any) {
      console.error('Load podium data error:', err);
      setError('Failed to load podium data: ' + err.message);
      setPodiumTimes([]);
    } finally {
      setLoading(false);
    }
  };

  const loadTimesForYear = async (year: number) => {
    setPodiumYear(year);
    setLoading(true);
    setError('');
    try {
      const eventsRes = await fetch(`${API_BASE}/api/admin/events-list`);
      if (!eventsRes.ok) {
        throw new Error(`Events API error: ${eventsRes.status}`);
      }
      const eventsData = await eventsRes.json();

      const timesRes = await fetch(`${API_BASE}/api/admin/podium-target-times?year=${year}`);
      if (!timesRes.ok) {
        throw new Error(`Times API error: ${timesRes.status}`);
      }
      const timesData = await timesRes.json();

      const existingTimesMap: Record<string, string> = {};
      for (const t of timesData.times || []) {
        existingTimesMap[t.event_id] = t.target_time_string;
      }

      const times: EventTime[] = eventsData.events.map((evt: any) => ({
        event_id: evt.event_id,
        event_display: evt.event_display,
        gender: evt.gender,
        time_string: existingTimesMap[evt.event_id] || ''
      }));

      setPodiumTimes(times);
    } catch (err: any) {
      console.error('Load times error:', err);
      setError('Failed to load times: ' + err.message);
      setPodiumTimes([]);
    } finally {
      setLoading(false);
    }
  };

  const handleTimeChange = (eventId: string, value: string) => {
    setPodiumTimes(prev =>
      prev.map(t =>
        t.event_id === eventId ? { ...t, time_string: value } : t
      )
    );
  };

  const savePodiumTimes = async () => {
    setLoading(true);
    try {
      const timesToSave = podiumTimes
        .filter(t => t.time_string.trim() !== '')
        .map(t => ({
          event_id: t.event_id,
          time_string: t.time_string
        }));

      const response = await fetch(`${API_BASE}/api/admin/podium-target-times`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ year: podiumYear, times: timesToSave })
      });

      const result = await response.json();
      if (result.success) {
        setMessage(`Saved ${result.updated} updated, ${result.inserted} inserted for year ${podiumYear}`);
        setShowPodiumModal(false);
      } else {
        setError('Failed to save: ' + (result.detail || 'Unknown error'));
      }
    } catch (err: any) {
      setError('Failed to save: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // MAP Base Times Functions
  const loadMapData = async (year: number = mapYear) => {
    setLoading(true);
    setError('');
    try {
      // Get all events
      const eventsRes = await fetch(`${API_BASE}/api/admin/events-list`);
      if (!eventsRes.ok) {
        throw new Error(`Events API returned ${eventsRes.status}`);
      }
      const eventsData = await eventsRes.json();

      // Get existing MAP times for this year (all ages)
      const timesRes = await fetch(`${API_BASE}/api/admin/map-base-times?year=${year}`);
      if (!timesRes.ok) {
        throw new Error(`MAP times API returned ${timesRes.status}`);
      }
      const timesData = await timesRes.json();

      // Store available years
      setAvailableMapYears(timesData.available_years || []);

      // Create a map of existing times by event_id and age
      const existingTimesMap: Record<string, Record<number, string>> = {};
      for (const t of timesData.times || []) {
        if (!existingTimesMap[t.event_id]) {
          existingTimesMap[t.event_id] = {};
        }
        existingTimesMap[t.event_id][t.age] = t.time_string;
      }

      // Build the times array with all events, default to age 12
      const times: MapEventTime[] = eventsData.events.map((evt: any) => {
        const timesByAge = existingTimesMap[evt.event_id] || {};
        return {
          event_id: evt.event_id,
          event_display: evt.event_display,
          gender: evt.gender,
          selectedAge: 12,
          time_string: timesByAge[12] || '',
          timesByAge: timesByAge
        };
      });

      setMapTimes(times);
    } catch (err: any) {
      console.error('Load MAP data error:', err);
      setError('Failed to load MAP data: ' + err.message);
      setMapTimes([]);
    } finally {
      setLoading(false);
    }
  };

  const handleMapTimeChange = (eventId: string, value: string) => {
    setMapTimes(prev =>
      prev.map(t => {
        if (t.event_id === eventId) {
          // Update both time_string and the timesByAge for the selected age
          const newTimesByAge = { ...t.timesByAge, [t.selectedAge]: value };
          return { ...t, time_string: value, timesByAge: newTimesByAge };
        }
        return t;
      })
    );
  };

  const handleMapAgeChange = (eventId: string, newAge: number) => {
    setMapTimes(prev =>
      prev.map(t => {
        if (t.event_id === eventId) {
          // Switch to the new age and load that age's time
          return {
            ...t,
            selectedAge: newAge,
            time_string: t.timesByAge[newAge] || ''
          };
        }
        return t;
      })
    );
  };

  const saveMapTimes = async () => {
    setLoading(true);
    try {
      // Group times by age for batch saving
      const timesByAge: Record<number, { event_id: string; time_string: string }[]> = {};

      for (const t of mapTimes) {
        // Save any age that has a non-empty time in timesByAge
        for (const [ageStr, timeStr] of Object.entries(t.timesByAge)) {
          const age = parseInt(ageStr);
          if (timeStr && timeStr.trim() !== '') {
            if (!timesByAge[age]) {
              timesByAge[age] = [];
            }
            timesByAge[age].push({ event_id: t.event_id, time_string: timeStr });
          }
        }
      }

      let totalUpdated = 0;
      let totalInserted = 0;

      // Save each age group
      for (const [ageStr, times] of Object.entries(timesByAge)) {
        const age = parseInt(ageStr);
        const response = await fetch(`${API_BASE}/api/admin/map-base-times`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ age, year: mapYear, times })
        });

        const result = await response.json();
        if (result.success) {
          totalUpdated += result.updated;
          totalInserted += result.inserted;
        }
      }

      setMessage(`Saved ${totalUpdated} updated, ${totalInserted} inserted across all ages`);
      setShowMapModal(false);
    } catch (err: any) {
      setError('Failed to save: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // AQUA Base Times Functions
  const loadAquaData = async (year: number = aquaYear) => {
    setLoading(true);
    setError('');
    try {
      // Get all events
      const eventsRes = await fetch(`${API_BASE}/api/admin/events-list`);
      if (!eventsRes.ok) {
        throw new Error(`Events API returned ${eventsRes.status}`);
      }
      const eventsData = await eventsRes.json();

      // Get existing AQUA times for this year (all courses)
      const timesRes = await fetch(`${API_BASE}/api/admin/aqua-base-times?year=${year}`);
      if (!timesRes.ok) {
        throw new Error(`AQUA times API returned ${timesRes.status}`);
      }
      const timesData = await timesRes.json();

      // Store available years and courses
      setAvailableAquaYears(timesData.available_years || []);
      setAvailableAquaCourses(timesData.available_courses || []);

      // Create a map of existing times by event base (without course prefix) and course
      const existingTimesMap: Record<string, Record<string, string>> = {};
      for (const t of timesData.times || []) {
        // Extract base event (stroke_distance_gender) from event_id
        const parts = t.event_id.split('_');
        if (parts.length >= 4) {
          const baseEvent = `${parts[1]}_${parts[2]}_${parts[3]}`; // e.g., Free_100_M
          if (!existingTimesMap[baseEvent]) {
            existingTimesMap[baseEvent] = {};
          }
          existingTimesMap[baseEvent][t.course] = t.time_string;
        }
      }

      // Build the times array with all events, default to LCM
      const times: AquaEventTime[] = eventsData.events.map((evt: any) => {
        // Extract base event from event_id
        const parts = evt.event_id.split('_');
        const baseEvent = parts.length >= 4 ? `${parts[1]}_${parts[2]}_${parts[3]}` : evt.event_id;
        const timesByCourse = existingTimesMap[baseEvent] || {};
        return {
          event_id: evt.event_id,
          event_display: evt.event_display,
          gender: evt.gender,
          selectedCourse: 'LCM',
          time_string: timesByCourse['LCM'] || '',
          timesByCourse: timesByCourse
        };
      });

      setAquaTimes(times);
    } catch (err: any) {
      console.error('Load AQUA data error:', err);
      setError('Failed to load AQUA data: ' + err.message);
      setAquaTimes([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAquaTimeChange = (eventId: string, value: string) => {
    setAquaTimes(prev =>
      prev.map(t => {
        if (t.event_id === eventId) {
          const newTimesByCourse = { ...t.timesByCourse, [t.selectedCourse]: value };
          return { ...t, time_string: value, timesByCourse: newTimesByCourse };
        }
        return t;
      })
    );
  };

  const handleAquaCourseChange = (eventId: string, newCourse: string) => {
    setAquaTimes(prev =>
      prev.map(t => {
        if (t.event_id === eventId) {
          return {
            ...t,
            selectedCourse: newCourse,
            time_string: t.timesByCourse[newCourse] || ''
          };
        }
        return t;
      })
    );
  };

  const saveAquaTimes = async () => {
    setLoading(true);
    try {
      // Group times by course for batch saving
      const timesByCourse: Record<string, { event_id: string; time_string: string }[]> = {};

      for (const t of aquaTimes) {
        // Save any course that has a non-empty time
        for (const [course, timeStr] of Object.entries(t.timesByCourse)) {
          if (timeStr && timeStr.trim() !== '') {
            if (!timesByCourse[course]) {
              timesByCourse[course] = [];
            }
            timesByCourse[course].push({ event_id: t.event_id, time_string: timeStr });
          }
        }
      }

      let totalUpdated = 0;
      let totalInserted = 0;

      // Save each course group
      for (const [course, times] of Object.entries(timesByCourse)) {
        const response = await fetch(`${API_BASE}/api/admin/aqua-base-times`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ year: aquaYear, course, times })
        });

        const result = await response.json();
        if (result.success) {
          totalUpdated += result.updated;
          totalInserted += result.inserted;
        }
      }

      setMessage(`Saved ${totalUpdated} updated, ${totalInserted} inserted for AQUA times`);
      setShowAquaModal(false);
    } catch (err: any) {
      setError('Failed to save: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Canada On Track Functions (modeled after MAP)
  const loadCanadaData = async (year: number = canadaYear) => {
    setLoading(true);
    setError('');
    try {
      // Get Canada times for this year
      const timesRes = await fetch(`${API_BASE}/api/admin/canada-on-track?year=${year}`);
      if (!timesRes.ok) {
        throw new Error(`Canada times API returned ${timesRes.status}`);
      }
      const timesData = await timesRes.json();

      // Store available years
      setAvailableCanadaYears(timesData.available_years || []);

      // Create a map of existing times by event_id, track, and age
      // Key format: "event_id" -> { "track_age": time_string }
      const existingTimesMap: Record<string, Record<string, string>> = {};
      const eventAgesMap: Record<string, Set<number>> = {};  // Track available ages per event
      const eventTracksByAge: Record<string, Record<number, Set<number>>> = {};  // event -> age -> tracks

      for (const t of timesData.times || []) {
        if (!existingTimesMap[t.event_id]) {
          existingTimesMap[t.event_id] = {};
          eventAgesMap[t.event_id] = new Set();
          eventTracksByAge[t.event_id] = {};
        }
        const key = `${t.canada_track}_${t.canada_track_age}`;
        existingTimesMap[t.event_id][key] = t.time_string;
        eventAgesMap[t.event_id].add(t.canada_track_age);

        // Track which tracks are available for each age
        if (!eventTracksByAge[t.event_id][t.canada_track_age]) {
          eventTracksByAge[t.event_id][t.canada_track_age] = new Set();
        }
        eventTracksByAge[t.event_id][t.canada_track_age].add(t.canada_track);
      }

      // Get unique events from the data
      const uniqueEvents = new Map<string, { event_display: string; gender: string }>();
      for (const t of timesData.times || []) {
        if (!uniqueEvents.has(t.event_id)) {
          const parts = t.event_id.split('_');
          if (parts.length >= 4) {
            const stroke = parts[1];
            const distance = parts[2];
            const gender = parts[3];
            uniqueEvents.set(t.event_id, {
              event_display: `${distance} ${stroke}`,
              gender: gender
            });
          }
        }
      }

      // Build the times array, default to first available age and first available track for that age
      const times: CanadaEventTime[] = Array.from(uniqueEvents.entries()).map(([event_id, info]) => {
        const timesByTrackAge = existingTimesMap[event_id] || {};
        const availableAges = Array.from(eventAgesMap[event_id] || []).sort((a, b) => a - b);
        const defaultAge = availableAges[0] || 16;

        // Build tracksByAge map (convert Sets to sorted arrays)
        const tracksByAge: Record<number, number[]> = {};
        for (const [age, tracks] of Object.entries(eventTracksByAge[event_id] || {})) {
          tracksByAge[parseInt(age)] = Array.from(tracks).sort((a, b) => a - b);
        }

        // Get first available track for the default age
        const availableTracksForAge = tracksByAge[defaultAge] || [1];
        const defaultTrack = availableTracksForAge[0];
        const defaultKey = `${defaultTrack}_${defaultAge}`;

        return {
          event_id,
          event_display: info.event_display,
          gender: info.gender,
          selectedTrack: defaultTrack,
          selectedAge: defaultAge,
          time_string: timesByTrackAge[defaultKey] || '',
          timesByTrackAge: timesByTrackAge,
          availableAges: availableAges,
          tracksByAge: tracksByAge
        };
      });

      // Sort by stroke order (Free, Back, Breast, Fly, Medley), then distance (short to long)
      const strokeOrder: Record<string, number> = { 'Free': 1, 'Back': 2, 'Breast': 3, 'Fly': 4, 'Medley': 5 };
      times.sort((a, b) => {
        // Parse event_display: "100 Free" -> distance=100, stroke=Free
        const [distA, strokeA] = a.event_display.split(' ');
        const [distB, strokeB] = b.event_display.split(' ');
        const strokeOrderA = strokeOrder[strokeA] || 99;
        const strokeOrderB = strokeOrder[strokeB] || 99;
        if (strokeOrderA !== strokeOrderB) return strokeOrderA - strokeOrderB;
        return parseInt(distA) - parseInt(distB);
      });

      setCanadaTimes(times);
    } catch (err: any) {
      console.error('Load Canada data error:', err);
      setError('Failed to load Canada data: ' + err.message);
      setCanadaTimes([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCanadaTimeChange = (eventId: string, value: string) => {
    setCanadaTimes(prev =>
      prev.map(t => {
        if (t.event_id === eventId) {
          const key = `${t.selectedTrack}_${t.selectedAge}`;
          const newTimesByTrackAge = { ...t.timesByTrackAge, [key]: value };
          return { ...t, time_string: value, timesByTrackAge: newTimesByTrackAge };
        }
        return t;
      })
    );
  };

  const handleCanadaTrackChange = (eventId: string, newTrack: number) => {
    setCanadaTimes(prev =>
      prev.map(t => {
        if (t.event_id === eventId) {
          const key = `${newTrack}_${t.selectedAge}`;
          return {
            ...t,
            selectedTrack: newTrack,
            time_string: t.timesByTrackAge[key] || ''
          };
        }
        return t;
      })
    );
  };

  const handleCanadaAgeChange = (eventId: string, newAge: number) => {
    setCanadaTimes(prev =>
      prev.map(t => {
        if (t.event_id === eventId) {
          // Get available tracks for the new age, default to first one
          const availableTracks = t.tracksByAge[newAge] || [1];
          const newTrack = availableTracks.includes(t.selectedTrack) ? t.selectedTrack : availableTracks[0];
          const key = `${newTrack}_${newAge}`;
          return {
            ...t,
            selectedAge: newAge,
            selectedTrack: newTrack,
            time_string: t.timesByTrackAge[key] || ''
          };
        }
        return t;
      })
    );
  };

  const saveCanadaTimes = async () => {
    setLoading(true);
    try {
      // Collect all times grouped by track_age key
      const timesToSave: { event_id: string; track: number; age: number; time_string: string }[] = [];

      for (const t of canadaTimes) {
        for (const [key, timeStr] of Object.entries(t.timesByTrackAge)) {
          if (timeStr && timeStr.trim() !== '') {
            const [trackStr, ageStr] = key.split('_');
            timesToSave.push({
              event_id: t.event_id,
              track: parseInt(trackStr),
              age: parseInt(ageStr),
              time_string: timeStr
            });
          }
        }
      }

      const response = await fetch(`${API_BASE}/api/admin/canada-on-track`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ year: canadaYear, times: timesToSave })
      });

      const result = await response.json();
      if (result.success) {
        setMessage(`Saved ${result.updated} updated, ${result.inserted} inserted for Canada On Track`);
        setShowCanadaModal(false);
      } else {
        setError('Failed to save: ' + (result.detail || 'Unknown error'));
      }
    } catch (err: any) {
      setError('Failed to save: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Split Canada times by gender (like MAP)
  const maleCanadaTimes = canadaTimes.filter(t => t.gender === 'M');
  const femaleCanadaTimes = canadaTimes.filter(t => t.gender === 'F');

  // Handle Enter key - Canada (like MAP)
  const handleCanadaKeyDown = (e: React.KeyboardEvent<HTMLInputElement>, currentEventId: string, gender: string) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const currentList = gender === 'M' ? maleCanadaTimes : femaleCanadaTimes;
      const currentIndex = currentList.findIndex(t => t.event_id === currentEventId);

      if (currentIndex < currentList.length - 1) {
        const nextEventId = currentList[currentIndex + 1].event_id;
        const nextInput = document.querySelector(`input[data-canada-event-id="${nextEventId}"]`) as HTMLInputElement;
        if (nextInput) {
          nextInput.focus();
          nextInput.select();
          return;
        }
      }

      if (gender === 'M' && femaleCanadaTimes.length > 0) {
        const firstFemaleInput = document.querySelector(`input[data-canada-event-id="${femaleCanadaTimes[0].event_id}"]`) as HTMLInputElement;
        if (firstFemaleInput) {
          firstFemaleInput.focus();
          firstFemaleInput.select();
        }
      }
    }
  };

  // MOT Base Times Functions
  const loadMotData = async () => {
    setLoading(true);
    setError('');
    try {
      // Get existing MOT times
      const timesRes = await fetch(`${API_BASE}/api/admin/mot-base-times`);
      if (!timesRes.ok) {
        throw new Error(`MOT times API returned ${timesRes.status}`);
      }
      const timesData = await timesRes.json();

      // Create a map of existing times by event_id and age
      const existingTimesMap: Record<string, Record<number, string>> = {};
      const eventInfoMap: Record<string, { event_display: string; gender: string; is_50m: boolean }> = {};

      for (const t of timesData.times || []) {
        if (!existingTimesMap[t.event_id]) {
          existingTimesMap[t.event_id] = {};
          eventInfoMap[t.event_id] = {
            event_display: t.event_display,
            gender: t.gender,
            is_50m: t.is_50m
          };
        }
        existingTimesMap[t.event_id][t.age] = t.time_string;
      }

      // Build the times array with all events
      const times: MotEventTime[] = Object.entries(eventInfoMap).map(([event_id, info]) => {
        const timesByAge = existingTimesMap[event_id] || {};
        const defaultAge = info.is_50m ? 18 : 15;
        return {
          event_id,
          event_display: info.event_display,
          gender: info.gender,
          is_50m: info.is_50m,
          selectedAge: defaultAge,
          time_string: timesByAge[defaultAge] || '',
          timesByAge: timesByAge
        };
      });

      // Sort by gender, then stroke order (Free, Back, Breast, Fly, Medley), then distance
      const strokeOrder: Record<string, number> = { 'Free': 1, 'Back': 2, 'Breast': 3, 'Fly': 4, 'Medley': 5 };
      times.sort((a, b) => {
        if (a.gender !== b.gender) return a.gender.localeCompare(b.gender);
        // Parse event_display: "100 Free" -> distance=100, stroke=Free
        const [distA, strokeA] = a.event_display.split(' ');
        const [distB, strokeB] = b.event_display.split(' ');
        const strokeOrderA = strokeOrder[strokeA] || 99;
        const strokeOrderB = strokeOrder[strokeB] || 99;
        if (strokeOrderA !== strokeOrderB) return strokeOrderA - strokeOrderB;
        return parseInt(distA) - parseInt(distB);
      });

      setMotTimes(times);
    } catch (err: any) {
      console.error('Load MOT data error:', err);
      setError('Failed to load MOT data: ' + err.message);
      setMotTimes([]);
    } finally {
      setLoading(false);
    }
  };

  const handleMotTimeChange = (eventId: string, value: string) => {
    setMotTimes(prev =>
      prev.map(t => {
        if (t.event_id === eventId) {
          const newTimesByAge = { ...t.timesByAge, [t.selectedAge]: value };
          return { ...t, time_string: value, timesByAge: newTimesByAge };
        }
        return t;
      })
    );
  };

  const handleMotAgeChange = (eventId: string, newAge: number) => {
    setMotTimes(prev =>
      prev.map(t => {
        if (t.event_id === eventId) {
          return {
            ...t,
            selectedAge: newAge,
            time_string: t.timesByAge[newAge] || ''
          };
        }
        return t;
      })
    );
  };

  const saveMotTimes = async () => {
    setLoading(true);
    try {
      // Collect all times to save
      const timesToSave: { event_id: string; age: number; time_string: string }[] = [];

      for (const t of motTimes) {
        for (const [ageStr, timeStr] of Object.entries(t.timesByAge)) {
          const age = parseInt(ageStr);
          if (timeStr && timeStr.trim() !== '') {
            timesToSave.push({ event_id: t.event_id, age, time_string: timeStr });
          }
        }
      }

      const response = await fetch(`${API_BASE}/api/admin/mot-base-times`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ times: timesToSave })
      });

      const result = await response.json();
      if (result.success) {
        setMessage(`Saved ${result.updated} updated, ${result.inserted} inserted for MOT times`);
        setShowMotModal(false);
      } else {
        setError('Failed to save: ' + (result.detail || 'Unknown error'));
      }
    } catch (err: any) {
      setError('Failed to save: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Split MOT times by gender
  const maleMotTimes = motTimes.filter(t => t.gender === 'M');
  const femaleMotTimes = motTimes.filter(t => t.gender === 'F');

  // Handle Enter key - MOT
  const handleMotKeyDown = (e: React.KeyboardEvent<HTMLInputElement>, currentEventId: string, gender: string) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const currentList = gender === 'M' ? maleMotTimes : femaleMotTimes;
      const currentIndex = currentList.findIndex(t => t.event_id === currentEventId);

      if (currentIndex < currentList.length - 1) {
        const nextEventId = currentList[currentIndex + 1].event_id;
        const nextInput = document.querySelector(`input[data-mot-event-id="${nextEventId}"]`) as HTMLInputElement;
        if (nextInput) {
          nextInput.focus();
          nextInput.select();
          return;
        }
      }

      if (gender === 'M' && femaleMotTimes.length > 0) {
        const firstFemaleInput = document.querySelector(`input[data-mot-event-id="${femaleMotTimes[0].event_id}"]`) as HTMLInputElement;
        if (firstFemaleInput) {
          firstFemaleInput.focus();
          firstFemaleInput.select();
        }
      }
    }
  };

  const buttonStyle = {
    padding: '2px 10px',
    backgroundColor: '#cc0000',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '0.9em',
    cursor: 'pointer',
    whiteSpace: 'nowrap' as const,
    display: 'inline-block',
    minWidth: '180px',
    textAlign: 'center' as const,
  };

  const wideButtonStyle = {
    ...buttonStyle,
    width: '250px',
  };

  // Split times by gender for display - Podium
  const maleTimes = podiumTimes.filter(t => t.gender === 'M');
  const femaleTimes = podiumTimes.filter(t => t.gender === 'F');

  // Split times by gender for display - MAP (exclude 50m events)
  const maleMapTimes = mapTimes.filter(t => t.gender === 'M' && !t.event_display.startsWith('50 '));
  const femaleMapTimes = mapTimes.filter(t => t.gender === 'F' && !t.event_display.startsWith('50 '));

  // Handle Enter key to move to next input - Podium
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>, currentEventId: string, gender: string) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const currentList = gender === 'M' ? maleTimes : femaleTimes;
      const currentIndex = currentList.findIndex(t => t.event_id === currentEventId);

      // Try next in same column
      if (currentIndex < currentList.length - 1) {
        const nextEventId = currentList[currentIndex + 1].event_id;
        const nextInput = document.querySelector(`input[data-event-id="${nextEventId}"]`) as HTMLInputElement;
        if (nextInput) {
          nextInput.focus();
          nextInput.select();
          return;
        }
      }

      // If at end of male column, jump to first female
      if (gender === 'M' && femaleTimes.length > 0) {
        const firstFemaleInput = document.querySelector(`input[data-event-id="${femaleTimes[0].event_id}"]`) as HTMLInputElement;
        if (firstFemaleInput) {
          firstFemaleInput.focus();
          firstFemaleInput.select();
        }
      }
    }
  };

  // Handle Enter key to move to next input - MAP
  const handleMapKeyDown = (e: React.KeyboardEvent<HTMLInputElement>, currentEventId: string, gender: string) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const currentList = gender === 'M' ? maleMapTimes : femaleMapTimes;
      const currentIndex = currentList.findIndex(t => t.event_id === currentEventId);

      // Try next in same column
      if (currentIndex < currentList.length - 1) {
        const nextEventId = currentList[currentIndex + 1].event_id;
        const nextInput = document.querySelector(`input[data-map-event-id="${nextEventId}"]`) as HTMLInputElement;
        if (nextInput) {
          nextInput.focus();
          nextInput.select();
          return;
        }
      }

      // If at end of male column, jump to first female
      if (gender === 'M' && femaleMapTimes.length > 0) {
        const firstFemaleInput = document.querySelector(`input[data-map-event-id="${femaleMapTimes[0].event_id}"]`) as HTMLInputElement;
        if (firstFemaleInput) {
          firstFemaleInput.focus();
          firstFemaleInput.select();
        }
      }
    }
  };

  // Split times by gender for display - AQUA
  const maleAquaTimes = aquaTimes.filter(t => t.gender === 'M');
  const femaleAquaTimes = aquaTimes.filter(t => t.gender === 'F');

  // Handle Enter key to move to next input - AQUA
  const handleAquaKeyDown = (e: React.KeyboardEvent<HTMLInputElement>, currentEventId: string, gender: string) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const currentList = gender === 'M' ? maleAquaTimes : femaleAquaTimes;
      const currentIndex = currentList.findIndex(t => t.event_id === currentEventId);

      // Try next in same column
      if (currentIndex < currentList.length - 1) {
        const nextEventId = currentList[currentIndex + 1].event_id;
        const nextInput = document.querySelector(`input[data-aqua-event-id="${nextEventId}"]`) as HTMLInputElement;
        if (nextInput) {
          nextInput.focus();
          nextInput.select();
          return;
        }
      }

      // If at end of male column, jump to first female
      if (gender === 'M' && femaleAquaTimes.length > 0) {
        const firstFemaleInput = document.querySelector(`input[data-aqua-event-id="${femaleAquaTimes[0].event_id}"]`) as HTMLInputElement;
        if (firstFemaleInput) {
          firstFemaleInput.focus();
          firstFemaleInput.select();
        }
      }
    }
  };

  return (
    <div>
      {error && (
        <div style={{ padding: '0.75rem', marginBottom: '1rem', backgroundColor: '#fef2f2', color: '#7f1d1d', fontSize: '0.875rem', borderRadius: '4px' }}>
          [ERROR] {error}
        </div>
      )}

      {message && (
        <div style={{ padding: '0.75rem', marginBottom: '1rem', backgroundColor: '#f0fdf4', color: '#166534', fontSize: '0.875rem', borderRadius: '4px' }}>
          {message}
        </div>
      )}

      {/* Export Buttons Row */}
      <div style={{ marginTop: '1.5rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <button onClick={() => handleExport('map')} style={buttonStyle}>
          Export MAP Table
        </button>

        <button onClick={() => handleExport('mot')} style={buttonStyle}>
          Export MOT Table
        </button>

        <button onClick={() => handleExport('aqua')} style={buttonStyle}>
          Export AQUA Table
        </button>

        <button onClick={() => handleExport('podium')} style={wideButtonStyle}>
          Export Podium Target Times Table
        </button>

        <button onClick={() => handleExport('canada')} style={wideButtonStyle}>
          Export Canada On Track Table
        </button>
      </div>

      {/* Update Buttons Row */}
      <div style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <button onClick={() => handleUpdate('map')} style={buttonStyle}>
          Update MAP Table
        </button>

        <button onClick={() => handleUpdate('mot')} style={buttonStyle}>
          Update MOT Table
        </button>

        <button onClick={() => handleUpdate('aqua')} style={buttonStyle}>
          Update AQUA Table
        </button>

        <button onClick={() => handleUpdate('podium')} style={wideButtonStyle}>
          Update Podium Target Times Table
        </button>

        <button onClick={() => handleUpdate('canada')} style={wideButtonStyle}>
          Update Canada On Track Table
        </button>
      </div>

      {/* Podium Target Times Modal */}
      {showPodiumModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '1.5rem',
            maxWidth: '90vw',
            maxHeight: '90vh',
            overflow: 'auto',
            minWidth: '800px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h2 style={{ margin: 0, fontSize: '1.25rem' }}>Update Podium Target Times</h2>
              <button
                onClick={() => setShowPodiumModal(false)}
                style={{ background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer' }}
              >
                x
              </button>
            </div>

            {/* Year Selector */}
            <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <label style={{ fontWeight: 'bold' }}>SEA Games Year:</label>
              <select
                value={podiumYear}
                onChange={(e) => {
                  const year = parseInt(e.target.value);
                  loadTimesForYear(year);
                }}
                style={{ padding: '0.25rem 0.5rem', border: '1px solid #ccc', borderRadius: '4px', fontSize: '0.9rem' }}
              >
                {seaGamesYears.map(year => (
                  <option key={year} value={year}>
                    {year} {availableYears.includes(year) ? '(has data)' : ''}
                  </option>
                ))}
              </select>
              {availableYears.length > 0 && (
                <span style={{ color: '#666', fontSize: '0.875rem' }}>
                  Years with data: {availableYears.join(', ')}
                </span>
              )}
            </div>

            {error && (
              <div style={{ padding: '0.75rem', marginBottom: '1rem', backgroundColor: '#fef2f2', color: '#7f1d1d', fontSize: '0.875rem', borderRadius: '4px' }}>
                [ERROR] {error}
              </div>
            )}

            {loading ? (
              <div style={{ padding: '2rem', textAlign: 'center' }}>Loading events from backend...</div>
            ) : podiumTimes.length === 0 ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>
                No events loaded. Check that the backend is running on port 8000.
              </div>
            ) : (
              <div style={{ display: 'flex', gap: '2rem' }}>
                {/* Male Events */}
                <div style={{ flex: 1 }}>
                  <h3 style={{ marginTop: 0, borderBottom: '2px solid #cc0000', paddingBottom: '0.5rem' }}>Male Events</h3>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                    <thead>
                      <tr style={{ backgroundColor: '#f3f4f6' }}>
                        <th style={{ padding: '0.5rem', textAlign: 'left', borderBottom: '1px solid #ddd' }}>Event</th>
                        <th style={{ padding: '0.5rem', textAlign: 'left', borderBottom: '1px solid #ddd' }}>3rd Place {podiumYear}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {maleTimes.map(t => (
                        <tr key={t.event_id}>
                          <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee' }}>{t.event_display}</td>
                          <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee' }}>
                            <input
                              type="text"
                              data-event-id={t.event_id}
                              value={t.time_string}
                              onChange={(e) => handleTimeChange(t.event_id, e.target.value)}
                              onKeyDown={(e) => handleKeyDown(e, t.event_id, 'M')}
                              placeholder="0:00.00"
                              style={{ width: '80px', padding: '0.125rem 0.25rem', border: '1px solid #ccc', borderRadius: '2px' }}
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Female Events */}
                <div style={{ flex: 1 }}>
                  <h3 style={{ marginTop: 0, borderBottom: '2px solid #cc0000', paddingBottom: '0.5rem' }}>Female Events</h3>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                    <thead>
                      <tr style={{ backgroundColor: '#f3f4f6' }}>
                        <th style={{ padding: '0.5rem', textAlign: 'left', borderBottom: '1px solid #ddd' }}>Event</th>
                        <th style={{ padding: '0.5rem', textAlign: 'left', borderBottom: '1px solid #ddd' }}>3rd Place {podiumYear}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {femaleTimes.map(t => (
                        <tr key={t.event_id}>
                          <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee' }}>{t.event_display}</td>
                          <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee' }}>
                            <input
                              type="text"
                              data-event-id={t.event_id}
                              value={t.time_string}
                              onChange={(e) => handleTimeChange(t.event_id, e.target.value)}
                              onKeyDown={(e) => handleKeyDown(e, t.event_id, 'F')}
                              placeholder="0:00.00"
                              style={{ width: '80px', padding: '0.125rem 0.25rem', border: '1px solid #ccc', borderRadius: '2px' }}
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
              <button
                onClick={() => setShowPodiumModal(false)}
                style={{ padding: '0.5rem 1rem', border: '1px solid #ccc', borderRadius: '4px', cursor: 'pointer' }}
              >
                Cancel
              </button>
              <button
                onClick={savePodiumTimes}
                disabled={loading}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: '#cc0000',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  opacity: loading ? 0.6 : 1
                }}
              >
                Save Times
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MAP Base Times Modal */}
      {showMapModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '1.5rem',
            maxWidth: '90vw',
            maxHeight: '90vh',
            overflow: 'auto',
            minWidth: '800px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h2 style={{ margin: 0, fontSize: '1.25rem' }}>Update MAP Base Times</h2>
              <button
                onClick={() => setShowMapModal(false)}
                style={{ background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer' }}
              >
                x
              </button>
            </div>

            {/* Year Selector */}
            <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <label style={{ fontWeight: 'bold' }}>100th All Time USA Year:</label>
              <select
                value={mapYear}
                onChange={(e) => {
                  const year = parseInt(e.target.value);
                  setMapYear(year);
                  loadMapData(year);
                }}
                style={{ padding: '0.25rem 0.5rem', border: '1px solid #ccc', borderRadius: '4px', fontSize: '0.9rem' }}
              >
                {mapYearOptions.map(year => (
                  <option key={year} value={year}>
                    {year} {availableMapYears.includes(year) ? '(has data)' : ''}
                  </option>
                ))}
              </select>
              {availableMapYears.length > 0 && (
                <span style={{ color: '#666', fontSize: '0.875rem' }}>
                  Years with data: {availableMapYears.join(', ')}
                </span>
              )}
            </div>

            {error && (
              <div style={{ padding: '0.75rem', marginBottom: '1rem', backgroundColor: '#fef2f2', color: '#7f1d1d', fontSize: '0.875rem', borderRadius: '4px' }}>
                [ERROR] {error}
              </div>
            )}

            {loading ? (
              <div style={{ padding: '2rem', textAlign: 'center' }}>Loading events from backend...</div>
            ) : mapTimes.length === 0 ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>
                No events loaded. Check that the backend is running on port 8000.
              </div>
            ) : (
              <div style={{ display: 'flex', gap: '2rem' }}>
                {/* Male Events */}
                <div style={{ flex: 1 }}>
                  <h3 style={{ marginTop: 0, borderBottom: '2px solid #cc0000', paddingBottom: '0.5rem' }}>Male Events</h3>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                    <thead>
                      <tr style={{ backgroundColor: '#f3f4f6' }}>
                        <th style={{ padding: '0.5rem', textAlign: 'left', borderBottom: '1px solid #ddd', width: '45%' }}>Event</th>
                        <th style={{ padding: '0.5rem', textAlign: 'center', borderBottom: '1px solid #ddd', width: '20%' }}>Age</th>
                        <th style={{ padding: '0.5rem', textAlign: 'left', borderBottom: '1px solid #ddd', width: '35%' }}>Base Time</th>
                      </tr>
                    </thead>
                    <tbody>
                      {maleMapTimes.map(t => (
                        <tr key={t.event_id}>
                          <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee' }}>{t.event_display}</td>
                          <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee', textAlign: 'center' }}>
                            <select
                              value={t.selectedAge}
                              onChange={(e) => handleMapAgeChange(t.event_id, parseInt(e.target.value))}
                              style={{
                                padding: '0.125rem 0.25rem',
                                border: '1px solid #ccc',
                                borderRadius: '2px',
                                backgroundColor: '#cc0000',
                                color: 'white',
                                fontWeight: 'bold',
                                fontSize: '0.8rem',
                                cursor: 'pointer'
                              }}
                            >
                              {mapAges.map(age => (
                                <option key={age} value={age}>{age}</option>
                              ))}
                            </select>
                          </td>
                          <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee' }}>
                            <input
                              type="text"
                              data-map-event-id={t.event_id}
                              value={t.time_string}
                              onChange={(e) => handleMapTimeChange(t.event_id, e.target.value)}
                              onKeyDown={(e) => handleMapKeyDown(e, t.event_id, 'M')}
                              placeholder="0:00.00"
                              style={{ width: '80px', padding: '0.125rem 0.25rem', border: '1px solid #ccc', borderRadius: '2px' }}
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Female Events */}
                <div style={{ flex: 1 }}>
                  <h3 style={{ marginTop: 0, borderBottom: '2px solid #cc0000', paddingBottom: '0.5rem' }}>Female Events</h3>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                    <thead>
                      <tr style={{ backgroundColor: '#f3f4f6' }}>
                        <th style={{ padding: '0.5rem', textAlign: 'left', borderBottom: '1px solid #ddd', width: '45%' }}>Event</th>
                        <th style={{ padding: '0.5rem', textAlign: 'center', borderBottom: '1px solid #ddd', width: '20%' }}>Age</th>
                        <th style={{ padding: '0.5rem', textAlign: 'left', borderBottom: '1px solid #ddd', width: '35%' }}>Base Time</th>
                      </tr>
                    </thead>
                    <tbody>
                      {femaleMapTimes.map(t => (
                        <tr key={t.event_id}>
                          <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee' }}>{t.event_display}</td>
                          <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee', textAlign: 'center' }}>
                            <select
                              value={t.selectedAge}
                              onChange={(e) => handleMapAgeChange(t.event_id, parseInt(e.target.value))}
                              style={{
                                padding: '0.125rem 0.25rem',
                                border: '1px solid #ccc',
                                borderRadius: '2px',
                                backgroundColor: '#cc0000',
                                color: 'white',
                                fontWeight: 'bold',
                                fontSize: '0.8rem',
                                cursor: 'pointer'
                              }}
                            >
                              {mapAges.map(age => (
                                <option key={age} value={age}>{age}</option>
                              ))}
                            </select>
                          </td>
                          <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee' }}>
                            <input
                              type="text"
                              data-map-event-id={t.event_id}
                              value={t.time_string}
                              onChange={(e) => handleMapTimeChange(t.event_id, e.target.value)}
                              onKeyDown={(e) => handleMapKeyDown(e, t.event_id, 'F')}
                              placeholder="0:00.00"
                              style={{ width: '80px', padding: '0.125rem 0.25rem', border: '1px solid #ccc', borderRadius: '2px' }}
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
              <button
                onClick={() => setShowMapModal(false)}
                style={{ padding: '0.5rem 1rem', border: '1px solid #ccc', borderRadius: '4px', cursor: 'pointer' }}
              >
                Cancel
              </button>
              <button
                onClick={saveMapTimes}
                disabled={loading}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: '#cc0000',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  opacity: loading ? 0.6 : 1
                }}
              >
                Save Times
              </button>
            </div>
          </div>
        </div>
      )}

      {/* AQUA Base Times Modal */}
      {showAquaModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '1.5rem',
            maxWidth: '90vw',
            maxHeight: '90vh',
            overflow: 'auto',
            minWidth: '800px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h2 style={{ margin: 0, fontSize: '1.25rem' }}>Update AQUA Base Times</h2>
              <button
                onClick={() => setShowAquaModal(false)}
                style={{ background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer' }}
              >
                x
              </button>
            </div>

            {/* Year Selector */}
            <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <label style={{ fontWeight: 'bold' }}>AQUA Points Year:</label>
              <select
                value={aquaYear}
                onChange={(e) => {
                  const year = parseInt(e.target.value);
                  setAquaYear(year);
                  loadAquaData(year);
                }}
                style={{ padding: '0.25rem 0.5rem', border: '1px solid #ccc', borderRadius: '4px', fontSize: '0.9rem' }}
              >
                {aquaYearOptions.map(year => (
                  <option key={year} value={year}>
                    {year} {availableAquaYears.includes(year) ? '(has data)' : ''}
                  </option>
                ))}
              </select>
              {availableAquaCourses.length > 0 && (
                <span style={{ color: '#666', fontSize: '0.875rem' }}>
                  Courses with data: {availableAquaCourses.join(', ')}
                </span>
              )}
            </div>

            {error && (
              <div style={{ padding: '0.75rem', marginBottom: '1rem', backgroundColor: '#fef2f2', color: '#7f1d1d', fontSize: '0.875rem', borderRadius: '4px' }}>
                [ERROR] {error}
              </div>
            )}

            {loading ? (
              <div style={{ padding: '2rem', textAlign: 'center' }}>Loading events from backend...</div>
            ) : aquaTimes.length === 0 ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>
                No events loaded. Check that the backend is running on port 8000.
              </div>
            ) : (
              <div style={{ display: 'flex', gap: '2rem' }}>
                {/* Male Events */}
                <div style={{ flex: 1 }}>
                  <h3 style={{ marginTop: 0, borderBottom: '2px solid #cc0000', paddingBottom: '0.5rem' }}>Male Events</h3>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                    <thead>
                      <tr style={{ backgroundColor: '#f3f4f6' }}>
                        <th style={{ padding: '0.5rem', textAlign: 'left', borderBottom: '1px solid #ddd', width: '45%' }}>Event</th>
                        <th style={{ padding: '0.5rem', textAlign: 'center', borderBottom: '1px solid #ddd', width: '20%' }}>Course</th>
                        <th style={{ padding: '0.5rem', textAlign: 'left', borderBottom: '1px solid #ddd', width: '35%' }}>Base Time</th>
                      </tr>
                    </thead>
                    <tbody>
                      {maleAquaTimes.map(t => (
                        <tr key={t.event_id}>
                          <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee' }}>{t.event_display}</td>
                          <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee', textAlign: 'center' }}>
                            <select
                              value={t.selectedCourse}
                              onChange={(e) => handleAquaCourseChange(t.event_id, e.target.value)}
                              style={{
                                padding: '0.125rem 0.25rem',
                                border: '1px solid #ccc',
                                borderRadius: '2px',
                                backgroundColor: '#cc0000',
                                color: 'white',
                                fontWeight: 'bold',
                                fontSize: '0.8rem',
                                cursor: 'pointer'
                              }}
                            >
                              {aquaCourseOptions.map(course => (
                                <option key={course} value={course}>{course}</option>
                              ))}
                            </select>
                          </td>
                          <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee' }}>
                            <input
                              type="text"
                              data-aqua-event-id={t.event_id}
                              value={t.time_string}
                              onChange={(e) => handleAquaTimeChange(t.event_id, e.target.value)}
                              onKeyDown={(e) => handleAquaKeyDown(e, t.event_id, 'M')}
                              placeholder="0:00.00"
                              style={{ width: '80px', padding: '0.125rem 0.25rem', border: '1px solid #ccc', borderRadius: '2px' }}
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Female Events */}
                <div style={{ flex: 1 }}>
                  <h3 style={{ marginTop: 0, borderBottom: '2px solid #cc0000', paddingBottom: '0.5rem' }}>Female Events</h3>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                    <thead>
                      <tr style={{ backgroundColor: '#f3f4f6' }}>
                        <th style={{ padding: '0.5rem', textAlign: 'left', borderBottom: '1px solid #ddd', width: '45%' }}>Event</th>
                        <th style={{ padding: '0.5rem', textAlign: 'center', borderBottom: '1px solid #ddd', width: '20%' }}>Course</th>
                        <th style={{ padding: '0.5rem', textAlign: 'left', borderBottom: '1px solid #ddd', width: '35%' }}>Base Time</th>
                      </tr>
                    </thead>
                    <tbody>
                      {femaleAquaTimes.map(t => (
                        <tr key={t.event_id}>
                          <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee' }}>{t.event_display}</td>
                          <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee', textAlign: 'center' }}>
                            <select
                              value={t.selectedCourse}
                              onChange={(e) => handleAquaCourseChange(t.event_id, e.target.value)}
                              style={{
                                padding: '0.125rem 0.25rem',
                                border: '1px solid #ccc',
                                borderRadius: '2px',
                                backgroundColor: '#cc0000',
                                color: 'white',
                                fontWeight: 'bold',
                                fontSize: '0.8rem',
                                cursor: 'pointer'
                              }}
                            >
                              {aquaCourseOptions.map(course => (
                                <option key={course} value={course}>{course}</option>
                              ))}
                            </select>
                          </td>
                          <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee' }}>
                            <input
                              type="text"
                              data-aqua-event-id={t.event_id}
                              value={t.time_string}
                              onChange={(e) => handleAquaTimeChange(t.event_id, e.target.value)}
                              onKeyDown={(e) => handleAquaKeyDown(e, t.event_id, 'F')}
                              placeholder="0:00.00"
                              style={{ width: '80px', padding: '0.125rem 0.25rem', border: '1px solid #ccc', borderRadius: '2px' }}
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
              <button
                onClick={() => setShowAquaModal(false)}
                style={{ padding: '0.5rem 1rem', border: '1px solid #ccc', borderRadius: '4px', cursor: 'pointer' }}
              >
                Cancel
              </button>
              <button
                onClick={saveAquaTimes}
                disabled={loading}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: '#cc0000',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  opacity: loading ? 0.6 : 1
                }}
              >
                Save Times
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Canada On Track Modal (modeled after MAP) */}
      {showCanadaModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '1.5rem',
            maxWidth: '90vw',
            maxHeight: '90vh',
            overflow: 'auto',
            minWidth: '800px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h2 style={{ margin: 0, fontSize: '1.25rem' }}>Update Canada On Track Times</h2>
              <button
                onClick={() => setShowCanadaModal(false)}
                style={{ background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer' }}
              >
                x
              </button>
            </div>

            {/* Year Selector */}
            <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <label style={{ fontWeight: 'bold' }}>Canada On Track Year:</label>
              <select
                value={canadaYear}
                onChange={(e) => {
                  const year = parseInt(e.target.value);
                  setCanadaYear(year);
                  loadCanadaData(year);
                }}
                style={{ padding: '0.25rem 0.5rem', border: '1px solid #ccc', borderRadius: '4px', fontSize: '0.9rem' }}
              >
                {canadaYearOptions.map(year => (
                  <option key={year} value={year}>
                    {year} {availableCanadaYears.includes(year) ? '(has data)' : ''}
                  </option>
                ))}
              </select>
              {availableCanadaYears.length > 0 && (
                <span style={{ color: '#666', fontSize: '0.875rem' }}>
                  Years with data: {availableCanadaYears.join(', ')}
                </span>
              )}
            </div>

            {error && (
              <div style={{ padding: '0.75rem', marginBottom: '1rem', backgroundColor: '#fef2f2', color: '#7f1d1d', fontSize: '0.875rem', borderRadius: '4px' }}>
                [ERROR] {error}
              </div>
            )}

            {loading ? (
              <div style={{ padding: '2rem', textAlign: 'center' }}>Loading events from backend...</div>
            ) : canadaTimes.length === 0 ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>
                No events loaded. Check that the backend is running on port 8000.
              </div>
            ) : (
              <div style={{ display: 'flex', gap: '2rem' }}>
                {/* Male Events */}
                <div style={{ flex: 1 }}>
                  <h3 style={{ marginTop: 0, borderBottom: '2px solid #cc0000', paddingBottom: '0.5rem' }}>Male Events</h3>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                    <thead>
                      <tr style={{ backgroundColor: '#f3f4f6' }}>
                        <th style={{ padding: '0.5rem', textAlign: 'left', borderBottom: '1px solid #ddd', width: '35%' }}>Event</th>
                        <th style={{ padding: '0.5rem', textAlign: 'center', borderBottom: '1px solid #ddd', width: '15%' }}>Age</th>
                        <th style={{ padding: '0.5rem', textAlign: 'center', borderBottom: '1px solid #ddd', width: '15%' }}>Track</th>
                        <th style={{ padding: '0.5rem', textAlign: 'left', borderBottom: '1px solid #ddd', width: '35%' }}>Time</th>
                      </tr>
                    </thead>
                    <tbody>
                      {maleCanadaTimes.map(t => (
                        <tr key={t.event_id}>
                          <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee' }}>{t.event_display}</td>
                          <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee', textAlign: 'center' }}>
                            <select
                              value={t.selectedAge}
                              onChange={(e) => handleCanadaAgeChange(t.event_id, parseInt(e.target.value))}
                              style={{
                                padding: '0.125rem 0.25rem',
                                border: '1px solid #ccc',
                                borderRadius: '2px',
                                backgroundColor: '#cc0000',
                                color: 'white',
                                fontWeight: 'bold',
                                fontSize: '0.8rem',
                                cursor: 'pointer'
                              }}
                            >
                              {t.availableAges.map(age => (
                                <option key={age} value={age}>{age}</option>
                              ))}
                            </select>
                          </td>
                          <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee', textAlign: 'center' }}>
                            <select
                              value={t.selectedTrack}
                              onChange={(e) => handleCanadaTrackChange(t.event_id, parseInt(e.target.value))}
                              style={{
                                padding: '0.125rem 0.25rem',
                                border: '1px solid #ccc',
                                borderRadius: '2px',
                                backgroundColor: '#cc0000',
                                color: 'white',
                                fontWeight: 'bold',
                                fontSize: '0.8rem',
                                cursor: 'pointer'
                              }}
                            >
                              {(t.tracksByAge[t.selectedAge] || [1, 2, 3]).map(track => (
                                <option key={track} value={track}>{track}</option>
                              ))}
                            </select>
                          </td>
                          <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee' }}>
                            <input
                              type="text"
                              data-canada-event-id={t.event_id}
                              value={t.time_string}
                              onChange={(e) => handleCanadaTimeChange(t.event_id, e.target.value)}
                              onKeyDown={(e) => handleCanadaKeyDown(e, t.event_id, 'M')}
                              placeholder="0:00.00"
                              style={{ width: '80px', padding: '0.125rem 0.25rem', border: '1px solid #ccc', borderRadius: '2px' }}
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Female Events */}
                <div style={{ flex: 1 }}>
                  <h3 style={{ marginTop: 0, borderBottom: '2px solid #cc0000', paddingBottom: '0.5rem' }}>Female Events</h3>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                    <thead>
                      <tr style={{ backgroundColor: '#f3f4f6' }}>
                        <th style={{ padding: '0.5rem', textAlign: 'left', borderBottom: '1px solid #ddd', width: '35%' }}>Event</th>
                        <th style={{ padding: '0.5rem', textAlign: 'center', borderBottom: '1px solid #ddd', width: '15%' }}>Age</th>
                        <th style={{ padding: '0.5rem', textAlign: 'center', borderBottom: '1px solid #ddd', width: '15%' }}>Track</th>
                        <th style={{ padding: '0.5rem', textAlign: 'left', borderBottom: '1px solid #ddd', width: '35%' }}>Time</th>
                      </tr>
                    </thead>
                    <tbody>
                      {femaleCanadaTimes.map(t => (
                        <tr key={t.event_id}>
                          <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee' }}>{t.event_display}</td>
                          <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee', textAlign: 'center' }}>
                            <select
                              value={t.selectedAge}
                              onChange={(e) => handleCanadaAgeChange(t.event_id, parseInt(e.target.value))}
                              style={{
                                padding: '0.125rem 0.25rem',
                                border: '1px solid #ccc',
                                borderRadius: '2px',
                                backgroundColor: '#cc0000',
                                color: 'white',
                                fontWeight: 'bold',
                                fontSize: '0.8rem',
                                cursor: 'pointer'
                              }}
                            >
                              {t.availableAges.map(age => (
                                <option key={age} value={age}>{age}</option>
                              ))}
                            </select>
                          </td>
                          <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee', textAlign: 'center' }}>
                            <select
                              value={t.selectedTrack}
                              onChange={(e) => handleCanadaTrackChange(t.event_id, parseInt(e.target.value))}
                              style={{
                                padding: '0.125rem 0.25rem',
                                border: '1px solid #ccc',
                                borderRadius: '2px',
                                backgroundColor: '#cc0000',
                                color: 'white',
                                fontWeight: 'bold',
                                fontSize: '0.8rem',
                                cursor: 'pointer'
                              }}
                            >
                              {(t.tracksByAge[t.selectedAge] || [1, 2, 3]).map(track => (
                                <option key={track} value={track}>{track}</option>
                              ))}
                            </select>
                          </td>
                          <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee' }}>
                            <input
                              type="text"
                              data-canada-event-id={t.event_id}
                              value={t.time_string}
                              onChange={(e) => handleCanadaTimeChange(t.event_id, e.target.value)}
                              onKeyDown={(e) => handleCanadaKeyDown(e, t.event_id, 'F')}
                              placeholder="0:00.00"
                              style={{ width: '80px', padding: '0.125rem 0.25rem', border: '1px solid #ccc', borderRadius: '2px' }}
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
              <button
                onClick={() => setShowCanadaModal(false)}
                style={{ padding: '0.5rem 1rem', border: '1px solid #ccc', borderRadius: '4px', cursor: 'pointer' }}
              >
                Cancel
              </button>
              <button
                onClick={saveCanadaTimes}
                disabled={loading}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: '#cc0000',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  opacity: loading ? 0.6 : 1
                }}
              >
                Save Times
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MOT Base Times Modal */}
      {showMotModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '1.5rem',
            maxWidth: '90vw',
            maxHeight: '90vh',
            overflow: 'auto',
            minWidth: '800px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h2 style={{ margin: 0, fontSize: '1.25rem' }}>Update MOT Base Times</h2>
              <button
                onClick={() => setShowMotModal(false)}
                style={{ background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer' }}
              >
                x
              </button>
            </div>

            <div style={{ marginBottom: '1rem', color: '#666', fontSize: '0.875rem' }}>
              Ages 15-23 for 100m+ events, Ages 18-23 for 50m events
            </div>

            {error && (
              <div style={{ padding: '0.75rem', marginBottom: '1rem', backgroundColor: '#fef2f2', color: '#7f1d1d', fontSize: '0.875rem', borderRadius: '4px' }}>
                [ERROR] {error}
              </div>
            )}

            {loading ? (
              <div style={{ padding: '2rem', textAlign: 'center' }}>Loading events from backend...</div>
            ) : motTimes.length === 0 ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>
                No events loaded. Check that the backend is running on port 8000.
              </div>
            ) : (
              <div style={{ display: 'flex', gap: '2rem' }}>
                {/* Male Events */}
                <div style={{ flex: 1 }}>
                  <h3 style={{ marginTop: 0, borderBottom: '2px solid #cc0000', paddingBottom: '0.5rem' }}>Male Events</h3>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                    <thead>
                      <tr style={{ backgroundColor: '#f3f4f6' }}>
                        <th style={{ padding: '0.5rem', textAlign: 'left', borderBottom: '1px solid #ddd', width: '45%' }}>Event</th>
                        <th style={{ padding: '0.5rem', textAlign: 'center', borderBottom: '1px solid #ddd', width: '20%' }}>Age</th>
                        <th style={{ padding: '0.5rem', textAlign: 'left', borderBottom: '1px solid #ddd', width: '35%' }}>Target Time</th>
                      </tr>
                    </thead>
                    <tbody>
                      {maleMotTimes.map(t => (
                        <tr key={t.event_id}>
                          <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee' }}>{t.event_display}</td>
                          <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee', textAlign: 'center' }}>
                            <select
                              value={t.selectedAge}
                              onChange={(e) => handleMotAgeChange(t.event_id, parseInt(e.target.value))}
                              style={{
                                padding: '0.125rem 0.25rem',
                                border: '1px solid #ccc',
                                borderRadius: '2px',
                                backgroundColor: '#cc0000',
                                color: 'white',
                                fontWeight: 'bold',
                                fontSize: '0.8rem',
                                cursor: 'pointer'
                              }}
                            >
                              {(t.is_50m ? motAges50m : motAges).map(age => (
                                <option key={age} value={age}>{age}</option>
                              ))}
                            </select>
                          </td>
                          <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee' }}>
                            <input
                              type="text"
                              data-mot-event-id={t.event_id}
                              value={t.time_string}
                              onChange={(e) => handleMotTimeChange(t.event_id, e.target.value)}
                              onKeyDown={(e) => handleMotKeyDown(e, t.event_id, 'M')}
                              placeholder="0:00.00"
                              style={{ width: '80px', padding: '0.125rem 0.25rem', border: '1px solid #ccc', borderRadius: '2px' }}
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Female Events */}
                <div style={{ flex: 1 }}>
                  <h3 style={{ marginTop: 0, borderBottom: '2px solid #cc0000', paddingBottom: '0.5rem' }}>Female Events</h3>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                    <thead>
                      <tr style={{ backgroundColor: '#f3f4f6' }}>
                        <th style={{ padding: '0.5rem', textAlign: 'left', borderBottom: '1px solid #ddd', width: '45%' }}>Event</th>
                        <th style={{ padding: '0.5rem', textAlign: 'center', borderBottom: '1px solid #ddd', width: '20%' }}>Age</th>
                        <th style={{ padding: '0.5rem', textAlign: 'left', borderBottom: '1px solid #ddd', width: '35%' }}>Target Time</th>
                      </tr>
                    </thead>
                    <tbody>
                      {femaleMotTimes.map(t => (
                        <tr key={t.event_id}>
                          <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee' }}>{t.event_display}</td>
                          <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee', textAlign: 'center' }}>
                            <select
                              value={t.selectedAge}
                              onChange={(e) => handleMotAgeChange(t.event_id, parseInt(e.target.value))}
                              style={{
                                padding: '0.125rem 0.25rem',
                                border: '1px solid #ccc',
                                borderRadius: '2px',
                                backgroundColor: '#cc0000',
                                color: 'white',
                                fontWeight: 'bold',
                                fontSize: '0.8rem',
                                cursor: 'pointer'
                              }}
                            >
                              {(t.is_50m ? motAges50m : motAges).map(age => (
                                <option key={age} value={age}>{age}</option>
                              ))}
                            </select>
                          </td>
                          <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee' }}>
                            <input
                              type="text"
                              data-mot-event-id={t.event_id}
                              value={t.time_string}
                              onChange={(e) => handleMotTimeChange(t.event_id, e.target.value)}
                              onKeyDown={(e) => handleMotKeyDown(e, t.event_id, 'F')}
                              placeholder="0:00.00"
                              style={{ width: '80px', padding: '0.125rem 0.25rem', border: '1px solid #ccc', borderRadius: '2px' }}
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
              <button
                onClick={() => setShowMotModal(false)}
                style={{ padding: '0.5rem 1rem', border: '1px solid #ccc', borderRadius: '4px', cursor: 'pointer' }}
              >
                Cancel
              </button>
              <button
                onClick={saveMotTimes}
                disabled={loading}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: '#cc0000',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  opacity: loading ? 0.6 : 1
                }}
              >
                Save Times
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ManualEntry;
