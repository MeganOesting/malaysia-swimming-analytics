/**
 * Registration Management
 * Admin panel for managing member registrations, tracking payments, and viewing statistics
 */

import React, { useState } from 'react';

export interface RegistrationManagementProps {
  isAuthenticated: boolean;
}

export const RegistrationManagement: React.FC<RegistrationManagementProps> = ({ isAuthenticated }) => {
  const [activeSection, setActiveSection] = useState<'dashboard' | 'accounts' | 'lapsed' | 'payments'>('dashboard');

  // Registration portal URL - update this when deployed
  const REGISTRATION_PORTAL_URL = 'http://localhost:3001';

  if (!isAuthenticated) {
    return <div>Please log in to access Registration Management.</div>;
  }

  return (
    <div style={{ padding: '20px' }}>
      {/* Header with link to registration form */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '24px',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        <h2 style={{ fontSize: '24px', fontWeight: 'bold', color: '#111', margin: 0 }}>
          Registration Management
        </h2>
        <a
          href={REGISTRATION_PORTAL_URL}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 20px',
            backgroundColor: '#cc0000',
            color: 'white',
            textDecoration: 'none',
            borderRadius: '6px',
            fontWeight: '600',
            fontSize: '14px',
          }}
          onMouseOver={(e) => (e.currentTarget.style.backgroundColor = '#aa0000')}
          onMouseOut={(e) => (e.currentTarget.style.backgroundColor = '#cc0000')}
        >
          Open Registration Form
          <span style={{ fontSize: '12px' }}>[External Link]</span>
        </a>
      </div>

      {/* Sub-navigation */}
      <div style={{
        display: 'flex',
        gap: '8px',
        marginBottom: '24px',
        borderBottom: '2px solid #eee',
        paddingBottom: '12px'
      }}>
        {[
          { id: 'dashboard', label: 'Dashboard' },
          { id: 'accounts', label: 'Accounts' },
          { id: 'lapsed', label: 'Lapsed Members' },
          { id: 'payments', label: 'Payments' },
        ].map((section) => (
          <button
            key={section.id}
            onClick={() => setActiveSection(section.id as any)}
            style={{
              padding: '8px 16px',
              backgroundColor: activeSection === section.id ? '#cc0000' : 'transparent',
              color: activeSection === section.id ? 'white' : '#666',
              border: activeSection === section.id ? 'none' : '1px solid #ddd',
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: activeSection === section.id ? '600' : '400',
              fontSize: '14px',
            }}
          >
            {section.label}
          </button>
        ))}
      </div>

      {/* Dashboard Section */}
      {activeSection === 'dashboard' && (
        <div>
          {/* Stats Grid */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '16px',
            marginBottom: '24px'
          }}>
            <StatCard title="Total Accounts" value="--" subtitle="Parent/Guardian accounts" color="#3b82f6" />
            <StatCard title="2026 Registered" value="--" subtitle="Athletes registered" color="#10b981" />
            <StatCard title="Pending Payment" value="--" subtitle="Awaiting payment" color="#f59e0b" />
            <StatCard title="Lapsed Members" value="--" subtitle="Not renewed from 2025" color="#ef4444" />
          </div>

          {/* Registration by State */}
          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '20px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
            marginBottom: '24px'
          }}>
            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', color: '#333' }}>
              Registrations by State
            </h3>
            <p style={{ color: '#888', fontSize: '14px' }}>
              Connect to Supabase to load registration statistics.
            </p>
            {/* Placeholder table */}
            <table style={{ width: '100%', marginTop: '16px', fontSize: '14px' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #eee' }}>
                  <th style={{ textAlign: 'left', padding: '8px', color: '#666' }}>State</th>
                  <th style={{ textAlign: 'right', padding: '8px', color: '#666' }}>Total</th>
                  <th style={{ textAlign: 'right', padding: '8px', color: '#666' }}>Complete</th>
                  <th style={{ textAlign: 'right', padding: '8px', color: '#666' }}>Pending</th>
                  <th style={{ textAlign: 'right', padding: '8px', color: '#666' }}>Rate</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '20px', color: '#888' }}>
                    No data available yet
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Quick Actions */}
          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '20px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
          }}>
            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', color: '#333' }}>
              Quick Actions
            </h3>
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              <ActionButton label="Export All Registrations" disabled />
              <ActionButton label="Send Reminder Emails" disabled />
              <ActionButton label="Generate Report" disabled />
            </div>
          </div>
        </div>
      )}

      {/* Accounts Section */}
      {activeSection === 'accounts' && (
        <div style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          padding: '20px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', color: '#333' }}>
            Account Management
          </h3>
          <p style={{ color: '#666', marginBottom: '16px', fontSize: '14px' }}>
            Search and manage parent/guardian accounts. Each account can have multiple athletes linked.
          </p>

          {/* Search */}
          <div style={{ marginBottom: '20px' }}>
            <input
              type="text"
              placeholder="Search by email, name, or phone..."
              style={{
                width: '100%',
                maxWidth: '400px',
                padding: '10px 12px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '14px'
              }}
              disabled
            />
          </div>

          {/* Placeholder message */}
          <div style={{
            padding: '40px',
            textAlign: 'center',
            backgroundColor: '#f9f9f9',
            borderRadius: '8px',
            color: '#888'
          }}>
            <p style={{ fontSize: '16px', marginBottom: '8px' }}>Account search coming soon</p>
            <p style={{ fontSize: '13px' }}>Connect to Supabase and create accounts table first</p>
          </div>
        </div>
      )}

      {/* Lapsed Members Section */}
      {activeSection === 'lapsed' && (
        <div style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          padding: '20px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', color: '#333' }}>
            Lapsed Members
          </h3>
          <p style={{ color: '#666', marginBottom: '16px', fontSize: '14px' }}>
            Members who registered in 2025 but have not yet renewed for 2026.
          </p>

          {/* Filter options */}
          <div style={{ display: 'flex', gap: '12px', marginBottom: '20px', flexWrap: 'wrap' }}>
            <select style={{ padding: '8px 12px', borderRadius: '4px', border: '1px solid #ddd' }} disabled>
              <option>All States</option>
            </select>
            <select style={{ padding: '8px 12px', borderRadius: '4px', border: '1px solid #ddd' }} disabled>
              <option>All Clubs</option>
            </select>
            <select style={{ padding: '8px 12px', borderRadius: '4px', border: '1px solid #ddd' }} disabled>
              <option>All Age Groups</option>
            </select>
          </div>

          {/* Placeholder */}
          <div style={{
            padding: '40px',
            textAlign: 'center',
            backgroundColor: '#f9f9f9',
            borderRadius: '8px',
            color: '#888'
          }}>
            <p style={{ fontSize: '16px', marginBottom: '8px' }}>Lapsed member tracking coming soon</p>
            <p style={{ fontSize: '13px' }}>Requires 2025 registration data to compare</p>
          </div>
        </div>
      )}

      {/* Payments Section */}
      {activeSection === 'payments' && (
        <div style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          padding: '20px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', color: '#333' }}>
            Payment Tracking
          </h3>
          <p style={{ color: '#666', marginBottom: '16px', fontSize: '14px' }}>
            View and manage registration payments. Integration with RevenueMonster pending.
          </p>

          {/* Payment stats */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
            gap: '12px',
            marginBottom: '20px'
          }}>
            <div style={{ padding: '16px', backgroundColor: '#f0fdf4', borderRadius: '6px', textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#10b981' }}>--</div>
              <div style={{ fontSize: '12px', color: '#666' }}>Completed</div>
            </div>
            <div style={{ padding: '16px', backgroundColor: '#fffbeb', borderRadius: '6px', textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#f59e0b' }}>--</div>
              <div style={{ fontSize: '12px', color: '#666' }}>Pending</div>
            </div>
            <div style={{ padding: '16px', backgroundColor: '#fef2f2', borderRadius: '6px', textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#ef4444' }}>--</div>
              <div style={{ fontSize: '12px', color: '#666' }}>Failed</div>
            </div>
          </div>

          {/* Placeholder */}
          <div style={{
            padding: '40px',
            textAlign: 'center',
            backgroundColor: '#f9f9f9',
            borderRadius: '8px',
            color: '#888'
          }}>
            <p style={{ fontSize: '16px', marginBottom: '8px' }}>Payment integration coming soon</p>
            <p style={{ fontSize: '13px' }}>RevenueMonster API research required (B002)</p>
          </div>
        </div>
      )}

      {/* Info box */}
      <div style={{
        marginTop: '24px',
        padding: '16px',
        backgroundColor: '#eff6ff',
        borderRadius: '8px',
        border: '1px solid #bfdbfe'
      }}>
        <h4 style={{ fontSize: '14px', fontWeight: '600', color: '#1e40af', marginBottom: '8px' }}>
          Registration System Status
        </h4>
        <ul style={{ fontSize: '13px', color: '#1e40af', margin: 0, paddingLeft: '20px' }}>
          <li>Database schema created (scripts/registration_schema.sql)</li>
          <li>Registration portal built (registration-portal/)</li>
          <li>Pending: Deploy to Vercel, connect Supabase, configure RevenueMonster</li>
          <li>Member types: Athletes, Coaches, Technical Officials</li>
          <li>Athletes can register for: Swimming, Artistic Swimming, Open Water, Water Polo, Diving</li>
          <li>Divisions: Open, Para, Masters</li>
        </ul>
      </div>
    </div>
  );
};

// Helper components
const StatCard: React.FC<{ title: string; value: string; subtitle: string; color: string }> = ({
  title, value, subtitle, color
}) => (
  <div style={{
    backgroundColor: 'white',
    borderRadius: '8px',
    padding: '20px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    borderLeft: `4px solid ${color}`
  }}>
    <div style={{ fontSize: '12px', color: '#666', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
      {title}
    </div>
    <div style={{ fontSize: '32px', fontWeight: 'bold', color: color, margin: '8px 0' }}>
      {value}
    </div>
    <div style={{ fontSize: '13px', color: '#888' }}>
      {subtitle}
    </div>
  </div>
);

const ActionButton: React.FC<{ label: string; disabled?: boolean; onClick?: () => void }> = ({
  label, disabled, onClick
}) => (
  <button
    onClick={onClick}
    disabled={disabled}
    style={{
      padding: '10px 16px',
      backgroundColor: disabled ? '#e5e7eb' : '#cc0000',
      color: disabled ? '#9ca3af' : 'white',
      border: 'none',
      borderRadius: '4px',
      cursor: disabled ? 'not-allowed' : 'pointer',
      fontSize: '14px',
      fontWeight: '500'
    }}
  >
    {label}
  </button>
);

export default RegistrationManagement;
