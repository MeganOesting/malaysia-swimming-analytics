/**
 * Coach Management Feature Component
 * Handles coach/manager CRUD operations with comprehensive fields
 */

import React, { useState, useCallback } from 'react';
import { Button, AlertBox } from '../../shared/components';
import { useNotification } from '../../shared/hooks';
import * as api from './api';
import { CoachFormData, Coach } from './api';

export interface CoachManagementProps {
  isAuthenticated: boolean;
}

const emptyFormData: CoachFormData = {
  club_name: '',
  name: '',
  role: 'head_coach',
  email: '',
  whatsapp: '',
  passport_photo: '',
  passport_number: '',
  ic: '',
  shoe_size: '',
  tshirt_size: '',
  tracksuit_size: '',
  course_level_1_sport_specific: false,
  course_level_2: false,
  course_level_3: false,
  course_level_1_isn: false,
  course_level_2_isn: false,
  course_level_3_isn: false,
  seminar_oct_2024: false,
  other_courses: '',
  state_coach: false,
  logbook_file: '',
};

export const CoachManagement: React.FC<CoachManagementProps> = ({
  isAuthenticated,
}) => {
  // Search
  const [coachSearchName, setCoachSearchName] = useState('');
  const [coachSearchClub, setCoachSearchClub] = useState('');
  const [coaches, setCoaches] = useState<Coach[]>([]);

  // Form
  const [coachFormMode, setCoachFormMode] = useState<'add' | 'edit'>('add');
  const [selectedCoach, setSelectedCoach] = useState<Coach | null>(null);
  const [coachFormData, setCoachFormData] = useState<CoachFormData>(emptyFormData);

  // Notifications
  const { notifications, success, error, clear } = useNotification();

  /**
   * Search coaches
   */
  const handleSearchCoaches = useCallback(async () => {
    try {
      const results = await api.searchCoaches(
        coachSearchName || undefined,
        coachSearchClub || undefined
      );
      setCoaches(results);
    } catch (err) {
      error(err instanceof Error ? err.message : 'Failed to search coaches');
    }
  }, [coachSearchName, coachSearchClub, error]);

  /**
   * Reset form to add mode
   */
  const handleResetForm = useCallback(() => {
    setSelectedCoach(null);
    setCoachFormMode('add');
    setCoachFormData(emptyFormData);
  }, []);

  /**
   * Select coach for editing
   */
  const handleSelectCoach = useCallback((coach: Coach) => {
    setSelectedCoach(coach);
    setCoachFormMode('edit');
    setCoachFormData({
      club_name: coach.club_name || '',
      name: coach.name || '',
      role: coach.role || 'head_coach',
      email: coach.email || '',
      whatsapp: coach.whatsapp || '',
      passport_photo: coach.passport_photo || '',
      passport_number: coach.passport_number || '',
      ic: coach.ic || '',
      shoe_size: coach.shoe_size || '',
      tshirt_size: coach.tshirt_size || '',
      tracksuit_size: coach.tracksuit_size || '',
      course_level_1_sport_specific: coach.course_level_1_sport_specific || false,
      course_level_2: coach.course_level_2 || false,
      course_level_3: coach.course_level_3 || false,
      course_level_1_isn: coach.course_level_1_isn || false,
      course_level_2_isn: coach.course_level_2_isn || false,
      course_level_3_isn: coach.course_level_3_isn || false,
      seminar_oct_2024: coach.seminar_oct_2024 || false,
      other_courses: coach.other_courses || '',
      state_coach: coach.state_coach || false,
      logbook_file: coach.logbook_file || '',
    });
  }, []);

  /**
   * Save coach (create or update)
   */
  const handleSaveCoach = useCallback(async () => {
    if (
      !coachFormData.club_name.trim() ||
      !coachFormData.name.trim() ||
      !coachFormData.role.trim()
    ) {
      error('Club Name, Name, and Role are required');
      return;
    }

    try {
      if (coachFormMode === 'add') {
        await api.createCoach(coachFormData);
        success('Coach created successfully');
        handleResetForm();
      } else {
        await api.updateCoach(selectedCoach!.id, coachFormData);
        success('Coach updated successfully');
      }

      // Refresh search results
      await handleSearchCoaches();
    } catch (err) {
      error(err instanceof Error ? err.message : 'Failed to save coach');
    }
  }, [
    coachFormData,
    coachFormMode,
    selectedCoach,
    handleSearchCoaches,
    handleResetForm,
    success,
    error,
  ]);

  /**
   * Export coaches to Excel
   */
  const handleExportCoaches = async () => {
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
      const response = await fetch(`${apiBase}/api/admin/coaches/export-excel`);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to export coaches: ${response.status} ${errorText}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'coaches_export.xlsx';
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      error(err instanceof Error ? err.message : 'Export failed');
    }
  };

  /**
   * Delete coach
   */
  const handleDeleteCoach = useCallback(
    async (coach: Coach) => {
      if (!window.confirm(`Delete coach "${coach.name}"?`)) {
        return;
      }

      try {
        await api.deleteCoach(coach.id);
        success(`Coach "${coach.name}" deleted successfully`);

        // Refresh search results
        await handleSearchCoaches();

        // Reset form if deleted coach was selected
        if (selectedCoach?.id === coach.id) {
          handleResetForm();
        }
      } catch (err) {
        error(err instanceof Error ? err.message : 'Failed to delete coach');
      }
    },
    [selectedCoach, handleSearchCoaches, handleResetForm, success, error]
  );

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

      {/* Export Button */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
        <button
          onClick={handleExportCoaches}
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
          Export Coaches Table
        </button>
      </div>

      {/* Search Section */}
      <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">
          Search Coaches
        </h3>
        <div className="grid grid-cols-3 gap-4 items-end">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search by Name:
            </label>
            <input
              type="text"
              value={coachSearchName}
              onChange={e => setCoachSearchName(e.target.value)}
              placeholder="Enter coach name..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-600"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search by Club:
            </label>
            <input
              type="text"
              value={coachSearchClub}
              onChange={e => setCoachSearchClub(e.target.value)}
              placeholder="Enter club name..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-600"
            />
          </div>

          <button
            onClick={handleSearchCoaches}
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
            Search
          </button>
        </div>

        <button
          onClick={handleResetForm}
          style={{
            marginTop: '1rem',
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
          Add New Coach
        </button>
      </div>

      {/* Search Results */}
      {coaches.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">
            Search Results ({coaches.length})
          </h3>
          <div className="max-h-96 overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-100 sticky top-0">
                <tr className="border-b-2 border-gray-300">
                  <th className="px-4 py-2 text-left font-semibold">Name</th>
                  <th className="px-4 py-2 text-left font-semibold">Club</th>
                  <th className="px-4 py-2 text-left font-semibold">Role</th>
                  <th className="px-4 py-2 text-left font-semibold">Email</th>
                  <th className="px-4 py-2 text-left font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody>
                {coaches.map(coach => (
                  <tr key={coach.id} className="border-b border-gray-200">
                    <td className="px-4 py-2">{coach.name}</td>
                    <td className="px-4 py-2">{coach.club_name}</td>
                    <td className="px-4 py-2">{coach.role}</td>
                    <td className="px-4 py-2">{coach.email || '-'}</td>
                    <td className="px-4 py-2">
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleSelectCoach(coach)}
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
                          Edit
                        </button>
                        <Button
                          size="sm"
                          variant="danger"
                          onClick={() => handleDeleteCoach(coach)}
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
        </div>
      )}

      {/* Coach Form */}
      <div className="bg-white border border-slate-200 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          {coachFormMode === 'add' ? 'Add New Coach' : 'Edit Coach'}
        </h3>

        {/* Basic Info */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Club Name <span className="text-red-600">*</span>
            </label>
            <input
              type="text"
              value={coachFormData.club_name}
              onChange={e =>
                setCoachFormData({ ...coachFormData, club_name: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-600"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Name <span className="text-red-600">*</span>
            </label>
            <input
              type="text"
              value={coachFormData.name}
              onChange={e =>
                setCoachFormData({ ...coachFormData, name: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-600"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Role <span className="text-red-600">*</span>
            </label>
            <select
              value={coachFormData.role}
              onChange={e =>
                setCoachFormData({ ...coachFormData, role: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-600"
            >
              <option value="head_coach">Head Coach</option>
              <option value="assistant_coach">Assistant Coach</option>
              <option value="manager">Manager</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email
            </label>
            <input
              type="email"
              value={coachFormData.email}
              onChange={e =>
                setCoachFormData({ ...coachFormData, email: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-600"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              WhatsApp
            </label>
            <input
              type="text"
              value={coachFormData.whatsapp}
              onChange={e =>
                setCoachFormData({ ...coachFormData, whatsapp: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-600"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              IC (Identity Card)
            </label>
            <input
              type="text"
              value={coachFormData.ic}
              onChange={e =>
                setCoachFormData({ ...coachFormData, ic: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-600"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Passport Number
            </label>
            <input
              type="text"
              value={coachFormData.passport_number}
              onChange={e =>
                setCoachFormData({
                  ...coachFormData,
                  passport_number: e.target.value,
                })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-600"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Passport Photo (file path)
            </label>
            <input
              type="text"
              value={coachFormData.passport_photo}
              onChange={e =>
                setCoachFormData({
                  ...coachFormData,
                  passport_photo: e.target.value,
                })
              }
              placeholder="/path/to/photo.jpg"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-600"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Shoe Size
            </label>
            <input
              type="text"
              value={coachFormData.shoe_size}
              onChange={e =>
                setCoachFormData({ ...coachFormData, shoe_size: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-600"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              T-Shirt Size
            </label>
            <input
              type="text"
              value={coachFormData.tshirt_size}
              onChange={e =>
                setCoachFormData({
                  ...coachFormData,
                  tshirt_size: e.target.value,
                })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-600"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tracksuit Size
            </label>
            <input
              type="text"
              value={coachFormData.tracksuit_size}
              onChange={e =>
                setCoachFormData({
                  ...coachFormData,
                  tracksuit_size: e.target.value,
                })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-600"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Logbook File (file path)
            </label>
            <input
              type="text"
              value={coachFormData.logbook_file}
              onChange={e =>
                setCoachFormData({
                  ...coachFormData,
                  logbook_file: e.target.value,
                })
              }
              placeholder="/path/to/logbook.pdf"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-600"
            />
          </div>
        </div>

        {/* Course Certifications */}
        <div className="bg-gray-50 rounded-lg p-4 mb-6">
          <h4 className="font-semibold text-gray-900 mb-3">
            Course Certifications
          </h4>
          <div className="grid grid-cols-3 gap-3">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={coachFormData.course_level_1_sport_specific}
                onChange={e =>
                  setCoachFormData({
                    ...coachFormData,
                    course_level_1_sport_specific: e.target.checked,
                  })
                }
                className="w-4 h-4"
              />
              <span className="text-sm">Level 1 Sport Specific</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={coachFormData.course_level_2}
                onChange={e =>
                  setCoachFormData({
                    ...coachFormData,
                    course_level_2: e.target.checked,
                  })
                }
                className="w-4 h-4"
              />
              <span className="text-sm">Level 2</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={coachFormData.course_level_3}
                onChange={e =>
                  setCoachFormData({
                    ...coachFormData,
                    course_level_3: e.target.checked,
                  })
                }
                className="w-4 h-4"
              />
              <span className="text-sm">Level 3</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={coachFormData.course_level_1_isn}
                onChange={e =>
                  setCoachFormData({
                    ...coachFormData,
                    course_level_1_isn: e.target.checked,
                  })
                }
                className="w-4 h-4"
              />
              <span className="text-sm">Level 1 ISN</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={coachFormData.course_level_2_isn}
                onChange={e =>
                  setCoachFormData({
                    ...coachFormData,
                    course_level_2_isn: e.target.checked,
                  })
                }
                className="w-4 h-4"
              />
              <span className="text-sm">Level 2 ISN</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={coachFormData.course_level_3_isn}
                onChange={e =>
                  setCoachFormData({
                    ...coachFormData,
                    course_level_3_isn: e.target.checked,
                  })
                }
                className="w-4 h-4"
              />
              <span className="text-sm">Level 3 ISN</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={coachFormData.seminar_oct_2024}
                onChange={e =>
                  setCoachFormData({
                    ...coachFormData,
                    seminar_oct_2024: e.target.checked,
                  })
                }
                className="w-4 h-4"
              />
              <span className="text-sm">Seminar Oct 2024</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={coachFormData.state_coach}
                onChange={e =>
                  setCoachFormData({
                    ...coachFormData,
                    state_coach: e.target.checked,
                  })
                }
                className="w-4 h-4"
              />
              <span className="text-sm">State Coach</span>
            </label>
          </div>

          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Other Courses
            </label>
            <textarea
              value={coachFormData.other_courses}
              onChange={e =>
                setCoachFormData({
                  ...coachFormData,
                  other_courses: e.target.value,
                })
              }
              placeholder="List any other courses attended..."
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-600"
            />
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          <Button variant="primary" onClick={handleSaveCoach}>
            {coachFormMode === 'add' ? 'Add Coach' : 'Update Coach'}
          </Button>

          {coachFormMode === 'edit' && (
            <Button variant="secondary" onClick={handleResetForm}>
              Cancel
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

export default CoachManagement;
