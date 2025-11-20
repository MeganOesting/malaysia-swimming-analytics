/**
 * Manual Entry Feature Component
 * 3-step wizard for manually entering meet results
 */

import React, { useState, useCallback, useEffect } from 'react';
import {
  Athlete,
  SelectedAthlete,
  ManualResult,
  ManualResultPayload,
} from '../../shared/types/admin';
import { Button, AlertBox, SearchBox } from '../../shared/components';
import { useNotification } from '../../shared/hooks';
import { searchAthletes } from '../athlete-management/api';
import * as api from './api';

export interface ManualEntryProps {
  isAuthenticated: boolean;
}

export const ManualEntry: React.FC<ManualEntryProps> = ({
  isAuthenticated,
}) => {
  // Step state
  const [currentStep, setCurrentStep] = useState<1 | 2 | 3>(1);

  // Step 1: Athlete selection
  const [athleteSearchQuery, setAthleteSearchQuery] = useState('');
  const [athleteSearchResults, setAthleteSearchResults] = useState<Athlete[]>([]);
  const [searchingAthletes, setSearchingAthletes] = useState(false);
  const [selectedAthletes, setSelectedAthletes] = useState<SelectedAthlete[]>([]);

  // Step 2: Meet info
  const [meetName, setMeetName] = useState('');
  const [meetDate, setMeetDate] = useState('');
  const [meetCity, setMeetCity] = useState('');
  const [meetCourse, setMeetCourse] = useState<'LCM' | 'SCM'>('LCM');
  const [meetAlias, setMeetAlias] = useState('');
  const [selectedEvents, setSelectedEvents] = useState<
    Array<{ distance: number; stroke: string; gender: string }>
  >([]);

  // Step 3: Time entry
  const [manualResults, setManualResults] = useState<ManualResult[]>([]);
  const [submitting, setSubmitting] = useState(false);

  // Notifications
  const { notifications, success, error, clear } = useNotification();

  /**
   * Search athletes (debounced)
   */
  useEffect(() => {
    if (!athleteSearchQuery.trim()) {
      setAthleteSearchResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      setSearchingAthletes(true);
      try {
        const results = await searchAthletes(athleteSearchQuery);
        setAthleteSearchResults(results);
      } catch (err) {
        error(err instanceof Error ? err.message : 'Search failed');
      } finally {
        setSearchingAthletes(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [athleteSearchQuery, error]);

  /**
   * Add athlete to selection
   */
  const handleAddAthlete = useCallback((athlete: Athlete) => {
    setSelectedAthletes(prev => {
      const exists = prev.find(a => a.id === athlete.id);
      if (exists) {
        return prev.filter(a => a.id !== athlete.id);
      }
      return [...prev, { ...athlete, selected: true }];
    });
  }, []);

  /**
   * Remove athlete from selection
   */
  const handleRemoveAthlete = useCallback((athleteId: string) => {
    setSelectedAthletes(prev => prev.filter(a => a.id !== athleteId));
  }, []);

  /**
   * Go to Step 2
   */
  const handleNextToStep2 = useCallback(() => {
    if (selectedAthletes.length === 0) {
      error('Please select at least one athlete');
      return;
    }
    setCurrentStep(2);
  }, [selectedAthletes, error]);

  /**
   * Go to Step 3
   */
  const handleNextToStep3 = useCallback(() => {
    if (!meetName || !meetDate || selectedEvents.length === 0) {
      error('Please fill in meet name, date, and select at least one event');
      return;
    }

    // Generate result entries for all athletes and events
    const results: ManualResult[] = [];
    selectedAthletes.forEach(athlete => {
      selectedEvents.forEach(event => {
        results.push({
          athlete_id: athlete.id,
          athlete_name: athlete.name,
          event_distance: event.distance,
          event_stroke: event.stroke,
          event_gender: event.gender,
          time_string: '',
          place: null,
        });
      });
    });

    setManualResults(results);
    setCurrentStep(3);
  }, [meetName, meetDate, selectedEvents, selectedAthletes, error]);

  /**
   * Submit manual results
   */
  const handleSubmitManualResults = useCallback(async () => {
    // Validate all times are entered
    const emptyTimes = manualResults.filter(r => !r.time_string.trim());
    if (emptyTimes.length > 0) {
      error(`Please enter times for all ${emptyTimes.length} remaining results`);
      return;
    }

    setSubmitting(true);
    try {
      const payload: ManualResultPayload[] = manualResults.map(r => ({
        athlete_id: r.athlete_id,
        distance: r.event_distance,
        stroke: r.event_stroke,
        event_gender: r.event_gender,
        time_string: r.time_string,
        place: r.place,
      }));

      const response = await api.submitManualResults({
        meet_name: meetName,
        meet_date: meetDate,
        meet_city: meetCity,
        meet_course: meetCourse,
        meet_alias: meetAlias,
        results: payload,
      });

      success(
        `Successfully submitted ${response.results_inserted} results! Meet ID: ${response.meet_id}`
      );

      // Reset wizard
      setTimeout(() => {
        setCurrentStep(1);
        setSelectedAthletes([]);
        setAthleteSearchQuery('');
        setAthleteSearchResults([]);
        setMeetName('');
        setMeetDate('');
        setMeetCity('');
        setMeetCourse('LCM');
        setMeetAlias('');
        setSelectedEvents([]);
        setManualResults([]);
      }, 2000);
    } catch (err) {
      error(err instanceof Error ? err.message : 'Failed to submit results');
    } finally {
      setSubmitting(false);
    }
  }, [
    manualResults,
    meetName,
    meetDate,
    meetCity,
    meetCourse,
    meetAlias,
    success,
    error,
  ]);

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

      {/* Step Indicator */}
      <div className="flex gap-2">
        <div
          className={`flex-1 text-center p-4 rounded ${
            currentStep >= 1
              ? 'bg-red-600 text-white'
              : 'bg-gray-200 text-gray-600'
          } ${currentStep === 1 ? 'font-semibold' : ''}`}
        >
          Step 1: Select Athletes
        </div>
        <div
          className={`flex-1 text-center p-4 rounded ${
            currentStep >= 2
              ? 'bg-red-600 text-white'
              : 'bg-gray-200 text-gray-600'
          } ${currentStep === 2 ? 'font-semibold' : ''}`}
        >
          Step 2: Meet Info
        </div>
        <div
          className={`flex-1 text-center p-4 rounded ${
            currentStep >= 3
              ? 'bg-red-600 text-white'
              : 'bg-gray-200 text-gray-600'
          } ${currentStep === 3 ? 'font-semibold' : ''}`}
        >
          Step 3: Enter Times
        </div>
      </div>

      {/* Step 1: Athlete Selection */}
      {currentStep === 1 && (
        <div className="space-y-4">
          <h2 className="text-2xl font-bold text-gray-900">Select Athletes</h2>

          {/* Search */}
          <div>
            <SearchBox
              label="Search Athletes (type name)"
              placeholder="Start typing athlete name..."
              value={athleteSearchQuery}
              onChange={e => setAthleteSearchQuery(e.target.value)}
            />
            {searchingAthletes && (
              <p className="mt-2 text-sm text-gray-600">Searching...</p>
            )}
          </div>

          {/* Search Results */}
          {athleteSearchResults.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-lg p-4">
              <h3 className="text-lg font-semibold mb-3">Search Results:</h3>
              <div className="max-h-72 overflow-y-auto space-y-2">
                {athleteSearchResults.map(athlete => (
                  <div
                    key={athlete.id}
                    onClick={() => handleAddAthlete(athlete)}
                    className={`p-3 rounded cursor-pointer flex justify-between items-center ${
                      selectedAthletes.find(a => a.id === athlete.id)
                        ? 'bg-green-50 border-2 border-green-600'
                        : 'bg-gray-50 border border-gray-200 hover:bg-gray-100'
                    }`}
                  >
                    <div>
                      <div className="font-medium">{athlete.name}</div>
                      <div className="text-sm text-gray-600">
                        {athlete.gender} | {athlete.birth_date || 'No DOB'} |{' '}
                        {athlete.club_name || 'No club'}
                      </div>
                    </div>
                    {selectedAthletes.find(a => a.id === athlete.id) && (
                      <span className="text-green-600 font-semibold">
                        ✓ Selected
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Selected Athletes */}
          {selectedAthletes.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-lg p-4">
              <h3 className="text-lg font-semibold mb-3">
                Selected Athletes ({selectedAthletes.length}):
              </h3>
              <div className="space-y-2">
                {selectedAthletes.map(athlete => (
                  <div
                    key={athlete.id}
                    className="p-3 bg-green-50 rounded flex justify-between items-center"
                  >
                    <div>
                      <div className="font-medium">{athlete.name}</div>
                      <div className="text-sm text-gray-600">
                        {athlete.gender} | {athlete.birth_date || 'No DOB'}
                      </div>
                    </div>
                    <Button
                      size="sm"
                      variant="danger"
                      onClick={() => handleRemoveAthlete(athlete.id)}
                    >
                      Remove
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <Button
            onClick={handleNextToStep2}
            disabled={selectedAthletes.length === 0}
            fullWidth
          >
            Next: Enter Meet Information ({selectedAthletes.length} athlete
            {selectedAthletes.length !== 1 ? 's' : ''} selected)
          </Button>
        </div>
      )}

      {/* Step 2: Meet Information */}
      {currentStep === 2 && (
        <div className="space-y-4">
          <h2 className="text-2xl font-bold text-gray-900">Meet Information</h2>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Meet Name <span className="text-red-600">*</span>
              </label>
              <input
                type="text"
                value={meetName}
                onChange={e => setMeetName(e.target.value)}
                placeholder="e.g., 67th Malaysian Open Championships"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-600"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Meet Date <span className="text-red-600">*</span>
              </label>
              <input
                type="date"
                value={meetDate}
                onChange={e => setMeetDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-600"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                City
              </label>
              <input
                type="text"
                value={meetCity}
                onChange={e => setMeetCity(e.target.value)}
                placeholder="e.g., Kuala Lumpur"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-600"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Course <span className="text-red-600">*</span>
              </label>
              <select
                value={meetCourse}
                onChange={e => setMeetCourse(e.target.value as 'LCM' | 'SCM')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-600"
              >
                <option value="LCM">LCM (Long Course Meters)</option>
                <option value="SCM">SCM (Short Course Meters)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Alias/Code (optional)
            </label>
            <input
              type="text"
              value={meetAlias}
              onChange={e => setMeetAlias(e.target.value)}
              placeholder="e.g., MO25, MIAG25"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-600"
            />
          </div>

          {/* Event Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Events <span className="text-red-600">*</span>
            </label>
            <div className="border border-gray-300 rounded-lg p-4 max-h-72 overflow-y-auto">
              {[50, 100, 200, 400, 800, 1500].map(distance =>
                ['FR', 'BK', 'BR', 'BU', 'IM'].map(stroke =>
                  ['M', 'F'].map(gender => {
                    const eventKey = `${distance}_${stroke}_${gender}`;
                    const isSelected = selectedEvents.some(
                      e =>
                        e.distance === distance &&
                        e.stroke === stroke &&
                        e.gender === gender
                    );
                    return (
                      <label
                        key={eventKey}
                        className={`flex items-center p-2 rounded cursor-pointer mb-1 ${
                          isSelected ? 'bg-blue-50' : 'hover:bg-gray-50'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={e => {
                            if (e.target.checked) {
                              setSelectedEvents([
                                ...selectedEvents,
                                { distance, stroke, gender },
                              ]);
                            } else {
                              setSelectedEvents(
                                selectedEvents.filter(
                                  ev =>
                                    !(
                                      ev.distance === distance &&
                                      ev.stroke === stroke &&
                                      ev.gender === gender
                                    )
                                )
                              );
                            }
                          }}
                          className="mr-2"
                        />
                        <span>
                          {gender} {distance}m {stroke}
                        </span>
                      </label>
                    );
                  })
                )
              )}
            </div>
          </div>

          <div className="flex gap-4">
            <Button
              variant="secondary"
              onClick={() => setCurrentStep(1)}
              fullWidth
            >
              ← Back
            </Button>
            <Button
              onClick={handleNextToStep3}
              disabled={!meetName || !meetDate || selectedEvents.length === 0}
              fullWidth
            >
              Next: Enter Times ({selectedEvents.length} event
              {selectedEvents.length !== 1 ? 's' : ''} selected)
            </Button>
          </div>
        </div>
      )}

      {/* Step 3: Time Entry */}
      {currentStep === 3 && (
        <div className="space-y-4">
          <h2 className="text-2xl font-bold text-gray-900">Enter Times</h2>
          <p className="text-gray-600">
            Meet: <strong>{meetName}</strong> | Date:{' '}
            <strong>{meetDate}</strong> | Course: <strong>{meetCourse}</strong>
          </p>

          <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
            <div className="overflow-x-auto max-h-96">
              <table className="w-full text-sm">
                <thead className="bg-slate-100 sticky top-0">
                  <tr className="border-b-2 border-slate-300">
                    <th className="px-4 py-3 text-left font-semibold">
                      Athlete
                    </th>
                    <th className="px-4 py-3 text-left font-semibold">Event</th>
                    <th className="px-4 py-3 text-left font-semibold">
                      Time (MM:SS.ss or SS.ss)
                    </th>
                    <th className="px-4 py-3 text-left font-semibold">Place</th>
                  </tr>
                </thead>
                <tbody>
                  {manualResults.map((result, idx) => (
                    <tr key={idx} className="border-b border-slate-200">
                      <td className="px-4 py-3">{result.athlete_name}</td>
                      <td className="px-4 py-3">
                        {result.event_gender} {result.event_distance}m{' '}
                        {result.event_stroke}
                      </td>
                      <td className="px-4 py-3">
                        <input
                          type="text"
                          value={result.time_string}
                          onChange={e => {
                            const newResults = [...manualResults];
                            newResults[idx].time_string = e.target.value;
                            setManualResults(newResults);
                          }}
                          placeholder="e.g., 1:23.45 or 23.45"
                          className="w-full px-2 py-1 border border-gray-300 rounded"
                          required
                        />
                      </td>
                      <td className="px-4 py-3">
                        <input
                          type="number"
                          value={result.place || ''}
                          onChange={e => {
                            const newResults = [...manualResults];
                            newResults[idx].place = e.target.value
                              ? parseInt(e.target.value)
                              : null;
                            setManualResults(newResults);
                          }}
                          placeholder="Optional"
                          min="1"
                          className="w-full px-2 py-1 border border-gray-300 rounded"
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="flex gap-4">
            <Button
              variant="secondary"
              onClick={() => setCurrentStep(2)}
              fullWidth
            >
              ← Back
            </Button>
            <Button
              variant="success"
              onClick={handleSubmitManualResults}
              disabled={
                submitting ||
                manualResults.some(r => !r.time_string.trim())
              }
              loading={submitting}
              fullWidth
            >
              {submitting
                ? 'Submitting...'
                : `Submit ${manualResults.length} Results`}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ManualEntry;
