/**
 * Club Management Feature Component
 * Handles club CRUD operations, coach viewing, and roster management
 */

import React, { useState, useCallback, useEffect } from 'react';
import { Meet } from '../../shared/types/admin';
import { Button, AlertBox } from '../../shared/components';
import { useNotification } from '../../shared/hooks';
import * as api from './api';
import { ClubData, Club, Coach, RosterAthlete } from './api';

export interface ClubManagementProps {
  isAuthenticated: boolean;
  meets?: Meet[]; // Optional: for roster filtering by meet
}

export const ClubManagement: React.FC<ClubManagementProps> = ({
  isAuthenticated,
  meets = [],
}) => {
  // States and clubs
  const [states, setStates] = useState<string[]>([]);
  const [selectedState, setSelectedState] = useState('');
  const [clubs, setClubs] = useState<Club[]>([]);
  const [selectedClub, setSelectedClub] = useState<Club | null>(null);

  // Club form
  const [clubFormMode, setClubFormMode] = useState<'add' | 'edit'>('add');
  const [clubFormData, setClubFormData] = useState<ClubData>({
    club_name: '',
    club_code: '',
    state_code: '',
    nation: 'MAS',
    alias: '',
  });

  // Coaches
  const [coaches, setCoaches] = useState<Coach[]>([]);

  // Roster
  const [selectedMeetForRoster, setSelectedMeetForRoster] = useState('');
  const [clubRoster, setClubRoster] = useState<RosterAthlete[]>([]);
  const [loadingRoster, setLoadingRoster] = useState(false);

  // Notifications
  const { notifications, success, error, clear } = useNotification();

  /**
   * Fetch states
   */
  const handleFetchStates = useCallback(async () => {
    try {
      const statesData = await api.getStates();
      setStates(statesData);
    } catch (err) {
      error(err instanceof Error ? err.message : 'Failed to load states');
    }
  }, [error]);

  /**
   * Fetch clubs by state
   */
  const handleFetchClubsByState = useCallback(
    async (stateCode: string) => {
      try {
        const clubsData = await api.getClubsByState(stateCode);
        setClubs(clubsData);
      } catch (err) {
        error(err instanceof Error ? err.message : 'Failed to load clubs');
      }
    },
    [error]
  );

  /**
   * Handle state selection
   */
  const handleSelectState = useCallback(
    (stateCode: string) => {
      setSelectedState(stateCode);
      setSelectedClub(null);
      setClubFormMode('add');
      setClubFormData({
        club_name: '',
        club_code: '',
        state_code: stateCode,
        nation: 'MAS',
        alias: '',
      });

      if (stateCode) {
        handleFetchClubsByState(stateCode);
      } else {
        setClubs([]);
      }
    },
    [handleFetchClubsByState]
  );

  /**
   * Handle club selection
   */
  const handleSelectClub = useCallback((club: Club) => {
    setSelectedClub(club);
    setClubFormMode('edit');
    setClubFormData({
      club_name: club.club_name || '',
      club_code: club.club_code || '',
      state_code: club.state_code || '',
      nation: club.nation || 'MAS',
      alias: club.alias || '',
    });
  }, []);

  /**
   * Save club (create or update)
   */
  const handleSaveClub = useCallback(async () => {
    if (!clubFormData.club_name.trim() || !clubFormData.state_code.trim()) {
      error('Club Name and State Code are required');
      return;
    }

    try {
      if (clubFormMode === 'add') {
        await api.createClub(clubFormData);
        success('Club created successfully');
      } else {
        await api.updateClub(selectedClub!.club_name, clubFormData);
        success('Club updated successfully');
      }

      // Refresh clubs list
      if (selectedState) {
        await handleFetchClubsByState(selectedState);
      }

      // Reset form if adding
      if (clubFormMode === 'add') {
        setClubFormData({
          club_name: '',
          club_code: '',
          state_code: selectedState || '',
          nation: 'MAS',
          alias: '',
        });
      }
    } catch (err) {
      error(err instanceof Error ? err.message : 'Failed to save club');
    }
  }, [
    clubFormData,
    clubFormMode,
    selectedClub,
    selectedState,
    handleFetchClubsByState,
    success,
    error,
  ]);

  /**
   * Load coaches for selected club
   */
  const handleLoadCoaches = useCallback(async () => {
    if (!selectedClub) return;

    try {
      const coachesData = await api.getCoachesByClub(selectedClub.club_name);
      setCoaches(coachesData);
    } catch (err) {
      error(err instanceof Error ? err.message : 'Failed to load coaches');
    }
  }, [selectedClub, error]);

  /**
   * Load roster for selected club
   */
  const handleLoadRoster = useCallback(async () => {
    if (!selectedClub) {
      error('Please select a club first');
      return;
    }

    setLoadingRoster(true);
    try {
      const rosterData = await api.getClubRoster(
        selectedClub.club_name,
        selectedMeetForRoster || undefined
      );
      setClubRoster(rosterData);
    } catch (err) {
      error(err instanceof Error ? err.message : 'Failed to load roster');
      setClubRoster([]);
    } finally {
      setLoadingRoster(false);
    }
  }, [selectedClub, selectedMeetForRoster, error]);

  /**
   * Initial load
   */
  useEffect(() => {
    if (isAuthenticated) {
      handleFetchStates();
    }
  }, [isAuthenticated, handleFetchStates]);

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

      {/* Header */}
      <h2 className="text-2xl font-bold text-gray-900">Club Management</h2>

      {/* State and Club Selection */}
      <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select State:
            </label>
            <select
              value={selectedState}
              onChange={e => handleSelectState(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-600"
            >
              <option value="">-- Select State --</option>
              {states.map(state => (
                <option key={state} value={state}>
                  {state}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Club:
            </label>
            <select
              value={selectedClub?.club_name || ''}
              onChange={e => {
                const club = clubs.find(c => c.club_name === e.target.value);
                if (club) handleSelectClub(club);
              }}
              disabled={!selectedState || clubs.length === 0}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-600 disabled:bg-gray-100"
            >
              <option value="">-- Select Club --</option>
              {clubs.map(club => (
                <option key={club.club_name} value={club.club_name}>
                  {club.club_name}
                  {club.club_code ? ` (${club.club_code})` : ''}
                </option>
              ))}
            </select>
          </div>
        </div>

        <Button
          variant="success"
          onClick={() => {
            setSelectedClub(null);
            setClubFormMode('add');
            setClubFormData({
              club_name: '',
              club_code: '',
              state_code: selectedState || '',
              nation: 'MAS',
              alias: '',
            });
          }}
        >
          Add New Club
        </Button>
      </div>

      {/* Club Form */}
      <div className="bg-white border border-slate-200 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          {clubFormMode === 'add' ? 'Add New Club' : 'Edit Club'}
        </h3>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Club Name <span className="text-red-600">*</span>
            </label>
            <input
              type="text"
              value={clubFormData.club_name}
              onChange={e =>
                setClubFormData({ ...clubFormData, club_name: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-600"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Club Code
            </label>
            <input
              type="text"
              value={clubFormData.club_code}
              onChange={e =>
                setClubFormData({
                  ...clubFormData,
                  club_code: e.target.value.toUpperCase(),
                })
              }
              maxLength={5}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-600"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              State Code <span className="text-red-600">*</span>
            </label>
            <input
              type="text"
              value={clubFormData.state_code}
              onChange={e =>
                setClubFormData({
                  ...clubFormData,
                  state_code: e.target.value.toUpperCase(),
                })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-600"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Nation
            </label>
            <input
              type="text"
              value={clubFormData.nation}
              onChange={e =>
                setClubFormData({
                  ...clubFormData,
                  nation: e.target.value.toUpperCase(),
                })
              }
              maxLength={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-600"
            />
          </div>

          <div className="col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Alias
            </label>
            <input
              type="text"
              value={clubFormData.alias}
              onChange={e =>
                setClubFormData({ ...clubFormData, alias: e.target.value })
              }
              placeholder="Alternative name for matching"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-600"
            />
          </div>
        </div>

        <div className="mt-4 flex gap-3">
          <Button variant="primary" onClick={handleSaveClub}>
            {clubFormMode === 'add' ? 'Add Club' : 'Update Club'}
          </Button>

          {clubFormMode === 'edit' && (
            <Button
              variant="secondary"
              onClick={() => {
                setSelectedClub(null);
                setClubFormMode('add');
                setClubFormData({
                  club_name: '',
                  club_code: '',
                  state_code: selectedState || '',
                  nation: 'MAS',
                  alias: '',
                });
              }}
            >
              Cancel
            </Button>
          )}
        </div>
      </div>

      {/* Coaches Section */}
      {selectedClub && (
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Coaches & Managers
          </h3>
          <Button variant="primary" onClick={handleLoadCoaches} size="sm">
            Load Coaches/Managers
          </Button>

          {coaches.length > 0 && (
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-100 border-b-2 border-gray-300">
                    <th className="px-4 py-2 text-left font-semibold">Name</th>
                    <th className="px-4 py-2 text-left font-semibold">Role</th>
                    <th className="px-4 py-2 text-left font-semibold">Email</th>
                    <th className="px-4 py-2 text-left font-semibold">
                      WhatsApp
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {coaches.map(coach => (
                    <tr key={coach.id} className="border-b border-gray-200">
                      <td className="px-4 py-2">{coach.name}</td>
                      <td className="px-4 py-2">{coach.role}</td>
                      <td className="px-4 py-2">{coach.email || '-'}</td>
                      <td className="px-4 py-2">{coach.whatsapp || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Roster Section */}
      {selectedClub && (
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            View Athlete Roster
          </h3>

          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Meet (optional):
              </label>
              <select
                value={selectedMeetForRoster}
                onChange={e => setSelectedMeetForRoster(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-600"
              >
                <option value="">-- All Meets --</option>
                {meets.map(meet => (
                  <option key={meet.id} value={meet.id}>
                    {meet.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-end">
              <Button
                variant="primary"
                onClick={handleLoadRoster}
                loading={loadingRoster}
                disabled={loadingRoster || !selectedClub}
              >
                {loadingRoster ? 'Loading...' : 'Load Roster'}
              </Button>
            </div>
          </div>

          {clubRoster.length > 0 && (
            <div className="mt-4">
              <h4 className="font-semibold text-gray-900 mb-3">
                Roster for {selectedClub.club_name} ({clubRoster.length}{' '}
                athletes)
              </h4>
              <div className="max-h-96 overflow-y-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-100 sticky top-0">
                    <tr className="border-b-2 border-gray-300">
                      <th className="px-4 py-2 text-left font-semibold">
                        Full Name
                      </th>
                      <th className="px-4 py-2 text-left font-semibold">
                        Gender
                      </th>
                      <th className="px-4 py-2 text-left font-semibold">
                        Year Age
                      </th>
                      <th className="px-4 py-2 text-left font-semibold">
                        Day Age
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {clubRoster.map((athlete, idx) => (
                      <tr key={idx} className="border-b border-gray-200">
                        <td className="px-4 py-2">{athlete.fullname}</td>
                        <td className="px-4 py-2">{athlete.gender}</td>
                        <td className="px-4 py-2">
                          {athlete.year_age !== null &&
                          athlete.year_age !== undefined
                            ? athlete.year_age
                            : '-'}
                        </td>
                        <td className="px-4 py-2">
                          {athlete.day_age !== null &&
                          athlete.day_age !== undefined
                            ? athlete.day_age
                            : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ClubManagement;
