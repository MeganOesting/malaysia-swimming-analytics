/**
 * Meet Management Feature Component
 * Handles file uploads and viewing, editing, and deleting meets
 */

import React, { useState, useCallback, useEffect } from 'react';
import { Meet, UploadSummary, ValidationIssueDetail } from '../../shared/types/admin';
import { Button } from '../../shared/components';
import { useNotification } from '../../shared/hooks';
import * as api from './api';

// Helper function to format dates as dd MMM yyyy (e.g., 20 Nov 2025)
const formatDateDDMMMYYYY = (dateString: string | null | undefined): string => {
  if (!dateString) return '-';
  try {
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

export interface MeetManagementProps {
  isAuthenticated: boolean;
}

// Tab Configuration for Meet Management Feature
export const MEET_MANAGEMENT_TAB_CONFIG = {
  id: 'manage' as const,
  label: 'Meet Management',
  icon: '',
  component: undefined, // Will be set in admin.tsx
};

const ISSUE_LABELS: Record<string, string> = {
  name_format_mismatches: 'Name Format Mismatches',
  club_misses: 'Club Not Found',
  duplicate_athletes: 'Duplicate Athletes',
  invalid_times: 'Invalid Times',
  missing_birthdates: 'Missing Birthdates',
};

export const MeetManagement: React.FC<MeetManagementProps> = ({
  isAuthenticated,
}) => {
  // File upload state
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [fileType, setFileType] = useState<'swimrankings' | 'seag'>('swimrankings');
  const [seagYear, setSeagYear] = useState<string>('2025');
  const [meetCity, setMeetCity] = useState<string>('');
  const [meetName, setMeetName] = useState<string>('');
  const [meetMonth, setMeetMonth] = useState<string>('01');
  const [meetDay, setMeetDay] = useState<string>('01');
  const [uploadSummaries, setUploadSummaries] = useState<UploadSummary[]>([]);
  const [expandedIssueKeys, setExpandedIssueKeys] = useState<Record<string, boolean>>({});

  // Meets state
  const [meets, setMeets] = useState<Meet[]>([]);
  const [loadingMeets, setLoadingMeets] = useState(false);

  // Checkbox filtering state
  const [selectedMeetIds, setSelectedMeetIds] = useState<Set<string>>(new Set());

  // Alias editing state
  const [editingAlias, setEditingAlias] = useState<Record<string, string>>({});

  // Category editing state
  const [editingCategory, setEditingCategory] = useState<Record<string, { participantType: string; scope: string }>>({});

  // Results editing state
  const [editingResultsMeetId, setEditingResultsMeetId] = useState<string | null>(null);
  const [showCompPlaceModal, setShowCompPlaceModal] = useState(false);
  const [meetResults, setMeetResults] = useState<Array<{
    id: string;  // UUID string
    athlete_name: string;
    event_display: string;
    time_string: string;
    comp_place: number | null;
    gender: string;
    result_status: string;  // OK, DQ, DNS, DNF, SCR
  }>>([]);
  const [compPlaceEdits, setCompPlaceEdits] = useState<Record<string, string>>({});
  const [loadingResults, setLoadingResults] = useState(false);
  const [editingMeetName, setEditingMeetName] = useState('');

  // Manual Entry State
  const [showManualEntry, setShowManualEntry] = useState(false);
  const [manualMeetName, setManualMeetName] = useState('');
  const [manualMeetAlias, setManualMeetAlias] = useState('');
  const [manualMeetDate, setManualMeetDate] = useState('');
  const [manualMeetCourse, setManualMeetCourse] = useState<'LCM' | 'SCM'>('LCM');
  const [manualMeetCity, setManualMeetCity] = useState('');
  const [manualMeetId, setManualMeetId] = useState<string | null>(null);

  // Roster state
  const [rosterSearch, setRosterSearch] = useState('');
  const [rosterSearchResults, setRosterSearchResults] = useState<Array<{
    id: number;
    fullname: string;
    birthdate: string;
    gender: string;
  }>>([]);
  const [roster, setRoster] = useState<Array<{
    id: number;
    fullname: string;
    birthdate: string;
    gender: string;
  }>>([]);
  const [selectedRosterAthlete, setSelectedRosterAthlete] = useState<number | null>(null);

  // Event results entry state (for selected athlete)
  const [athleteEventResults, setAthleteEventResults] = useState<Array<{
    event_id: string;
    event_display: string;
    prelim_time: string;
    prelim_place: string;
    final_time: string;
    final_place: string;
  }>>([]);
  const [availableEvents, setAvailableEvents] = useState<Array<{id: string; display: string}>>([]);
  const [selectedEventToAdd, setSelectedEventToAdd] = useState('');

  // Relay splits entry state
  const [showRelayEntry, setShowRelayEntry] = useState(false);
  const [relayEventId, setRelayEventId] = useState('');
  const [relayRound, setRelayRound] = useState<'Prelim' | 'Final'>('Final');
  const [relayPlace, setRelayPlace] = useState('');
  const [relaySplits, setRelaySplits] = useState<Array<{
    leg: number;
    athlete_id: number | null;
    athlete_name: string;
    split_time: string;
  }>>([
    { leg: 1, athlete_id: null, athlete_name: '', split_time: '' },
    { leg: 2, athlete_id: null, athlete_name: '', split_time: '' },
    { leg: 3, athlete_id: null, athlete_name: '', split_time: '' },
    { leg: 4, athlete_id: null, athlete_name: '', split_time: '' },
  ]);
  const [availableRelayEvents, setAvailableRelayEvents] = useState<Array<{id: string; display: string}>>([]);

  // Notifications
  const { notifications, success, error, clear } = useNotification();

  /**
   * Export results table to Excel
   */
  const handleExportResults = useCallback(async () => {
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
      const response = await fetch(`${apiBase}/api/admin/results/export-excel`);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to export results: ${response.status} ${errorText}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'results_export.xlsx';
      // Append to body, click, then remove (fixes download not triggering in some browsers)
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      success('Results exported successfully');
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Export failed';
      error(`Export error: ${errorMsg}`);
      console.error('Export error:', err);
    }
  }, [success, error]);

  /**
   * Export events table to Excel
   */
  const handleExportEvents = useCallback(async () => {
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
      const response = await fetch(`${apiBase}/api/admin/events/export-excel`);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to export events: ${response.status} ${errorText}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'events_export.xlsx';
      // Append to body, click, then remove (fixes download not triggering in some browsers)
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      success('Events exported successfully');
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Export failed';
      error(`Export error: ${errorMsg}`);
      console.error('Export error:', err);
    }
  }, [success, error]);

  /**
   * Handle file selection
   */
  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;

      if (files && files.length > 0) {
        const newFiles = Array.from(files);

        // Add new files to existing ones (avoid duplicates by filename)
        setUploadedFiles(prevFiles => {
          const existingFilenames = new Set(prevFiles.map(f => f.name));
          const uniqueNewFiles = newFiles.filter(
            f => !existingFilenames.has(f.name)
          );
          return [...prevFiles, ...uniqueNewFiles];
        });
      }

      // Reset input to allow re-selecting same file
      e.target.value = '';
    },
    [success]
  );

  /**
   * Remove file from list
   */
  const handleRemoveFile = useCallback((index: number) => {
    setUploadedFiles(prevFiles => prevFiles.filter((_, i) => i !== index));
  }, []);

  /**
   * Upload all files
   */
  const handleUpload = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      if (uploadedFiles.length === 0) {
        error('No files selected. Click "Choose Files" to add Excel files for upload.');
        return;
      }

      if (fileType === 'seag') {
        if (!seagYear || !meetCity || !meetName || !meetMonth || !meetDay) {
          error('For SEAG uploads, the following are required: Year, Meet City, Meet Name, and 1st Day date.');
          return;
        }
      }

      setUploading(true);
      setUploadSummaries(
        uploadedFiles.map(file => ({
          filename: file.name,
          status: 'pending',
          message: 'Waiting to process…',
        }))
      );
      setExpandedIssueKeys({});

      try {
        const summaries = await api.uploadMultipleFiles(
          uploadedFiles,
          fileType,
          seagYear,
          meetCity,
          meetName,
          meetMonth,
          meetDay,
          summary => {
            setUploadSummaries(prev =>
              prev.map(s =>
                s.filename === summary.filename ? summary : s
              )
            );
          }
        );

        setUploadSummaries(summaries);

        const successCount = summaries.filter(s => s.status === 'success').length;
        const errorCount = summaries.filter(s => s.status === 'error').length;

        if (successCount > 0) {
          success(
            `Successfully uploaded ${successCount} file(s)${
              errorCount > 0 ? `, ${errorCount} file(s) encountered validation issues` : ''
            }`
          );
        }

        // Silently handle case where all files failed
        // (errors will be shown in the upload summaries below)
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Upload failed';
        error(`Upload failed: ${errorMsg}. Check the browser console (F12) for more details.`);
      } finally {
        setUploading(false);
      }
    },
    [uploadedFiles, fileType, seagYear, success, error]
  );

  /**
   * Review SEAG upload as spreadsheet
   */
  const handleReview = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      if (uploadedFiles.length === 0) {
        error('No files selected. Click "Choose Files" to add Excel files for upload.');
        return;
      }

      try {
        let blob: Blob;
        let filename: string;
        let summaryMessage = '';

        if (fileType === 'seag') {
          if (!seagYear) {
            error('SEAG year is required.');
            return;
          }

          if (!meetCity || !meetName) {
            error('Meet city and meet name are required for upload.');
            return;
          }

          // For SEAG files, generate preview for the first file
          blob = await api.previewSeagUpload(
            uploadedFiles[0],
            seagYear,
            meetCity,
            meetName,
            meetMonth,
            meetDay
          );
          filename = `seag_${seagYear}_preview.xlsx`;
          summaryMessage = 'SEAG preview downloaded. Check SUMMARY sheet in Excel.';
        } else {
          // For SwimRankings files, generate preview (extracts meet info from file)
          const result = await api.previewSwimRankingsUpload(uploadedFiles[0]);
          blob = result.blob;
          filename = `swimrankings_preview.xlsx`;

          // Build summary message for user feedback
          const { total, matched, unmatched } = result.summary;
          summaryMessage = `Preview: ${matched} of ${total} results MATCHED (will upload). ${unmatched} UNMATCHED (see Excel for details).`;
        }

        // Create download link
        console.log('[DEBUG] Blob size:', blob?.size, 'Blob type:', blob?.type);
        if (!blob || blob.size === 0) {
          throw new Error('Preview returned empty file. Check backend console for errors.');
        }

        // Force correct MIME type for Excel
        const excelBlob = new Blob([blob], {
          type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        });
        const url = window.URL.createObjectURL(excelBlob);

        // Try multiple download approaches
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.style.display = 'none';
        document.body.appendChild(link);

        // Use setTimeout to ensure DOM is ready
        setTimeout(() => {
          link.click();
          document.body.removeChild(link);
          window.URL.revokeObjectURL(url);
        }, 100);

        success(summaryMessage);
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Review failed';
        error(`Review failed: ${errorMsg}. Check the browser console (F12) for more details.`);
      }
    },
    [uploadedFiles, fileType, seagYear, meetCity, meetName, meetMonth, meetDay, success, error]
  );

  /**
   * Toggle issue group expansion
   */
  const toggleIssueGroup = useCallback((key: string) => {
    setExpandedIssueKeys(prev => ({
      ...prev,
      [key]: !prev[key],
    }));
  }, []);

  /**
   * Can submit form
   */
  const canSubmit = uploadedFiles.length > 0 && !uploading;

  /**
   * Fetch all meets
   */
  const handleFetchMeets = useCallback(async () => {
    setLoadingMeets(true);
    try {
      const meetsData = await api.getMeets();
      setMeets(meetsData);
    } catch (err) {
      error(err instanceof Error ? err.message : 'Failed to load meets');
    } finally {
      setLoadingMeets(false);
    }
  }, [error]);

  /**
   * Force refresh meets
   */
  const handleForceRefresh = useCallback(() => {
    setLoadingMeets(false);
    setTimeout(() => handleFetchMeets(), 100);
  }, [handleFetchMeets]);

  /**
   * Update meet alias
   */
  const handleUpdateAlias = useCallback(
    async (meetId: string, newAlias: string) => {
      try {
        await api.updateMeetAlias(meetId, newAlias);
        success('Alias updated successfully');

        // Update local state
        setMeets(prevMeets =>
          prevMeets.map(m => (m.id === meetId ? { ...m, alias: newAlias } : m))
        );

        // Clear editing state
        const newEditing = { ...editingAlias };
        delete newEditing[meetId];
        setEditingAlias(newEditing);
      } catch (err) {
        error(err instanceof Error ? err.message : 'Failed to update alias');
      }
    },
    [editingAlias, success, error]
  );

  /**
   * Update meet category
   */
  const handleUpdateCategory = useCallback(
    async (meetId: string, participantType: string, scope: string) => {
      try {
        await api.updateMeetCategory(meetId, participantType, scope);
        const newCategory = `${participantType}-${scope}`;
        success('Category updated successfully');

        // Update local state
        setMeets(prevMeets =>
          prevMeets.map(m => (m.id === meetId ? { ...m, category: newCategory } : m))
        );

        // Clear editing state
        const newEditing = { ...editingCategory };
        delete newEditing[meetId];
        setEditingCategory(newEditing);
      } catch (err) {
        error(err instanceof Error ? err.message : 'Failed to update category');
      }
    },
    [editingCategory, success, error]
  );

  /**
   * Load results for a meet to edit comp_place
   * Opens modal immediately, then loads data inside it
   */
  const handleLoadMeetResults = useCallback(
    async (meetId: string, meetName: string) => {
      // Open modal immediately (like Update Table modals do)
      setEditingMeetName(meetName);
      setEditingResultsMeetId(meetId);
      setMeetResults([]);
      setCompPlaceEdits({});
      setLoadingResults(true);
      setShowCompPlaceModal(true);

      // Then fetch data
      try {
        const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
        const response = await fetch(`${apiBase}/api/admin/meet-results/${meetId}`);
        if (!response.ok) {
          throw new Error(`Failed to load results: ${response.status}`);
        }
        const data = await response.json();
        setMeetResults(data.results || []);
        // Initialize edits with existing values
        // Show comp_place if set, otherwise show status if not OK
        const initialEdits: Record<string, string> = {};
        for (const r of data.results || []) {
          if (r.comp_place !== null) {
            initialEdits[r.id] = String(r.comp_place);
          } else if (r.result_status && r.result_status !== 'OK') {
            initialEdits[r.id] = r.result_status;  // Show DQ, DNS, etc.
          } else {
            initialEdits[r.id] = '';
          }
        }
        setCompPlaceEdits(initialEdits);
      } catch (err) {
        error(err instanceof Error ? err.message : 'Failed to load results');
      } finally {
        setLoadingResults(false);
      }
    },
    [error]
  );

  /**
   * Save comp_place edits
   */
  const handleSaveCompPlace = useCallback(
    async () => {
      try {
        const updates = Object.entries(compPlaceEdits)
          .map(([resultId, value]) => ({
            result_id: resultId,  // Keep as string (UUID)
            value: value  // Can be number string or status code (DQ, DNS, etc.)
          }));

        if (updates.length === 0) {
          setShowCompPlaceModal(false);
          return;
        }

        const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
        const response = await fetch(`${apiBase}/api/admin/meet-results/update-comp-place`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ updates })
        });

        const result = await response.json();
        if (result.success) {
          success(`Updated ${result.updated} results`);
          setShowCompPlaceModal(false);
          setEditingResultsMeetId(null);
          setMeetResults([]);
          setCompPlaceEdits({});
        } else {
          error('Failed to save: ' + (result.detail || 'Unknown error'));
        }
      } catch (err) {
        error(err instanceof Error ? err.message : 'Failed to save');
      }
    },
    [compPlaceEdits, success, error]
  );

  // ==================== MANUAL ENTRY HANDLERS ====================

  /**
   * Create meet for manual entry
   */
  const handleCreateManualMeet = useCallback(async () => {
    if (!manualMeetName || !manualMeetAlias || !manualMeetDate) {
      error('Meet name, alias, and date are required');
      return;
    }

    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
      const response = await fetch(`${apiBase}/api/admin/meets/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          meet_name: manualMeetName,
          meet_alias: manualMeetAlias,
          meet_date: manualMeetDate,
          meet_course: manualMeetCourse,
          meet_city: manualMeetCity,
        })
      });

      const result = await response.json();
      if (result.success) {
        setManualMeetId(result.meet_id);
        success(`Meet "${manualMeetName}" created. Now add athletes to roster.`);
        handleFetchMeets(); // Refresh meets list
      } else {
        error('Failed to create meet: ' + (result.detail || 'Unknown error'));
      }
    } catch (err) {
      error(err instanceof Error ? err.message : 'Failed to create meet');
    }
  }, [manualMeetName, manualMeetAlias, manualMeetDate, manualMeetCourse, manualMeetCity, success, error, handleFetchMeets]);

  /**
   * Search athletes for roster
   */
  const handleRosterSearch = useCallback(async () => {
    if (!rosterSearch || rosterSearch.length < 2) {
      setRosterSearchResults([]);
      return;
    }

    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
      const response = await fetch(`${apiBase}/api/admin/athletes/search?q=${encodeURIComponent(rosterSearch)}&limit=10`);
      const data = await response.json();
      setRosterSearchResults(data.athletes || []);
    } catch (err) {
      console.error('Search error:', err);
    }
  }, [rosterSearch]);

  /**
   * Add athlete to roster
   */
  const handleAddToRoster = useCallback((athlete: { id: number; fullname: string; birthdate: string; gender: string }) => {
    if (roster.some(a => a.id === athlete.id)) {
      error('Athlete already in roster');
      return;
    }
    setRoster(prev => [...prev, athlete]);
    setRosterSearch('');
    setRosterSearchResults([]);
  }, [roster, error]);

  /**
   * Remove athlete from roster
   */
  const handleRemoveFromRoster = useCallback((athleteId: number) => {
    setRoster(prev => prev.filter(a => a.id !== athleteId));
    if (selectedRosterAthlete === athleteId) {
      setSelectedRosterAthlete(null);
      setAthleteEventResults([]);
    }
  }, [selectedRosterAthlete]);

  /**
   * Select athlete for results entry
   */
  const handleSelectAthleteForResults = useCallback(async (athleteId: number) => {
    setSelectedRosterAthlete(athleteId);
    setAthleteEventResults([]);

    // Fetch available events based on athlete's gender
    const athlete = roster.find(a => a.id === athleteId);
    if (!athlete) return;

    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
      const response = await fetch(`${apiBase}/api/admin/events/filter?gender=${athlete.gender}&course=${manualMeetCourse}`);
      const data = await response.json();
      setAvailableEvents((data.events || []).map((e: any) => ({
        id: e.id,
        display: `${e.distance} ${e.stroke}`
      })));
    } catch (err) {
      console.error('Failed to load events:', err);
    }
  }, [roster, manualMeetCourse]);

  /**
   * Add event to athlete's results
   */
  const handleAddEventToAthlete = useCallback(() => {
    if (!selectedEventToAdd) return;

    const event = availableEvents.find(e => e.id === selectedEventToAdd);
    if (!event) return;

    if (athleteEventResults.some(r => r.event_id === selectedEventToAdd)) {
      error('Event already added');
      return;
    }

    setAthleteEventResults(prev => [...prev, {
      event_id: selectedEventToAdd,
      event_display: event.display,
      prelim_time: '',
      prelim_place: '',
      final_time: '',
      final_place: '',
    }]);
    setSelectedEventToAdd('');
  }, [selectedEventToAdd, availableEvents, athleteEventResults, error]);

  /**
   * Update event result field
   */
  const handleUpdateEventResult = useCallback((eventId: string, field: string, value: string) => {
    setAthleteEventResults(prev => prev.map(r =>
      r.event_id === eventId ? { ...r, [field]: value } : r
    ));
  }, []);

  /**
   * Remove event from athlete's results
   */
  const handleRemoveEventFromAthlete = useCallback((eventId: string) => {
    setAthleteEventResults(prev => prev.filter(r => r.event_id !== eventId));
  }, []);

  /**
   * Save results for current athlete
   */
  const handleSaveAthleteResults = useCallback(async () => {
    if (!manualMeetId || !selectedRosterAthlete) {
      error('No meet or athlete selected');
      return;
    }

    const resultsToSave = athleteEventResults.filter(r =>
      r.prelim_time || r.final_time
    );

    if (resultsToSave.length === 0) {
      error('No results to save (enter at least one time)');
      return;
    }

    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
      const response = await fetch(`${apiBase}/api/admin/manual-results/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          meet_id: manualMeetId,
          athlete_id: selectedRosterAthlete,
          results: resultsToSave.map(r => ({
            event_id: r.event_id,
            prelim_time: r.prelim_time || null,
            prelim_place: r.prelim_place || null,
            final_time: r.final_time || null,
            final_place: r.final_place || null,
          }))
        })
      });

      const result = await response.json();
      if (result.success) {
        success(`Saved ${result.saved} results for athlete`);
        setAthleteEventResults([]);
      } else {
        error('Failed to save: ' + (result.detail || 'Unknown error'));
      }
    } catch (err) {
      error(err instanceof Error ? err.message : 'Failed to save results');
    }
  }, [manualMeetId, selectedRosterAthlete, athleteEventResults, success, error]);

  /**
   * Load relay events
   */
  const handleLoadRelayEvents = useCallback(async () => {
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
      const response = await fetch(`${apiBase}/api/admin/events/filter?is_relay=1&course=${manualMeetCourse}`);
      const data = await response.json();
      setAvailableRelayEvents((data.events || []).map((e: any) => ({
        id: e.id,
        display: `${e.distance} ${e.stroke} ${e.gender === 'M' ? 'Men' : e.gender === 'F' ? 'Women' : 'Mixed'}`
      })));
    } catch (err) {
      console.error('Failed to load relay events:', err);
    }
  }, [manualMeetCourse]);

  /**
   * Update relay split
   */
  const handleUpdateRelaySplit = useCallback((leg: number, field: string, value: any) => {
    setRelaySplits(prev => prev.map(s =>
      s.leg === leg ? { ...s, [field]: value } : s
    ));
  }, []);

  /**
   * Save relay splits
   */
  const handleSaveRelaySplits = useCallback(async () => {
    if (!manualMeetId || !relayEventId) {
      error('No meet or relay event selected');
      return;
    }

    const validSplits = relaySplits.filter(s => s.athlete_id && s.split_time);
    if (validSplits.length === 0) {
      error('No valid splits to save');
      return;
    }

    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
      const response = await fetch(`${apiBase}/api/admin/relay-splits/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          meet_id: manualMeetId,
          event_id: relayEventId,
          round: relayRound,
          relay_place: relayPlace ? parseInt(relayPlace) : null,
          splits: relaySplits.map(s => ({
            leg_number: s.leg,
            athlete_id: s.athlete_id,
            split_time: s.split_time,
            is_leadoff: s.leg === 1,
          }))
        })
      });

      const result = await response.json();
      if (result.success) {
        success(`Saved relay splits. ${result.leadoff_copied ? 'Leadoff time copied to results.' : ''}`);
        // Reset splits
        setRelaySplits([
          { leg: 1, athlete_id: null, athlete_name: '', split_time: '' },
          { leg: 2, athlete_id: null, athlete_name: '', split_time: '' },
          { leg: 3, athlete_id: null, athlete_name: '', split_time: '' },
          { leg: 4, athlete_id: null, athlete_name: '', split_time: '' },
        ]);
        setRelayPlace('');
      } else {
        error('Failed to save: ' + (result.detail || 'Unknown error'));
      }
    } catch (err) {
      error(err instanceof Error ? err.message : 'Failed to save relay splits');
    }
  }, [manualMeetId, relayEventId, relayRound, relayPlace, relaySplits, success, error]);

  /**
   * Reset manual entry form
   */
  const handleResetManualEntry = useCallback(() => {
    setManualMeetName('');
    setManualMeetAlias('');
    setManualMeetDate('');
    setManualMeetCourse('LCM');
    setManualMeetCity('');
    setManualMeetId(null);
    setRoster([]);
    setSelectedRosterAthlete(null);
    setAthleteEventResults([]);
    setShowRelayEntry(false);
  }, []);

  // ==================== END MANUAL ENTRY HANDLERS ====================

  /**
   * Delete meet
   */
  const handleDeleteMeet = useCallback(
    async (meetId: string, meetName: string) => {
      if (!window.confirm(`Delete "${meetName}" and all its results?`)) {
        return;
      }

      try {
        await api.deleteMeet(meetId);
        success(`Meet "${meetName}" deleted successfully`);

        // Remove from local state
        setMeets(prevMeets => prevMeets.filter(m => m.id !== meetId));
      } catch (err) {
        error(err instanceof Error ? err.message : 'Failed to delete meet');
      }
    },
    [success, error]
  );

  /**
   * View meet PDF
   */
  const handleViewPdf = useCallback((meetId: string) => {
    api.openMeetPdf(meetId);
  }, []);

  /**
   * Toggle meet checkbox
   */
  const handleToggleMeet = useCallback((meetId: string) => {
    setSelectedMeetIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(meetId)) {
        newSet.delete(meetId);
      } else {
        newSet.add(meetId);
      }
      return newSet;
    });
  }, []);

  /**
   * Select/Deselect all meets
   */
  const handleSelectAll = useCallback(() => {
    if (selectedMeetIds.size === meets.length) {
      setSelectedMeetIds(new Set());
    } else {
      setSelectedMeetIds(new Set(meets.map(m => m.id)));
    }
  }, [meets, selectedMeetIds.size]);

  /**
   * Filtered meets to display
   */
  const displayedMeets = selectedMeetIds.size === 0 ? meets : meets.filter(m => selectedMeetIds.has(m.id));

  /**
   * Initial load
   */
  useEffect(() => {
    if (isAuthenticated) {
      handleFetchMeets();
    }
  }, [isAuthenticated, handleFetchMeets]);

  return (
    <div className="space-y-6 bg-gray-50 px-6">
      {/* Notifications */}
      {notifications.map(notification => {
        const bgColor = notification.type === 'success' ? '#ecfdf5' : notification.type === 'error' ? '#fef2f2' : '#fef3c7';
        const textColor = notification.type === 'success' ? '#065f46' : notification.type === 'error' ? '#cc0000' : '#cc0000';
        const icon = notification.type === 'success' ? '✓' : notification.type === 'error' ? '✕' : '⚠';
        return (
          <div key={notification.id} style={{ padding: '0.75rem', marginBottom: '0.75rem', backgroundColor: bgColor, color: textColor, fontSize: '0.875rem', borderRadius: '4px' }}>
            {icon} {notification.message}
          </div>
        );
      })}

      {/* Export Tables Section - Fixed and Independent */}
      <div style={{ marginTop: '1.5rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <button
          onClick={handleExportResults}
          style={{
            padding: '2px 10px',
            backgroundColor: '#cc0000',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            fontSize: '0.9em',
            cursor: 'pointer',
            whiteSpace: 'nowrap',
            display: 'inline-block',
          }}
        >
          Export Results Table
        </button>

        <button
          onClick={handleExportEvents}
          style={{
            padding: '2px 10px',
            backgroundColor: '#cc0000',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            fontSize: '0.9em',
            cursor: 'pointer',
            whiteSpace: 'nowrap',
            display: 'inline-block',
          }}
        >
          Export Events Table
        </button>
      </div>

      {/* Upload Meet Files Form */}
      <div className="bg-white p-6 rounded-lg">
        {/* Upload Meet Files Header - Gray Background */}
        <div className="bg-gray-50 p-4 rounded-lg" style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: '0.5rem', marginBottom: '10px' }}>
          <h3 className="text-xl font-bold text-gray-900 m-0">
            Upload Meet Files
          </h3>

          {/* File Type Selection - Inline with Radio Buttons */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap', marginBottom: '12px' }}>
            <strong style={{ fontSize: '14px' }}>File Type:</strong>

              <label style={{ display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer', whiteSpace: 'nowrap', marginRight: '8px' }}>
                <input
                  type="radio"
                  name="fileType"
                  value="swimrankings"
                  checked={fileType === 'swimrankings'}
                  onChange={() => setFileType('swimrankings')}
                  style={{ accentColor: '#cc0000', marginRight: '4px' }}
                />
                <span style={{ fontSize: '14px' }}>SwimRankings.net Download</span>
              </label>

              <label style={{ display: 'flex', alignItems: 'center', gap: '2px', cursor: 'pointer', whiteSpace: 'nowrap', marginRight: 'px' }}>
                <input
                  type="radio"
                  name="fileType"
                  value="seag"
                  checked={fileType === 'seag'}
                  onChange={() => setFileType('seag')}
                  style={{ accentColor: '#cc0000', marginRight: '4px' }}
                />
                <span style={{ fontSize: '14px' }}>SEA Age Group Championships</span>
              </label>
          </div>
        </div>

        <form onSubmit={handleUpload} style={{ margin: '0' }}>
          {/* Form Action Row - SEAG inputs (conditional) and buttons (always visible) in one container */}
          {true && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', marginBottom: '10px' }}>
              {/* SEAG Meet City Input - First */}
              {fileType === 'seag' && (
              <input
                type="text"
                value={meetCity}
                onChange={(e) => setMeetCity(e.target.value)}
                placeholder="Meet City"
                style={{
                  padding: '2px 10px',
                  border: '1px solid #ccc',
                  borderRadius: '4px',
                  fontSize: '0.9em',
                  width: '100px'
                }}
              />
            )}

            {/* SEAG Meet Name Input - Second */}
            {fileType === 'seag' && (
              <input
                type="text"
                value={meetName}
                onChange={(e) => setMeetName(e.target.value)}
                placeholder="Meet Name"
                style={{
                  padding: '2px 10px',
                  border: '1px solid #ccc',
                  borderRadius: '4px',
                  fontSize: '0.9em',
                  width: '150px'
                }}
              />
            )}

            {/* SEAG 1st Day of Meet - Month/Day/Year Dropdowns - Third */}
            {fileType === 'seag' && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '2px' }}>
                <label style={{ fontSize: '0.9em', fontWeight: '500' }}>1st Day:</label>
                <select
                  value={meetMonth}
                  onChange={(e) => setMeetMonth(e.target.value)}
                  style={{
                    padding: '2px 6px',
                    border: '1px solid #ccc',
                    borderRadius: '4px',
                    fontSize: '0.9em',
                    width: '70px'
                  }}
                >
                  <option value="01">Jan</option>
                  <option value="02">Feb</option>
                  <option value="03">Mar</option>
                  <option value="04">Apr</option>
                  <option value="05">May</option>
                  <option value="06">Jun</option>
                  <option value="07">Jul</option>
                  <option value="08">Aug</option>
                  <option value="09">Sep</option>
                  <option value="10">Oct</option>
                  <option value="11">Nov</option>
                  <option value="12">Dec</option>
                </select>
                <select
                  value={meetDay}
                  onChange={(e) => setMeetDay(e.target.value)}
                  style={{
                    padding: '2px 6px',
                    border: '1px solid #ccc',
                    borderRadius: '4px',
                    fontSize: '0.9em',
                    width: '60px'
                  }}
                >
                  {Array.from({ length: 31 }, (_, i) => (
                    <option key={i + 1} value={String(i + 1).padStart(2, '0')}>
                      {i + 1}
                    </option>
                  ))}
                </select>
                <select
                  value={seagYear}
                  onChange={(e) => setSeagYear(e.target.value)}
                  style={{
                    padding: '2px 6px',
                    border: '1px solid #ccc',
                    borderRadius: '4px',
                    fontSize: '0.9em',
                    width: '70px'
                  }}
                >
                  {Array.from({ length: 41 }, (_, i) => {
                    const year = 2000 + i;
                    return (
                      <option key={year} value={String(year)}>
                        {year}
                      </option>
                    );
                  })}
                </select>
              </div>
            )}

            {/* Red Choose Files button */}
            <button
              type="button"
              onClick={() => {
                const fileInput = document.getElementById(
                  'meet-files'
                ) as HTMLInputElement;
                if (fileInput) fileInput.click();
              }}
              style={{
                padding: '2px 10px',
                backgroundColor: '#cc0000',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                fontSize: '0.9em',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                display: 'inline-block'
              }}
              onMouseEnter={(e) => {
                (e.target as HTMLButtonElement).style.backgroundColor = '#cc0000';
              }}
              onMouseLeave={(e) => {
                (e.target as HTMLButtonElement).style.backgroundColor = '#cc0000';
              }}
            >
              Choose Files
            </button>

            {/* Upload & Convert Meet button */}
            <button
              type="submit"
              disabled={!canSubmit || uploading}
              style={{
                padding: '2px 10px',
                backgroundColor: uploadedFiles.length > 0 ? '#16a34a' : '#cc0000',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                fontSize: '0.9em',
                cursor: canSubmit ? 'pointer' : 'not-allowed',
                whiteSpace: 'nowrap',
                opacity: uploading ? 0.7 : 1,
                display: 'inline-block'
              }}
              onMouseEnter={(e) => {
                if (canSubmit) {
                  const currentColor = (e.target as HTMLButtonElement).style.backgroundColor;
                  const hoverColor = uploadedFiles.length > 0 ? '#15803d' : '#cc0000';
                  (e.target as HTMLButtonElement).style.backgroundColor = hoverColor;
                }
              }}
              onMouseLeave={(e) => {
                const leaveColor = uploadedFiles.length > 0 ? '#16a34a' : '#cc0000';
                (e.target as HTMLButtonElement).style.backgroundColor = leaveColor;
              }}
            >
              {uploading ? 'Processing...' : 'Upload & Convert Meet'}
            </button>

            {/* Preview Results button - Shows when files are selected (same trigger as green Upload button) */}
            {uploadedFiles.length > 0 && (
              <button
                type="button"
                onClick={handleReview}
                style={{
                  padding: '2px 10px',
                  backgroundColor: '#3b82f6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  fontSize: '0.9em',
                  cursor: 'pointer',
                  whiteSpace: 'nowrap',
                  display: 'inline-block'
                }}
                onMouseEnter={(e) => {
                  (e.target as HTMLButtonElement).style.backgroundColor = '#2563eb';
                }}
                onMouseLeave={(e) => {
                  (e.target as HTMLButtonElement).style.backgroundColor = '#3b82f6';
                }}
                title="Preview results before uploading (download spreadsheet)"
              >
                Preview Results
              </button>
            )}
            </div>
          )}

          {/* Hidden file input */}
          <input
            id="meet-files"
            type="file"
            accept=".xlsx,.xls"
            onChange={handleFileSelect}
            multiple
            style={{ display: 'none' }}
          />

          {/* Selected files list - Below the action row */}
          {uploadedFiles.length > 0 && (
            <div style={{ marginTop: '2px', marginBottom: '2px' }}>
              <p style={{ color: '#16a34a', fontSize: '13px', fontWeight: '500', marginBottom: '2px' }}>
                Selected {uploadedFiles.length} file(s) - Ready to upload
              </p>
              <div style={{ border: '1px solid #e5e7eb', borderRadius: '4px', padding: '8px', backgroundColor: '#f9fafb' }}>
                {uploadedFiles.map((file, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '8px',
                      marginBottom: '2px',
                      backgroundColor: '#ffffff',
                      borderRadius: '4px',
                      border: '1px solid #e5e7eb',
                      fontSize: '13px'
                    }}
                  >
                    <span>{file.name}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveFile(idx)}
                      style={{
                        padding: '4px 8px',
                        backgroundColor: '#dc2626',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        fontSize: '12px',
                        cursor: 'pointer',
                        fontWeight: 'bold'
                      }}
                      onMouseEnter={(e) => {
                        (e.target as HTMLButtonElement).style.backgroundColor = '#b91c1c';
                      }}
                      onMouseLeave={(e) => {
                        (e.target as HTMLButtonElement).style.backgroundColor = '#dc2626';
                      }}
                      title="Remove file"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </form>
      </div>

      {/* Upload Summaries - Gray Background */}
      {uploadSummaries.length > 0 && (
        <div className="bg-gray-50 p-6 rounded-lg">
          <div className="space-y-4">
          {uploadSummaries.map(summary => {
            const statusColor =
              summary.status === 'success'
                ? '#166534'
                : summary.status === 'processing'
                ? '#854d0e'
                : summary.status === 'pending'
                ? '#1f2937'
                : '#b91c1c';

            const borderColor =
              summary.status === 'success'
                ? '#bbf7d0'
                : summary.status === 'processing'
                ? '#fcd34d'
                : summary.status === 'pending'
                ? '#d1d5db'
                : '#fecaca';

            return (
              <div
                key={summary.filename}
                className="bg-white border rounded-lg p-4 shadow-sm"
                style={{ borderColor }}
              >
                {/* Header */}
                <div className="flex justify-between items-start gap-2">
                  <div>
                    <div className="font-semibold text-gray-900">
                      {summary.filename}
                    </div>
                    <div className="text-sm mt-1" style={{ color: statusColor }}>
                      <pre className="whitespace-pre-wrap font-sans m-0">
                        {summary.message}
                      </pre>
                    </div>
                  </div>

                  <div
                    className="text-xs px-2 py-1 rounded-full font-semibold uppercase tracking-wide"
                    style={{
                      backgroundColor:
                        summary.status === 'success'
                          ? '#dcfce7'
                          : summary.status === 'processing'
                          ? '#fef3c7'
                          : summary.status === 'pending'
                          ? '#e5e7eb'
                          : '#fee2e2',
                      color: statusColor,
                    }}
                  >
                    {summary.status}
                  </div>
                </div>

                {/* Metrics */}
                {summary.metrics && (
                  <div className="grid grid-cols-4 gap-2 mt-4">
                    {[
                      { label: 'Athletes', value: summary.metrics.athletes },
                      { label: 'Results', value: summary.metrics.results },
                      { label: 'Events', value: summary.metrics.events },
                      { label: 'Meets', value: summary.metrics.meets },
                    ].map(metric => (
                      <div key={metric.label} className="text-center">
                        <div className="text-xl font-bold text-red-600">
                          {metric.value}
                        </div>
                        <div className="text-xs text-gray-600">
                          {metric.label}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Issues */}
                {summary.issues && (
                  <div className="mt-4 space-y-2">
                    {Object.entries(summary.issues)
                      .filter(([, items]) => Array.isArray(items) && items.length > 0)
                      .map(([issueKey, items]) => {
                        const label =
                          ISSUE_LABELS[issueKey] ||
                          issueKey.replace(/_/g, ' ');
                        const expandKey = `${summary.filename}__${issueKey}`;
                        const isExpanded = expandedIssueKeys[expandKey];

                        return (
                          <div
                            key={expandKey}
                            className="border border-gray-200 rounded bg-gray-50"
                          >
                            <button
                              type="button"
                              onClick={() => toggleIssueGroup(expandKey)}
                              className="w-full text-left px-3 py-2 flex justify-between items-center font-semibold text-gray-900 hover:bg-gray-100"
                            >
                              <span>
                                {label} ({items.length})
                              </span>
                              <span className="text-gray-600">
                                {isExpanded ? '−' : '+'}
                              </span>
                            </button>

                            {isExpanded && (
                              <div className="px-3 py-2 border-t border-gray-200">
                                <ul className="space-y-2 text-sm text-gray-700">
                                  {items.map((issue: ValidationIssueDetail, idx: number) => {
                                    const rowInfo = [
                                      issue.sheet ? `Sheet ${issue.sheet}` : null,
                                      issue.row ? `Row ${issue.row}` : null,
                                    ]
                                      .filter(Boolean)
                                      .join(' • ');

                                    const extraFields = Object.entries(issue)
                                      .filter(
                                        ([key]) => key !== 'sheet' && key !== 'row'
                                      )
                                      .map(([key, value]) => `${key}: ${value}`)
                                      .join(' | ');

                                    return (
                                      <li key={idx} className="mb-2">
                                        {rowInfo && (
                                          <strong>{rowInfo}</strong>
                                        )}
                                        {extraFields && (
                                          <span className={rowInfo ? 'ml-2' : ''}>
                                            {extraFields}
                                          </span>
                                        )}
                                        {!rowInfo && !extraFields && (
                                          <span>No additional detail provided.</span>
                                        )}
                                      </li>
                                    );
                                  })}
                                </ul>
                              </div>
                            )}
                          </div>
                        );
                      })}
                  </div>
                )}
              </div>
            );
          })}
          </div>
        </div>
      )}

      {/* ==================== MANUAL ENTRY SECTION ==================== */}
      <div className="bg-white p-6 rounded-lg">
        {/* Collapsible Header */}
        <div
          onClick={() => setShowManualEntry(!showManualEntry)}
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            cursor: 'pointer',
            padding: '0.5rem 0',
          }}
        >
          <h3 className="text-xl font-bold text-gray-900">
            Manual Meet Entry {manualMeetId && `- ${manualMeetName}`}
          </h3>
          <span style={{ fontSize: '1.25rem', color: '#666' }}>
            {showManualEntry ? '[-]' : '[+]'}
          </span>
        </div>

        {showManualEntry && (
          <div style={{ marginTop: '1rem' }}>
            {/* Step 1: Create Meet */}
            {!manualMeetId ? (
              <div style={{ backgroundColor: '#f9fafb', padding: '1rem', borderRadius: '8px', marginBottom: '1rem' }}>
                <h4 style={{ fontWeight: 'bold', marginBottom: '0.75rem' }}>Step 1: Create Meet</h4>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem', marginBottom: '1rem' }}>
                  <div>
                    <label style={{ fontSize: '0.875rem', fontWeight: '500', display: 'block', marginBottom: '0.25rem' }}>Meet Name *</label>
                    <input
                      type="text"
                      value={manualMeetName}
                      onChange={(e) => setManualMeetName(e.target.value)}
                      placeholder="Asian Youth Games 2025"
                      style={{ width: '100%', padding: '0.5rem', border: '1px solid #ccc', borderRadius: '4px' }}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: '0.875rem', fontWeight: '500', display: 'block', marginBottom: '0.25rem' }}>Meet Alias *</label>
                    <input
                      type="text"
                      value={manualMeetAlias}
                      onChange={(e) => setManualMeetAlias(e.target.value.toUpperCase())}
                      placeholder="AYG25"
                      style={{ width: '100%', padding: '0.5rem', border: '1px solid #ccc', borderRadius: '4px' }}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: '0.875rem', fontWeight: '500', display: 'block', marginBottom: '0.25rem' }}>Meet Date *</label>
                    <input
                      type="date"
                      value={manualMeetDate}
                      onChange={(e) => setManualMeetDate(e.target.value)}
                      style={{ width: '100%', padding: '0.5rem', border: '1px solid #ccc', borderRadius: '4px' }}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: '0.875rem', fontWeight: '500', display: 'block', marginBottom: '0.25rem' }}>Course</label>
                    <select
                      value={manualMeetCourse}
                      onChange={(e) => setManualMeetCourse(e.target.value as 'LCM' | 'SCM')}
                      style={{ width: '100%', padding: '0.5rem', border: '1px solid #ccc', borderRadius: '4px' }}
                    >
                      <option value="LCM">LCM (50m)</option>
                      <option value="SCM">SCM (25m)</option>
                    </select>
                  </div>
                  <div>
                    <label style={{ fontSize: '0.875rem', fontWeight: '500', display: 'block', marginBottom: '0.25rem' }}>City</label>
                    <input
                      type="text"
                      value={manualMeetCity}
                      onChange={(e) => setManualMeetCity(e.target.value)}
                      placeholder="Harbin"
                      style={{ width: '100%', padding: '0.5rem', border: '1px solid #ccc', borderRadius: '4px' }}
                    />
                  </div>
                </div>
                <button
                  onClick={handleCreateManualMeet}
                  style={{
                    padding: '0.5rem 1rem',
                    backgroundColor: '#cc0000',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontWeight: 'bold',
                  }}
                >
                  Create Meet
                </button>
              </div>
            ) : (
              <>
                {/* Step 2: Build Roster */}
                <div style={{ backgroundColor: '#f9fafb', padding: '1rem', borderRadius: '8px', marginBottom: '1rem' }}>
                  <h4 style={{ fontWeight: 'bold', marginBottom: '0.75rem' }}>Step 2: Build Roster ({roster.length} athletes)</h4>
                  <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
                    <input
                      type="text"
                      value={rosterSearch}
                      onChange={(e) => {
                        setRosterSearch(e.target.value);
                        if (e.target.value.length >= 2) {
                          handleRosterSearch();
                        }
                      }}
                      onKeyUp={handleRosterSearch}
                      placeholder="Search athlete name..."
                      style={{ flex: 1, padding: '0.5rem', border: '1px solid #ccc', borderRadius: '4px' }}
                    />
                  </div>

                  {/* Search Results */}
                  {rosterSearchResults.length > 0 && (
                    <div style={{ border: '1px solid #ddd', borderRadius: '4px', marginBottom: '0.75rem', maxHeight: '150px', overflowY: 'auto' }}>
                      {rosterSearchResults.map(athlete => (
                        <div
                          key={athlete.id}
                          onClick={() => handleAddToRoster(athlete)}
                          style={{
                            padding: '0.5rem',
                            borderBottom: '1px solid #eee',
                            cursor: 'pointer',
                            display: 'flex',
                            justifyContent: 'space-between',
                          }}
                          onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#f0f0f0')}
                          onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'white')}
                        >
                          <span>{athlete.fullname}</span>
                          <span style={{ color: '#666', fontSize: '0.875rem' }}>
                            {athlete.gender} | {athlete.birthdate?.substring(0, 10) || 'No DOB'}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Current Roster */}
                  {roster.length > 0 && (
                    <div style={{ border: '1px solid #ddd', borderRadius: '4px', maxHeight: '200px', overflowY: 'auto' }}>
                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                        <thead>
                          <tr style={{ backgroundColor: '#f3f4f6' }}>
                            <th style={{ padding: '0.5rem', textAlign: 'left' }}>Name</th>
                            <th style={{ padding: '0.5rem', textAlign: 'center', width: '60px' }}>Gender</th>
                            <th style={{ padding: '0.5rem', textAlign: 'center', width: '100px' }}>DOB</th>
                            <th style={{ padding: '0.5rem', textAlign: 'center', width: '120px' }}>Actions</th>
                          </tr>
                        </thead>
                        <tbody>
                          {roster.map(athlete => (
                            <tr
                              key={athlete.id}
                              style={{
                                backgroundColor: selectedRosterAthlete === athlete.id ? '#fef3c7' : 'white',
                                borderBottom: '1px solid #eee',
                              }}
                            >
                              <td style={{ padding: '0.5rem' }}>{athlete.fullname}</td>
                              <td style={{ padding: '0.5rem', textAlign: 'center' }}>{athlete.gender}</td>
                              <td style={{ padding: '0.5rem', textAlign: 'center' }}>{athlete.birthdate?.substring(0, 10) || '-'}</td>
                              <td style={{ padding: '0.5rem', textAlign: 'center' }}>
                                <button
                                  onClick={() => handleSelectAthleteForResults(athlete.id)}
                                  style={{
                                    padding: '2px 8px',
                                    backgroundColor: selectedRosterAthlete === athlete.id ? '#16a34a' : '#cc0000',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '4px',
                                    fontSize: '0.75rem',
                                    cursor: 'pointer',
                                    marginRight: '4px',
                                  }}
                                >
                                  {selectedRosterAthlete === athlete.id ? 'Selected' : 'Enter Results'}
                                </button>
                                <button
                                  onClick={() => handleRemoveFromRoster(athlete.id)}
                                  style={{
                                    padding: '2px 8px',
                                    backgroundColor: '#dc2626',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '4px',
                                    fontSize: '0.75rem',
                                    cursor: 'pointer',
                                  }}
                                >
                                  X
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>

                {/* Step 3: Enter Results for Selected Athlete */}
                {selectedRosterAthlete && (
                  <div style={{ backgroundColor: '#fef3c7', padding: '1rem', borderRadius: '8px', marginBottom: '1rem' }}>
                    <h4 style={{ fontWeight: 'bold', marginBottom: '0.75rem' }}>
                      Step 3: Enter Results for {roster.find(a => a.id === selectedRosterAthlete)?.fullname}
                    </h4>

                    {/* Add Event */}
                    <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
                      <select
                        value={selectedEventToAdd}
                        onChange={(e) => setSelectedEventToAdd(e.target.value)}
                        style={{ flex: 1, padding: '0.5rem', border: '1px solid #ccc', borderRadius: '4px' }}
                      >
                        <option value="">-- Select Event --</option>
                        {availableEvents.map(event => (
                          <option key={event.id} value={event.id}>{event.display}</option>
                        ))}
                      </select>
                      <button
                        onClick={handleAddEventToAthlete}
                        disabled={!selectedEventToAdd}
                        style={{
                          padding: '0.5rem 1rem',
                          backgroundColor: selectedEventToAdd ? '#cc0000' : '#9ca3af',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: selectedEventToAdd ? 'pointer' : 'not-allowed',
                        }}
                      >
                        Add Event
                      </button>
                    </div>

                    {/* Event Results Table */}
                    {athleteEventResults.length > 0 && (
                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem', marginBottom: '0.75rem' }}>
                        <thead>
                          <tr style={{ backgroundColor: '#f3f4f6' }}>
                            <th style={{ padding: '0.5rem', textAlign: 'left' }}>Event</th>
                            <th style={{ padding: '0.5rem', textAlign: 'center' }}>Prelim Time</th>
                            <th style={{ padding: '0.5rem', textAlign: 'center' }}>Prelim Place</th>
                            <th style={{ padding: '0.5rem', textAlign: 'center' }}>Final Time</th>
                            <th style={{ padding: '0.5rem', textAlign: 'center' }}>Final Place</th>
                            <th style={{ padding: '0.5rem', textAlign: 'center', width: '50px' }}></th>
                          </tr>
                        </thead>
                        <tbody>
                          {athleteEventResults.map(result => (
                            <tr key={result.event_id} style={{ borderBottom: '1px solid #eee' }}>
                              <td style={{ padding: '0.5rem' }}>{result.event_display}</td>
                              <td style={{ padding: '0.5rem', textAlign: 'center' }}>
                                <input
                                  type="text"
                                  value={result.prelim_time}
                                  onChange={(e) => handleUpdateEventResult(result.event_id, 'prelim_time', e.target.value)}
                                  placeholder="00:00.00"
                                  style={{ width: '80px', padding: '0.25rem', border: '1px solid #ccc', borderRadius: '2px', textAlign: 'center' }}
                                />
                              </td>
                              <td style={{ padding: '0.5rem', textAlign: 'center' }}>
                                <input
                                  type="text"
                                  value={result.prelim_place}
                                  onChange={(e) => handleUpdateEventResult(result.event_id, 'prelim_place', e.target.value)}
                                  placeholder=""
                                  style={{ width: '50px', padding: '0.25rem', border: '1px solid #ccc', borderRadius: '2px', textAlign: 'center' }}
                                />
                              </td>
                              <td style={{ padding: '0.5rem', textAlign: 'center' }}>
                                <input
                                  type="text"
                                  value={result.final_time}
                                  onChange={(e) => handleUpdateEventResult(result.event_id, 'final_time', e.target.value)}
                                  placeholder="00:00.00"
                                  style={{ width: '80px', padding: '0.25rem', border: '1px solid #ccc', borderRadius: '2px', textAlign: 'center' }}
                                />
                              </td>
                              <td style={{ padding: '0.5rem', textAlign: 'center' }}>
                                <input
                                  type="text"
                                  value={result.final_place}
                                  onChange={(e) => handleUpdateEventResult(result.event_id, 'final_place', e.target.value)}
                                  placeholder=""
                                  style={{ width: '50px', padding: '0.25rem', border: '1px solid #ccc', borderRadius: '2px', textAlign: 'center' }}
                                />
                              </td>
                              <td style={{ padding: '0.5rem', textAlign: 'center' }}>
                                <button
                                  onClick={() => handleRemoveEventFromAthlete(result.event_id)}
                                  style={{ padding: '2px 6px', backgroundColor: '#dc2626', color: 'white', border: 'none', borderRadius: '2px', cursor: 'pointer' }}
                                >
                                  X
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}

                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button
                        onClick={handleSaveAthleteResults}
                        disabled={athleteEventResults.length === 0}
                        style={{
                          padding: '0.5rem 1rem',
                          backgroundColor: athleteEventResults.length > 0 ? '#16a34a' : '#9ca3af',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: athleteEventResults.length > 0 ? 'pointer' : 'not-allowed',
                          fontWeight: 'bold',
                        }}
                      >
                        Save Results for This Athlete
                      </button>
                      <button
                        onClick={() => {
                          setSelectedRosterAthlete(null);
                          setAthleteEventResults([]);
                        }}
                        style={{
                          padding: '0.5rem 1rem',
                          backgroundColor: '#6b7280',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer',
                        }}
                      >
                        Close
                      </button>
                    </div>
                  </div>
                )}

                {/* Step 4: Relay Splits (Optional) */}
                <div style={{ backgroundColor: '#dbeafe', padding: '1rem', borderRadius: '8px', marginBottom: '1rem' }}>
                  <div
                    onClick={() => {
                      setShowRelayEntry(!showRelayEntry);
                      if (!showRelayEntry) handleLoadRelayEvents();
                    }}
                    style={{ display: 'flex', justifyContent: 'space-between', cursor: 'pointer' }}
                  >
                    <h4 style={{ fontWeight: 'bold', margin: 0 }}>Step 4: Relay Splits (Optional)</h4>
                    <span>{showRelayEntry ? '[-]' : '[+]'}</span>
                  </div>

                  {showRelayEntry && (
                    <div style={{ marginTop: '0.75rem' }}>
                      {/* Relay Event Selection */}
                      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
                        <select
                          value={relayEventId}
                          onChange={(e) => setRelayEventId(e.target.value)}
                          style={{ flex: 1, padding: '0.5rem', border: '1px solid #ccc', borderRadius: '4px' }}
                        >
                          <option value="">-- Select Relay Event --</option>
                          {availableRelayEvents.map(event => (
                            <option key={event.id} value={event.id}>{event.display}</option>
                          ))}
                        </select>
                        <select
                          value={relayRound}
                          onChange={(e) => setRelayRound(e.target.value as 'Prelim' | 'Final')}
                          style={{ width: '100px', padding: '0.5rem', border: '1px solid #ccc', borderRadius: '4px' }}
                        >
                          <option value="Prelim">Prelim</option>
                          <option value="Final">Final</option>
                        </select>
                        <input
                          type="text"
                          value={relayPlace}
                          onChange={(e) => setRelayPlace(e.target.value)}
                          placeholder="Place"
                          style={{ width: '70px', padding: '0.5rem', border: '1px solid #ccc', borderRadius: '4px', textAlign: 'center' }}
                        />
                      </div>

                      {/* Relay Splits Table */}
                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem', marginBottom: '0.75rem' }}>
                        <thead>
                          <tr style={{ backgroundColor: '#f3f4f6' }}>
                            <th style={{ padding: '0.5rem', textAlign: 'center', width: '50px' }}>Leg</th>
                            <th style={{ padding: '0.5rem', textAlign: 'left' }}>Athlete</th>
                            <th style={{ padding: '0.5rem', textAlign: 'center', width: '100px' }}>Split Time</th>
                          </tr>
                        </thead>
                        <tbody>
                          {relaySplits.map(split => (
                            <tr key={split.leg} style={{ borderBottom: '1px solid #eee', backgroundColor: split.leg === 1 ? '#fef9c3' : 'white' }}>
                              <td style={{ padding: '0.5rem', textAlign: 'center', fontWeight: 'bold' }}>
                                {split.leg} {split.leg === 1 && '(Leadoff)'}
                              </td>
                              <td style={{ padding: '0.5rem' }}>
                                <select
                                  value={split.athlete_id || ''}
                                  onChange={(e) => {
                                    const athleteId = e.target.value ? parseInt(e.target.value) : null;
                                    const athlete = roster.find(a => a.id === athleteId);
                                    handleUpdateRelaySplit(split.leg, 'athlete_id', athleteId);
                                    handleUpdateRelaySplit(split.leg, 'athlete_name', athlete?.fullname || '');
                                  }}
                                  style={{ width: '100%', padding: '0.25rem', border: '1px solid #ccc', borderRadius: '2px' }}
                                >
                                  <option value="">-- Select from Roster --</option>
                                  {roster.map(athlete => (
                                    <option key={athlete.id} value={athlete.id}>{athlete.fullname}</option>
                                  ))}
                                </select>
                              </td>
                              <td style={{ padding: '0.5rem', textAlign: 'center' }}>
                                <input
                                  type="text"
                                  value={split.split_time}
                                  onChange={(e) => handleUpdateRelaySplit(split.leg, 'split_time', e.target.value)}
                                  placeholder="00:00.00"
                                  style={{ width: '80px', padding: '0.25rem', border: '1px solid #ccc', borderRadius: '2px', textAlign: 'center' }}
                                />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>

                      <button
                        onClick={handleSaveRelaySplits}
                        disabled={!relayEventId}
                        style={{
                          padding: '0.5rem 1rem',
                          backgroundColor: relayEventId ? '#16a34a' : '#9ca3af',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: relayEventId ? 'pointer' : 'not-allowed',
                          fontWeight: 'bold',
                        }}
                      >
                        Save Relay Splits
                      </button>
                      <p style={{ fontSize: '0.75rem', color: '#666', marginTop: '0.5rem' }}>
                        Note: Leadoff times (Leg 1) will be automatically copied to the results table as individual times.
                      </p>
                    </div>
                  )}
                </div>

                {/* Reset Button */}
                <button
                  onClick={handleResetManualEntry}
                  style={{
                    padding: '0.5rem 1rem',
                    backgroundColor: '#6b7280',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                  }}
                >
                  Start New Meet
                </button>
              </>
            )}
          </div>
        )}
      </div>

      {/* Meet Management Section - White Background */}
      <div className="bg-white p-6 rounded-lg w-full">
        {/* Header */}
        <div className="flex justify-between items-center w-full mb-6">
          <h3 className="text-xl font-bold text-gray-900">
            Meet Management {loadingMeets && '(Loading...)'}{' '}
            {meets.length > 0 && `(${meets.length} meets)`}
          </h3>
          <Button variant="danger" onClick={handleForceRefresh}>
            Force Refresh
          </Button>
        </div>

        {/* Meet Checkboxes Filter - White Background */}
        {!loadingMeets && meets.length > 0 && (
          <div style={{
            padding: '12px',
            backgroundColor: '#ffffff',
            borderRadius: '4px'
          }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(100px, 1fr))',
            gap: '0px 2px'
          }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '2px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={selectedMeetIds.size === meets.length && meets.length > 0}
                ref={(el) => {
                  if (el) {
                    (el as any).indeterminate = selectedMeetIds.size > 0 && selectedMeetIds.size < meets.length;
                  }
                }}
                onChange={handleSelectAll}
                style={{ cursor: 'pointer', width: '16px', height: '16px', accentColor: '#cc0000' }}
              />
              <strong style={{ fontSize: '13px', color: '#374151' }}>
                {selectedMeetIds.size === meets.length ? 'Deselect All' : 'Select All'}
              </strong>
            </label>

            {meets.map(meet => (
              <label
                key={meet.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0px, 2px',
                  cursor: 'pointer',
                 
                }}
              >
                <input
                  type="checkbox"
                  checked={selectedMeetIds.has(meet.id)}
                  onChange={() => handleToggleMeet(meet.id)}
                  style={{ cursor: 'pointer', width: '16px', height: '16px', accentColor: '#cc0000' }}
                />
                <span style={{ fontSize: '13px', color: '#374151', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {meet.alias || meet.name || '(No name)'}
                </span>
              </label>
            ))}
          </div>
        </div>
      )}
      </div>

      {/* Meets Table Section - Gray Background */}
      <div className="bg-gray-50 p-6 rounded-lg">
        {/* Meets Table */}
        {loadingMeets ? (
        <div className="text-center py-8">
          <p className="text-gray-600 mb-2">Loading meets...</p>
          <p className="text-gray-400 text-sm">
            If this takes too long, check the browser console (F12) for errors
          </p>
        </div>
      ) : displayedMeets.length === 0 ? (
        <p className="text-center py-8 text-gray-600">
          {meets.length === 0 ? 'No meets found in database.' : 'No meets match your selection.'}
        </p>
      ) : (
        <div className="overflow-x-auto bg-white border border-slate-200 rounded-lg">
          <table className="w-full text-sm" style={{ tableLayout: 'fixed' }}>
            <thead>
              <tr className="bg-slate-100 border-b-2 border-slate-300">
                <th className="px-4 py-3 text-left font-semibold text-gray-900" style={{ width: '22%' }}>
                  Meet Name
                </th>
                <th className="px-4 py-3 text-left font-semibold text-gray-900" style={{ width: '12%' }}>
                  Alias/Code
                </th>
                <th className="px-4 py-3 text-left font-semibold text-gray-900" style={{ width: '10%' }}>
                  Type
                </th>
                <th className="px-4 py-3 text-left font-semibold text-gray-900" style={{ width: '10%' }}>
                  Date
                </th>
                <th className="px-4 py-3 text-left font-semibold text-gray-900" style={{ width: '14%' }}>
                  City
                </th>
                <th className="px-4 py-3 text-center font-semibold text-gray-900" style={{ width: '12%' }}>
                  Results
                </th>
                <th className="px-4 py-3 text-center font-semibold text-gray-900" style={{ width: '20%' }}>
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {displayedMeets.map(meet => (
                <tr
                  key={meet.id}
                  className={`border-b border-slate-200 ${
                    editingAlias[meet.id] !== undefined || editingCategory[meet.id] !== undefined
                      ? 'bg-amber-50'
                      : 'bg-white hover:bg-gray-50'
                  }`}
                >
                  {/* Meet Name */}
                  <td className="px-4 py-3" style={{ width: '22%' }}>
                    {meet.name || '(No name)'}
                  </td>

                  {/* Alias (editable) */}
                  <td className="px-4 py-3" style={{ width: '12%', position: 'relative' }}>
                    {editingAlias[meet.id] !== undefined ? (
                      <div className="flex gap-2 items-center">
                        <input
                          type="text"
                          value={editingAlias[meet.id]}
                          onChange={e =>
                            setEditingAlias({
                              ...editingAlias,
                              [meet.id]: e.target.value,
                            })
                          }
                          onKeyPress={e => {
                            if (e.key === 'Enter') {
                              handleUpdateAlias(meet.id, editingAlias[meet.id]);
                            }
                          }}
                          className="px-2 py-1 border border-slate-300 rounded text-sm w-40"
                        />
                        <Button
                          size="sm"
                          variant="success"
                          onClick={() =>
                            handleUpdateAlias(meet.id, editingAlias[meet.id])
                          }
                        >
                          ✓
                        </Button>
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => {
                            const newEditing = { ...editingAlias };
                            delete newEditing[meet.id];
                            setEditingAlias(newEditing);
                          }}
                        >
                          ✕
                        </Button>
                      </div>
                    ) : (
                      <div className="flex justify-between items-center w-full" style={{ boxSizing: 'border-box' }}>
                        <span
                          className={`w-full ${
                            meet.alias
                              ? 'font-medium text-gray-900'
                              : 'text-gray-400'
                          }`}
                          style={{ flex: 1 }}
                        >
                          {meet.alias || '(No alias)'}
                        </span>
                        <button
                          onClick={() =>
                            setEditingAlias({
                              ...editingAlias,
                              [meet.id]: meet.alias || '',
                            })
                          }
                          style={{
                            position: 'absolute',
                            right: '4px',
                            padding: '2px 10px',
                            backgroundColor: '#cc0000',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            fontSize: '0.9em',
                            cursor: 'pointer',
                            whiteSpace: 'nowrap',
                            display: 'inline-block',
                          }}
                        >
                          Edit
                        </button>
                      </div>
                    )}
                  </td>

                  {/* Type (editable with dropdowns) */}
                  <td className="px-4 py-3" style={{ width: '10%', position: 'relative' }}>
                    {editingCategory[meet.id] !== undefined ? (
                      <div className="flex flex-col gap-1">
                        <select
                          value={editingCategory[meet.id].participantType}
                          onChange={e =>
                            setEditingCategory({
                              ...editingCategory,
                              [meet.id]: { ...editingCategory[meet.id], participantType: e.target.value },
                            })
                          }
                          className="px-1 py-1 border border-slate-300 rounded text-xs"
                        >
                          <option value="">--</option>
                          <option value="OPEN">Open</option>
                          <option value="MAST">Masters</option>
                          <option value="PARA">Para</option>
                        </select>
                        <select
                          value={editingCategory[meet.id].scope}
                          onChange={e =>
                            setEditingCategory({
                              ...editingCategory,
                              [meet.id]: { ...editingCategory[meet.id], scope: e.target.value },
                            })
                          }
                          className="px-1 py-1 border border-slate-300 rounded text-xs"
                        >
                          <option value="">--</option>
                          <option value="D">Domestic</option>
                          <option value="I">International</option>
                          <option value="N">National Team</option>
                        </select>
                        <div className="flex gap-1">
                          <Button
                            size="sm"
                            variant="success"
                            onClick={() => {
                              const cat = editingCategory[meet.id];
                              if (cat.participantType && cat.scope) {
                                handleUpdateCategory(meet.id, cat.participantType, cat.scope);
                              }
                            }}
                          >
                            ✓
                          </Button>
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() => {
                              const newEditing = { ...editingCategory };
                              delete newEditing[meet.id];
                              setEditingCategory(newEditing);
                            }}
                          >
                            ✕
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex justify-between items-center w-full">
                        <span
                          className={`${
                            meet.category
                              ? 'font-medium text-gray-900'
                              : 'text-gray-400'
                          }`}
                        >
                          {meet.category || '-'}
                        </span>
                        <button
                          onClick={() => {
                            // Parse existing category into parts
                            const parts = (meet.category || '').split('-');
                            setEditingCategory({
                              ...editingCategory,
                              [meet.id]: {
                                participantType: parts[0] || '',
                                scope: parts[1] || '',
                              },
                            });
                          }}
                          style={{
                            position: 'absolute',
                            right: '4px',
                            padding: '2px 10px',
                            backgroundColor: '#cc0000',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            fontSize: '0.9em',
                            cursor: 'pointer',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          Edit
                        </button>
                      </div>
                    )}
                  </td>

                  {/* Date */}
                  <td className="px-4 py-3 text-gray-600 text-center" style={{ width: '10%', textAlign: 'center' }}>
                    {formatDateDDMMMYYYY(meet.date)}
                  </td>

                  {/* City */}
                  <td className="px-4 py-3 text-gray-600" style={{ width: '14%' }}>
                    {meet.city || '-'}
                  </td>

                  {/* Result Count with Edit */}
                  <td className="px-4 py-3" style={{ width: '12%', position: 'relative' }}>
                    <div className="flex justify-between items-center w-full" style={{ boxSizing: 'border-box' }}>
                      <span className="font-medium" style={{ flex: 1 }}>
                        {meet.result_count || 0}
                      </span>
                      {(meet.result_count || 0) > 0 && (
                        <button
                          onClick={() => handleLoadMeetResults(meet.id, meet.name || 'Meet')}
                          style={{
                            position: 'absolute',
                            right: '4px',
                            padding: '2px 10px',
                            backgroundColor: '#cc0000',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            fontSize: '0.9em',
                            cursor: 'pointer',
                            whiteSpace: 'nowrap',
                            display: 'inline-block',
                          }}
                        >
                          Edit
                        </button>
                      )}
                    </div>
                  </td>

                  {/* Actions */}
                  <td className="px-4 py-3" style={{ width: '20%', textAlign: 'center' }}>
                    <div className="flex gap-2 justify-center">
                      <Button
                        size="sm"
                        variant="success"
                        onClick={() => handleViewPdf(meet.id)}
                        title={`Generate PDF report for ${meet.name} (event by event with place, name, birthdate, time)`}
                      >
                        View PDF
                      </Button>
                      <Button
                        size="sm"
                        variant="danger"
                        onClick={() => handleDeleteMeet(meet.id, meet.name)}
                        title={`Delete ${meet.name} and all its results`}
                      >
                        Delete
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Comp Place Edit Modal */}
      {showCompPlaceModal && (
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
            minWidth: '700px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h2 style={{ margin: 0, fontSize: '1.25rem' }}>Edit Competition Place - {editingMeetName}</h2>
              <button
                onClick={() => {
                  setShowCompPlaceModal(false);
                  setEditingResultsMeetId(null);
                  setMeetResults([]);
                  setCompPlaceEdits({});
                }}
                style={{ background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer' }}
              >
                x
              </button>
            </div>

            {loadingResults ? (
              <div style={{ padding: '2rem', textAlign: 'center' }}>Loading results...</div>
            ) : meetResults.length === 0 ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>
                No results found for this meet.
              </div>
            ) : (
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f3f4f6' }}>
                    <th style={{ padding: '0.5rem', textAlign: 'left', borderBottom: '1px solid #ddd' }}>Athlete</th>
                    <th style={{ padding: '0.5rem', textAlign: 'left', borderBottom: '1px solid #ddd' }}>Event</th>
                    <th style={{ padding: '0.5rem', textAlign: 'center', borderBottom: '1px solid #ddd' }}>Gender</th>
                    <th style={{ padding: '0.5rem', textAlign: 'right', borderBottom: '1px solid #ddd' }}>Time</th>
                    <th style={{ padding: '0.5rem', textAlign: 'center', borderBottom: '1px solid #ddd', width: '80px' }}>Place</th>
                  </tr>
                </thead>
                <tbody>
                  {meetResults.map((result, idx) => (
                    <tr key={result.id} style={{ backgroundColor: idx % 2 === 0 ? 'white' : '#f9fafb' }}>
                      <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee' }}>{result.athlete_name}</td>
                      <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee' }}>{result.event_display}</td>
                      <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee', textAlign: 'center' }}>{result.gender}</td>
                      <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee', textAlign: 'right', fontFamily: 'monospace' }}>{result.time_string}</td>
                      <td style={{ padding: '0.25rem 0.5rem', borderBottom: '1px solid #eee', textAlign: 'center' }}>
                        <input
                          type="text"
                          data-place-input="true"
                          placeholder=""
                          value={compPlaceEdits[result.id] || ''}
                          onChange={(e) => setCompPlaceEdits({ ...compPlaceEdits, [result.id]: e.target.value.toUpperCase() })}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              // Move to next input
                              const inputs = document.querySelectorAll('input[data-place-input]');
                              const currentIdx = Array.from(inputs).findIndex(el => el === e.target);
                              if (currentIdx < inputs.length - 1) {
                                (inputs[currentIdx + 1] as HTMLInputElement).focus();
                              }
                            }
                          }}
                          style={{
                            width: '50px',
                            padding: '0.125rem 0.25rem',
                            border: '1px solid #ccc',
                            borderRadius: '2px',
                            textAlign: 'center'
                          }}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {/* Action Buttons */}
            <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
              <button
                onClick={() => {
                  setShowCompPlaceModal(false);
                  setEditingResultsMeetId(null);
                  setMeetResults([]);
                  setCompPlaceEdits({});
                }}
                style={{ padding: '0.5rem 1rem', border: '1px solid #ccc', borderRadius: '4px', cursor: 'pointer' }}
              >
                Cancel
              </button>
              <button
                onClick={handleSaveCompPlace}
                disabled={loadingResults}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: '#cc0000',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: loadingResults ? 'not-allowed' : 'pointer',
                  opacity: loadingResults ? 0.6 : 1
                }}
              >
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}
      </div>
    </div>
  );
};

export default MeetManagement;
