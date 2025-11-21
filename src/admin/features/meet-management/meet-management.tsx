/**
 * Meet Management Feature Component
 * Handles file uploads and viewing, editing, and deleting meets
 */

import React, { useState, useCallback, useEffect } from 'react';
import { Meet, UploadSummary, ValidationIssueDetail } from '../../shared/types/admin';
import { Button } from '../../shared/components';
import { useNotification } from '../../shared/hooks';
import * as api from './api';

export interface MeetManagementProps {
  isAuthenticated: boolean;
}

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

  // Notifications
  const { notifications, success, error, clear } = useNotification();

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

      if (fileType === 'seag' && !seagYear) {
        error('SEAG year is required when uploading SEA Age Group Championship files.');
        return;
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
    <div className="space-y-6">
      {/* Notifications */}
      {notifications.map(notification => {
        const bgColor = notification.type === 'success' ? '#ecfdf5' : notification.type === 'error' ? '#fef2f2' : '#fef3c7';
        const textColor = notification.type === 'success' ? '#065f46' : notification.type === 'error' ? '#7f1d1d' : '#92400e';
        const icon = notification.type === 'success' ? '✓' : notification.type === 'error' ? '✕' : '⚠';
        return (
          <div key={notification.id} style={{ padding: '0.75rem', marginBottom: '0.75rem', backgroundColor: bgColor, color: textColor, fontSize: '0.875rem', borderRadius: '4px' }}>
            {icon} {notification.message}
          </div>
        );
      })}

      {/* Upload Meet Files Form */}
      <div className="sticky top-0 z-10 bg-white border-2 border-green-600 rounded-lg p-6 shadow-md">
        <h3 className="text-xl font-bold text-gray-900 mb-4 pb-2 border-b-2 border-green-600">
          Upload Meet Files
        </h3>

        <form onSubmit={handleUpload} style={{ margin: '2px 0' }}>
          {/* File Type Selection - Inline with Radio Buttons */}
          <div style={{ margin: '2px 0', display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
            <strong style={{ fontSize: '14px' }}>File Type:</strong>

            <label style={{ display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer', whiteSpace: 'nowrap', marginRight: '10px' }}>
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

            <label style={{ display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer', whiteSpace: 'nowrap', marginRight: '10px' }}>
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

            {/* SEAG Year Input - Inline */}
            {fileType === 'seag' && (
              <input
                type="text"
                value={seagYear}
                onChange={(e) => setSeagYear(e.target.value)}
                placeholder="2025"
                style={{
                  padding: '2px 10px',
                  border: '1px solid #ccc',
                  borderRadius: '4px',
                  fontSize: '0.9em',
                  width: '40px',
                  marginRight: '8px'
                }}
              />
            )}

            {/* SEAG Meet City Input */}
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
                  width: '100px',
                  marginRight: '8px'
                }}
              />
            )}

            {/* SEAG Meet Name Input */}
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
                  width: '150px',
                  marginRight: '8px'
                }}
              />
            )}

            {/* SEAG 1st Day of Meet - Month/Day Dropdowns */}
            {fileType === 'seag' && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginRight: '8px' }}>
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
              </div>
            )}

            {/* Red Choose Files button - Main page style */}
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
                display: 'inline-block',
                marginRight: '8px'
              }}
              onMouseEnter={(e) => {
                (e.target as HTMLButtonElement).style.backgroundColor = '#990000';
              }}
              onMouseLeave={(e) => {
                (e.target as HTMLButtonElement).style.backgroundColor = '#cc0000';
              }}
            >
              Choose Files
            </button>

            {/* Upload & Convert Meet button - Main page style */}
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
                display: 'inline-block',
                marginRight: '8px'
              }}
              onMouseEnter={(e) => {
                if (canSubmit) {
                  const currentColor = (e.target as HTMLButtonElement).style.backgroundColor;
                  const hoverColor = uploadedFiles.length > 0 ? '#15803d' : '#990000';
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
          </div>

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
            <div style={{ marginTop: '12px', marginBottom: '16px' }}>
              <p style={{ color: '#16a34a', fontSize: '13px', fontWeight: '500', marginBottom: '8px' }}>
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
                      marginBottom: '4px',
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

      {/* Upload Summaries */}
      {uploadSummaries.length > 0 && (
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
                <div className="flex justify-between items-start gap-4">
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
                  <div className="grid grid-cols-4 gap-3 mt-4">
                    {[
                      { label: 'Athletes', value: summary.metrics.athletes },
                      { label: 'Results', value: summary.metrics.results },
                      { label: 'Events', value: summary.metrics.events },
                      { label: 'Meets', value: summary.metrics.meets },
                    ].map(metric => (
                      <div key={metric.label} className="text-center">
                        <div className="text-2xl font-bold text-red-600">
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
      )}

      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">
          Meet Management {loadingMeets && '(Loading...)'}{' '}
          {meets.length > 0 && `(${meets.length} meets)`}
        </h2>
        <Button variant="danger" onClick={handleForceRefresh}>
          Force Refresh
        </Button>
      </div>

      {/* Meet Checkboxes Filter */}
      {!loadingMeets && meets.length > 0 && (
        <div style={{
          padding: '12px',
          backgroundColor: '#f9fafb',
          border: '1px solid #e5e7eb',
          borderRadius: '4px'
        }}>
          <div style={{ marginBottom: '8px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', marginBottom: '8px' }}>
              <input
                type="checkbox"
                checked={selectedMeetIds.size === meets.length && meets.length > 0}
                ref={(el) => {
                  if (el) {
                    (el as any).indeterminate = selectedMeetIds.size > 0 && selectedMeetIds.size < meets.length;
                  }
                }}
                onChange={handleSelectAll}
                style={{ cursor: 'pointer', width: '16px', height: '16px' }}
              />
              <strong style={{ fontSize: '13px', color: '#374151' }}>
                {selectedMeetIds.size === meets.length ? 'Deselect All' : 'Select All'}
              </strong>
            </label>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
            gap: '8px'
          }}>
            {meets.map(meet => (
              <label
                key={meet.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  cursor: 'pointer',
                  padding: '4px 0'
                }}
              >
                <input
                  type="checkbox"
                  checked={selectedMeetIds.has(meet.id)}
                  onChange={() => handleToggleMeet(meet.id)}
                  style={{ cursor: 'pointer', width: '16px', height: '16px' }}
                />
                <span style={{ fontSize: '13px', color: '#374151', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {meet.alias || meet.name || '(No name)'}
                </span>
              </label>
            ))}
          </div>
        </div>
      )}

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
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-100 border-b-2 border-slate-300">
                <th className="px-4 py-3 text-left font-semibold text-gray-900">
                  Meet Name
                </th>
                <th className="px-4 py-3 text-left font-semibold text-gray-900">
                  ID
                </th>
                <th className="px-4 py-3 text-left font-semibold text-gray-900">
                  Alias/Code
                </th>
                <th className="px-4 py-3 text-left font-semibold text-gray-900">
                  Date
                </th>
                <th className="px-4 py-3 text-left font-semibold text-gray-900">
                  City
                </th>
                <th className="px-4 py-3 text-center font-semibold text-gray-900">
                  Results
                </th>
                <th className="px-4 py-3 text-center font-semibold text-gray-900">
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
                  <td className="px-4 py-3">{meet.name || '(No name)'}</td>

                  {/* Meet ID */}
                  <td className="px-4 py-3 text-xs text-gray-600 font-mono">
                    <span title={meet.id} className="cursor-help">
                      {meet.id}
                    </span>
                  </td>

                  {/* Alias (editable) */}
                  <td className="px-4 py-3">
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
                          className="px-2 py-1 border border-slate-300 rounded text-sm w-32"
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
                      <div className="flex gap-2 items-center">
                        <span
                          className={`${
                            meet.alias
                              ? 'font-medium text-gray-900'
                              : 'text-gray-400'
                          }`}
                        >
                          {meet.alias || '(No alias)'}
                        </span>
                        <Button
                          size="sm"
                          variant="primary"
                          onClick={() =>
                            setEditingAlias({
                              ...editingAlias,
                              [meet.id]: meet.alias || '',
                            })
                          }
                        >
                          Edit
                        </Button>
                      </div>
                    )}
                  </td>

                  {/* Date */}
                  <td className="px-4 py-3 text-gray-600">
                    {meet.date
                      ? new Date(meet.date).toLocaleDateString()
                      : '-'}
                  </td>

                  {/* City */}
                  <td className="px-4 py-3 text-gray-600">
                    {meet.city || '-'}
                  </td>

                  {/* Result Count */}
                  <td className="px-4 py-3 text-center font-medium">
                    {meet.result_count || 0}
                  </td>

                  {/* Actions */}
                  <td className="px-4 py-3">
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
  );
};

export default MeetManagement;
