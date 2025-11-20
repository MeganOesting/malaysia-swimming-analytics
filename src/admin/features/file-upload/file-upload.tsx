/**
 * File Upload Feature Component
 * Handles Excel file uploads for meet conversion with validation issue display
 */

import React, { useState, useCallback } from 'react';
import { UploadSummary, ValidationIssueDetail } from '../../shared/types/admin';
import { Button, AlertBox } from '../../shared/components';
import { useNotification } from '../../shared/hooks';
import * as api from './api';

export interface FileUploadProps {
  isAuthenticated: boolean;
}

const ISSUE_LABELS: Record<string, string> = {
  name_format_mismatches: 'Name Format Mismatches',
  club_misses: 'Club Not Found',
  duplicate_athletes: 'Duplicate Athletes',
  invalid_times: 'Invalid Times',
  missing_birthdates: 'Missing Birthdates',
};

export const FileUpload: React.FC<FileUploadProps> = ({ isAuthenticated }) => {
  // File state
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [fileType, setFileType] = useState<'swimrankings' | 'seag'>('swimrankings');
  const [seagYear, setSeagYear] = useState<string>('2025');

  // Results
  const [uploadSummaries, setUploadSummaries] = useState<UploadSummary[]>([]);
  const [expandedIssueKeys, setExpandedIssueKeys] = useState<
    Record<string, boolean>
  >({});

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

        success(`Added ${newFiles.length} file(s)`);
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

        if (errorCount === summaries.length) {
          error('All files failed to upload. Check the error details below for validation issues.');
        }
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

  return (
    <div className="space-y-6">
      {/* Notifications */}
      {notifications.map(notification => (
        <AlertBox
          key={notification.id}
          type={notification.type}
          message={notification.message}
          onClose={() => clear(notification.id)}
        />
      ))}

      {/* Upload Form */}
      <div className="sticky top-0 z-10 bg-white border-2 border-green-600 rounded-lg p-6 shadow-md">
        <h3 className="text-xl font-bold text-gray-900 mb-4 pb-2 border-b-2 border-green-600">
          📤 Upload Meet Files
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
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <label style={{ fontSize: '14px', fontWeight: '500' }}>Year:</label>
                <input
                  type="text"
                  value={seagYear}
                  onChange={(e) => setSeagYear(e.target.value)}
                  placeholder="2025"
                  style={{
                    padding: '6px 10px',
                    border: '1px solid #ccc',
                    borderRadius: '4px',
                    fontSize: '14px',
                    width: '70px'
                  }}
                />
              </div>
            )}
          </div>

          {/* File Selection and Upload - All on One Line */}
          <div style={{ margin: '8px 0', display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            {/* Hidden file input */}
            <input
              id="meet-files"
              type="file"
              accept=".xlsx,.xls"
              onChange={handleFileSelect}
              multiple
              className="hidden"
            />

            {/* Custom file selection button - Same size as action buttons */}
            <button
              type="button"
              onClick={() => {
                const fileInput = document.getElementById(
                  'meet-files'
                ) as HTMLInputElement;
                if (fileInput) fileInput.click();
              }}
              style={{
                padding: '10px 20px',
                backgroundColor: uploadedFiles.length > 0 ? '#f0fdf4' : '#ffffff',
                border: uploadedFiles.length > 0 ? '2px solid #16a34a' : '1px solid #d1d5db',
                borderRadius: '4px',
                fontWeight: 'bold',
                fontSize: '14px',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                display: 'inline-block'
              }}
              onMouseEnter={(e) => {
                if (uploadedFiles.length === 0) {
                  (e.target as HTMLButtonElement).style.backgroundColor = '#f9fafb';
                }
              }}
              onMouseLeave={(e) => {
                if (uploadedFiles.length === 0) {
                  (e.target as HTMLButtonElement).style.backgroundColor = '#ffffff';
                }
              }}
            >
              {uploadedFiles.length > 0
                ? `📁 Add More (${uploadedFiles.length})`
                : '📁 Choose Files'}
            </button>

            {/* Upload button - Red when ready, Gray when not */}
            <button
              type="submit"
              disabled={!canSubmit || uploading}
              style={{
                padding: '10px 20px',
                backgroundColor: canSubmit ? '#cc0000' : '#9ca3af',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                fontWeight: 'bold',
                fontSize: '14px',
                cursor: canSubmit ? 'pointer' : 'not-allowed',
                whiteSpace: 'nowrap',
                opacity: uploading ? 0.7 : 1,
                display: 'inline-block'
              }}
              onMouseEnter={(e) => {
                if (canSubmit) {
                  (e.target as HTMLButtonElement).style.backgroundColor = '#990000';
                }
              }}
              onMouseLeave={(e) => {
                if (canSubmit) {
                  (e.target as HTMLButtonElement).style.backgroundColor = '#cc0000';
                }
              }}
            >
              {uploading ? '⏳ Processing...' : '✓ Upload & Convert Meet'}
            </button>
          </div>

          {/* Selected files list - Below the action row */}
          {uploadedFiles.length > 0 && (
            <div style={{ marginTop: '12px', marginBottom: '16px' }}>
              <p style={{ color: '#16a34a', fontSize: '13px', fontWeight: '500', marginBottom: '8px' }}>
                ✅ Selected {uploadedFiles.length} file(s) - Ready to upload
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
    </div>
  );
};

export default FileUpload;
