/**
 * Admin Panel Orchestrator
 * Main component that manages authentication and routes between all admin features
 * Replaces the old monolithic src/pages/admin.tsx
 */

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAdminAuth, useNotification } from './shared/hooks';
import { AlertBox, Button } from './shared/components';

// Import all feature components
import { AthleteManagement } from './features/athlete-management';
import { MeetManagement } from './features/meet-management';
import { ManualEntry } from './features/manual-entry';
import { ClubManagement } from './features/club-management';
import { CoachManagement } from './features/coach-management';

type TabType = 'manual' | 'manage' | 'athleteinfo' | 'clubinfo' | 'coachmanagement';

interface TabConfig {
  id: TabType;
  label: string;
  icon: string;
  component: React.ComponentType<{ isAuthenticated: boolean }>;
}

const TABS: TabConfig[] = [
  {
    id: 'manage',
    label: 'Meet Management',
    icon: '',
    component: MeetManagement,
  },
  {
    id: 'athleteinfo',
    label: 'Athlete Management',
    icon: '',
    component: AthleteManagement,
  },
  {
    id: 'clubinfo',
    label: 'Club Management',
    icon: '',
    component: ClubManagement,
  },
  {
    id: 'coachmanagement',
    label: 'Coach Management',
    icon: '',
    component: CoachManagement,
  },
  {
    id: 'manual',
    label: 'Manual Entry',
    icon: '',
    component: ManualEntry,
  },
];

export interface AdminProps {
  initialTab?: TabType;
}

/**
 * Main Admin Panel Component
 * Handles authentication and feature routing
 */
export const Admin: React.FC<AdminProps> = ({ initialTab = 'manage' }) => {
  // Router and Auth state
  const router = useRouter();
  const auth = useAdminAuth();
  const [passwordInput, setPasswordInput] = useState('');

  // UI state
  const [activeTab, setActiveTab] = useState<TabType>(initialTab);
  const [authenticating, setAuthenticating] = useState(false);

  // Notifications
  const { notifications, error, clear } = useNotification();

  /**
   * Handle login
   */
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!passwordInput.trim()) {
      error('Please enter a password');
      return;
    }

    setAuthenticating(true);
    try {
      const success = await auth.authenticate(passwordInput);
      if (success) {
        setPasswordInput('');
      }
    } finally {
      setAuthenticating(false);
    }
  };

  /**
   * Render login screen
   */
  if (!auth.isAuthenticated) {
    return (
      <div style={{ minHeight: '100vh', backgroundColor: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
        <div style={{ backgroundColor: '#ffffff', borderRadius: '0.5rem', boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)', padding: '2rem', width: '100%', maxWidth: '28rem' }}>
          {/* Logo/Title */}
          <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#111827', marginBottom: '0.5rem' }}>
              Malaysia Swimming Analytics
            </h1>
          </div>

          {/* Errors */}
          {notifications.map(notification => (
            <AlertBox
              key={notification.id}
              type={notification.type}
              message={notification.message}
              onClose={() => clear(notification.id)}
            />
          ))}

          {/* Login Form */}
          <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <input
                type="password"
                value={passwordInput}
                onChange={(e) => setPasswordInput(e.target.value)}
                placeholder="Enter admin password"
                disabled={authenticating}
                style={{
                  width: '100%',
                  padding: '0.5rem 1rem',
                  border: '1px solid #d1d5db',
                  borderRadius: '0.5rem',
                  fontSize: '1rem',
                  outline: 'none',
                  backgroundColor: authenticating ? '#f3f4f6' : '#ffffff'
                }}
                onFocus={(e) => e.target.style.boxShadow = '0 0 0 3px rgba(220, 38, 38, 0.1)'}
                onBlur={(e) => e.target.style.boxShadow = 'none'}
                autoFocus
              />
            </div>

            <button
              type="submit"
              disabled={authenticating}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#cc0000',
                color: 'white',
                border: 'none',
                borderRadius: '0.5rem',
                fontWeight: '600',
                fontSize: '1rem',
                cursor: authenticating ? 'not-allowed' : 'pointer',
                opacity: authenticating ? 0.7 : 1,
                width: '100%'
              }}
              onMouseEnter={(e) => {
                if (!authenticating) {
                  (e.target as HTMLButtonElement).style.backgroundColor = '#990000';
                }
              }}
              onMouseLeave={(e) => {
                if (!authenticating) {
                  (e.target as HTMLButtonElement).style.backgroundColor = '#cc0000';
                }
              }}
            >
              {authenticating ? 'Authenticating...' : 'Login'}
            </button>
          </form>

          {/* Footer */}
          <p style={{ textAlign: 'center', fontSize: '0.875rem', color: '#9ca3af', marginTop: '1.5rem', marginBottom: '1rem' }}>
            Secure admin access only
          </p>

          {/* Back to Main Button */}
          <div style={{ display: 'flex', justifyContent: 'center' }}>
            <button
              type="button"
              onClick={() => router.push('/')}
              style={{
                padding: '2px 10px',
                backgroundColor: '#cc0000',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                fontSize: '0.9em',
                cursor: 'pointer',
                fontWeight: '600'
              }}
              onMouseEnter={(e) => {
                (e.target as HTMLButtonElement).style.backgroundColor = '#990000';
              }}
              onMouseLeave={(e) => {
                (e.target as HTMLButtonElement).style.backgroundColor = '#cc0000';
              }}
            >
              Back to Main
            </button>
          </div>
        </div>
      </div>
    );
  }

  /**
   * Render authenticated admin panel
   */
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Malaysia Swimming Admin Panel
              </h1>
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => router.push('/')}
              >
                Back to Main
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => auth.logout()}
              >
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <div style={{ display: 'flex', gap: '0.5rem', padding: '1rem', backgroundColor: '#fff', flexWrap: 'wrap' }}>
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            type="button"
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: activeTab === tab.id ? '#cc0000' : '#ee0000',
              color: 'white',
              border: activeTab === tab.id ? 'none' : '1px solid #cc0000',
              borderBottom: activeTab === tab.id ? '3px solid #cc0000' : '3px solid transparent',
              borderRadius: '4px 4px 0 0',
              cursor: 'pointer',
              fontSize: '0.9rem',
              fontWeight: activeTab === tab.id ? '700' : '400'
            }}
          >
            <span style={{ marginRight: '0.5rem' }}>{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content Area */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Notifications */}
        {notifications.map(notification => (
          <AlertBox
            key={notification.id}
            type={notification.type}
            message={notification.message}
            onClose={() => clear(notification.id)}
          />
        ))}

        {/* Active Tab Content */}
        {TABS.map((tab) => {
          const Component = tab.component;
          return (
            <div
              key={tab.id}
              style={{ display: activeTab === tab.id ? 'block' : 'none' }}
            >
              <Component isAuthenticated={auth.isAuthenticated} />
            </div>
          );
        })}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <p className="text-center text-sm text-gray-600">
            © {new Date().getFullYear()} Malaysia Swimming Analytics. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
};

/**
 * Export as default for easy page import
 */
export default Admin;
