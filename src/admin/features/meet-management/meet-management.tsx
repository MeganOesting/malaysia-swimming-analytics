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

  // Search and Edit Events state
  const [showEventSearch, setShowEventSearch] = useState(false);
  const [eventCourse, setEventCourse] = useState<string>('');
  const [eventGender, setEventGender] = useState<string>('');
  const [filteredEvents, setFilteredEvents] = useState<any[]>([]);
  const [loadingEvents, setLoadingEvents] = useState(false);
  const [showCourseRadios, setShowCourseRadios] = useState(false);
  const [showGenderRadios, setShowGenderRadios] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<any>(null);
  const [editingEventFields, setEditingEventFields] = useState<Record<string, any>>({});

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
   * Fetch events filtered by course and gender
   */
  const handleFetchFilteredEvents = useCallback(async (course: string, gender: string) => {
    if (!course) {
      setFilteredEvents([]);
      return;
    }

    setLoadingEvents(true);
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

      // If gender is provided, fetch for specific gender; otherwise fetch for all genders
      if (gender) {
        const response = await fetch(`${apiBase}/api/admin/events/filter?course=${course}&gender=${gender}`);
        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`Failed to fetch events: ${response.status} ${errorText}`);
        }
        const data = await response.json();
        setFilteredEvents(data.events || []);
      } else {
        // Fetch for all genders and combine results
        const genders = ['M', 'F', 'X'];
        const allEvents: any[] = [];
        const eventIds = new Set<string>();

        for (const g of genders) {
          try {
            const response = await fetch(`${apiBase}/api/admin/events/filter?course=${course}&gender=${g}`);
            if (response.ok) {
              const data = await response.json();
              // Add events, avoiding duplicates
              (data.events || []).forEach((event: any) => {
                const eventKey = `${event.distance}-${event.stroke}-${event.gender}`;
                if (!eventIds.has(eventKey)) {
                  eventIds.add(eventKey);
                  allEvents.push(event);
                }
              });
            }
          } catch (err) {
            console.warn(`Failed to fetch events for gender ${g}:`, err);
          }
        }
        setFilteredEvents(allEvents);
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to fetch events';
      error(`Error: ${errorMsg}`);
      console.error('Fetch error:', err);
    } finally {
      setLoadingEvents(false);
    }
  }, [error]);

  /**
   * Handle event selection - open edit form
   */
  const handleSelectEvent = useCallback((event: any) => {
    setSelectedEvent(event);
    setEditingEventFields({ ...event });
  }, []);

  /**
   * Handle event field updates
   */
  const handleUpdateEventField = useCallback((field: string, value: any) => {
    setEditingEventFields(prev => ({
      ...prev,
      [field]: value
    }));
  }, []);

  /**
   * Save event changes to database
   */
  const handleSaveEvent = useCallback(async () => {
    if (!selectedEvent) return;

    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

      // Extract course from old event ID (first 3 letters)
      const coursePrefix = selectedEvent.id.substring(0, 3);

      // Build new event ID based on updated fields
      const newDistance = editingEventFields.distance || selectedEvent.distance;
      const newStroke = editingEventFields.stroke || selectedEvent.stroke;
      const newGender = editingEventFields.gender || selectedEvent.gender;
      const newEventType = editingEventFields.event_type || selectedEvent.event_type;

      const newEventId = `${coursePrefix}_${newEventType}_${newDistance}_${newStroke}_${newGender}`;

      console.log('Updating event:', selectedEvent.id, '→', newEventId, 'with fields:', editingEventFields);

      // If event ID changed, check for duplicates first
      if (newEventId !== selectedEvent.id) {
        const checkResponse = await fetch(`${apiBase}/api/admin/events/check-duplicate?id=${encodeURIComponent(newEventId)}`);

        if (checkResponse.ok) {
          const checkData = await checkResponse.json();
          if (checkData.exists) {
            error(`Cannot update: Event ID "${newEventId}" already exists in database`);
            return;
          }
        }
      }

      // Prepare update payload with new event ID
      const updatePayload = {
        ...editingEventFields,
        id: newEventId  // Include new ID in payload for backend to handle the rename
      };

      // Try PATCH first, fallback to PUT if not found
      let response = await fetch(`${apiBase}/api/admin/events/${selectedEvent.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updatePayload),
      });

      // If PATCH returns 404, try PUT instead
      if (response.status === 404) {
        console.log('PATCH not found, trying PUT...');
        response = await fetch(`${apiBase}/api/admin/events/${selectedEvent.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(updatePayload),
        });
      }

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to update event: ${response.status} ${errorText}`);
      }

      success(`Event updated successfully${newEventId !== selectedEvent.id ? ` (ID changed to ${newEventId})` : ''}`);
      setSelectedEvent(null);
      setEditingEventFields({});
      // Refresh the events list
      handleFetchFilteredEvents(eventCourse, eventGender);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Update failed';
      error(`Error: ${errorMsg}`);
      console.error('Update error:', err);
    }
  }, [selectedEvent, editingEventFields, eventCourse, eventGender, handleFetchFilteredEvents, success, error]);

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
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);

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
      <div style={{ marginTop: '1.5rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '2rem' }}>
        {/* Export Results Table */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: '#111', margin: 0 }}>
            Export Results Table
          </h3>
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
            Download Excel
          </button>
        </div>

        {/* Export Events Table */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: '#111', margin: 0 }}>
            Export Events Table
          </h3>
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
            Download Excel
          </button>
          <button
            onClick={() => setShowEventSearch(!showEventSearch)}
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
              marginRight: '1rem',
            }}
          >
            Search and Edit
          </button>
        </div>
      </div>

      {/* Course Selection with Events Dropdown - Completely Separate Container */}
      {showEventSearch && (
        <div style={{ marginTop: '1rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '2rem', flexWrap: 'wrap' }}>
          {/* Course Selection */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <strong style={{ fontSize: '14px', lineHeight: '1.4' }}>Course:</strong>
            {['LCM', 'SCM'].map(course => (
              <label key={course} style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', cursor: 'pointer', marginRight: '1rem', lineHeight: '1.4' }}>
                <input
                  type="radio"
                  name="course"
                  value={course}
                  checked={eventCourse === course}
                  onChange={(e) => {
                    setEventCourse(e.target.value);
                    handleFetchFilteredEvents(e.target.value, eventGender);
                  }}
                  style={{ accentColor: '#cc0000' }}
                />
                <span style={{ fontSize: '14px' }}>{course}</span>
              </label>
            ))}
          </div>

          {/* Gender Selection - on same line */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <strong style={{ fontSize: '14px', lineHeight: '1.4' }}>Gender:</strong>
            {['M', 'F', 'X'].map(gender => (
              <label key={gender} style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', cursor: 'pointer', marginRight: '1rem', lineHeight: '1.4' }}>
                <input
                  type="radio"
                  name="gender"
                  value={gender}
                  checked={eventGender === gender}
                  onChange={(e) => {
                    setEventGender(e.target.value);
                    handleFetchFilteredEvents(eventCourse, e.target.value);
                  }}
                  style={{ accentColor: '#cc0000' }}
                />
                <span style={{ fontSize: '14px' }}>{gender}</span>
              </label>
            ))}
          </div>

          {/* Events Dropdown - appears on same line when course selected */}
          {eventCourse && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <label style={{ fontSize: '14px', fontWeight: '500', whiteSpace: 'nowrap', lineHeight: '1.4' }}>Events:</label>
              {loadingEvents ? (
                <span style={{ fontSize: '14px', color: '#666', lineHeight: '1.4' }}>Loading...</span>
              ) : filteredEvents.length > 0 ? (
                <select
                  onChange={(e) => {
                    // Handle event selection
                    const selectedEvent = filteredEvents.find(evt => evt.id.toString() === e.target.value);
                    if (selectedEvent) {
                      handleSelectEvent(selectedEvent);
                    }
                  }}
                  style={{
                    padding: '4px 8px',
                    border: '1px solid #ccc',
                    borderRadius: '4px',
                    fontSize: '14px',
                    cursor: 'pointer',
                    lineHeight: '1.4',
                  }}
                  value={selectedEvent?.id || ''}
                >
                  <option value="">Select event...</option>
                  {/* Display ONLY event IDs, no formatting */}
                  {filteredEvents.map((event) => (
                    <option key={event.id} value={event.id}>
                      {event.id}
                    </option>
                  ))}
                </select>
              ) : (
                <span style={{ fontSize: '14px', color: '#666', lineHeight: '1.4' }}>No events found</span>
              )}
            </div>
          )}

          {/* Select button - before Close button */}
          {selectedEvent && !eventGender && (
            <button
              onClick={() => {}}
              style={{
                padding: '2px 8px',
                backgroundColor: '#cc0000',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                fontSize: '0.85em',
                cursor: 'pointer',
                height: 'fit-content',
                whiteSpace: 'nowrap',
              }}
            >
              Select
            </button>
          )}

          {/* Close button - on same line */}
          <button
            onClick={() => {
              setShowEventSearch(false);
              setSelectedEvent(null);
              setEditingEventFields({});
            }}
            style={{
              padding: '2px 8px',
              backgroundColor: '#666',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontSize: '0.85em',
              cursor: 'pointer',
              height: 'fit-content',
              whiteSpace: 'nowrap',
            }}
          >
            Close
          </button>
        </div>
      )}

      {/* Event Edit Form - appears when event is selected */}
      {selectedEvent && (
        <div style={{ marginTop: '1rem', marginBottom: '1.5rem', padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '4px', border: '1px solid #e5e7eb' }}>
          <h4 style={{ margin: '0 0 1rem 0', fontSize: '14px', fontWeight: '600' }}>
            Edit Event: {selectedEvent.id}
          </h4>

          {/* Event fields in specific order: id, course, stroke, distance, gender, event_type */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
            {/* Event ID (read-only display) */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <label style={{ fontSize: '12px', fontWeight: '500', color: '#374151' }}>Event ID</label>
              <input
                type="text"
                value={editingEventFields.id || ''}
                readOnly
                style={{
                  padding: '4px 8px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '13px',
                  fontFamily: 'monospace',
                  backgroundColor: '#e5e7eb',
                  color: '#666',
                }}
              />
            </div>

            {/* Course */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <label style={{ fontSize: '12px', fontWeight: '500', color: '#374151' }}>Course</label>
              <input
                type="text"
                value={editingEventFields.course || ''}
                onChange={(e) => handleUpdateEventField('course', e.target.value)}
                style={{
                  padding: '4px 8px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '13px',
                  fontFamily: 'monospace',
                }}
              />
            </div>

            {/* Stroke */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <label style={{ fontSize: '12px', fontWeight: '500', color: '#374151' }}>Stroke</label>
              <input
                type="text"
                value={editingEventFields.stroke || ''}
                onChange={(e) => handleUpdateEventField('stroke', e.target.value)}
                style={{
                  padding: '4px 8px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '13px',
                  fontFamily: 'monospace',
                }}
              />
            </div>

            {/* Distance */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <label style={{ fontSize: '12px', fontWeight: '500', color: '#374151' }}>Distance</label>
              <input
                type="text"
                value={editingEventFields.distance || ''}
                onChange={(e) => handleUpdateEventField('distance', e.target.value)}
                style={{
                  padding: '4px 8px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '13px',
                  fontFamily: 'monospace',
                }}
              />
            </div>

            {/* Gender */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <label style={{ fontSize: '12px', fontWeight: '500', color: '#374151' }}>Gender</label>
              <input
                type="text"
                value={editingEventFields.gender || ''}
                onChange={(e) => handleUpdateEventField('gender', e.target.value)}
                style={{
                  padding: '4px 8px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '13px',
                  fontFamily: 'monospace',
                }}
              />
            </div>

            {/* Event Type (Individual/Relay) */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <label style={{ fontSize: '12px', fontWeight: '500', color: '#374151' }}>Type</label>
              <input
                type="text"
                value={editingEventFields.event_type || ''}
                placeholder="Individual or Relay"
                onChange={(e) => handleUpdateEventField('event_type', e.target.value)}
                style={{
                  padding: '4px 8px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '13px',
                  fontFamily: 'monospace',
                }}
              />
            </div>
          </div>

          {/* Action buttons */}
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={handleSaveEvent}
              style={{
                padding: '4px 12px',
                backgroundColor: '#cc0000',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                fontSize: '0.85em',
                cursor: 'pointer',
                fontWeight: '500',
              }}
            >
              Confirm
            </button>
            <button
              onClick={() => {
                setSelectedEvent(null);
                setEditingEventFields({});
              }}
              style={{
                padding: '4px 12px',
                backgroundColor: '#6b7280',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                fontSize: '0.85em',
                cursor: 'pointer',
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

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
                <th className="px-4 py-3 text-left font-semibold text-gray-900" style={{ width: '25%' }}>
                  Meet Name
                </th>
                <th className="px-4 py-3 text-left font-semibold text-gray-900" style={{ width: '15%' }}>
                  Alias/Code
                </th>
                <th className="px-4 py-3 text-left font-semibold text-gray-900" style={{ width: '10%' }}>
                  Date
                </th>
                <th className="px-4 py-3 text-left font-semibold text-gray-900" style={{ width: '20%' }}>
                  City
                </th>
                <th className="px-4 py-3 text-center font-semibold text-gray-900" style={{ width: '10%' }}>
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
                    editingAlias[meet.id] !== undefined
                      ? 'bg-amber-50'
                      : 'bg-white hover:bg-gray-50'
                  }`}
                >
                  {/* Meet Name */}
                  <td className="px-4 py-3" style={{ width: '25%' }}>
                    {meet.name || '(No name)'}
                  </td>

                  {/* Alias (editable) */}
                  <td className="px-4 py-3" style={{ width: '15%', position: 'relative' }}>
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

                  {/* Date */}
                  <td className="px-4 py-3 text-gray-600 text-center" style={{ width: '10%', textAlign: 'center' }}>
                    {formatDateDDMMMYYYY(meet.date)}
                  </td>

                  {/* City */}
                  <td className="px-4 py-3 text-gray-600" style={{ width: '20%' }}>
                    {meet.city || '-'}
                  </td>

                  {/* Result Count */}
                  <td className="px-4 py-3 text-center font-medium" style={{ width: '10%', textAlign: 'center' }}>
                    {meet.result_count || 0}
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
      </div>
    </div>
  );
};

export default MeetManagement;
