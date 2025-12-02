/**
 * Team Selection
 * Admin panel for managing national team selections for international competitions
 */

import React, { useState } from 'react';

export interface TeamSelectionProps {
  isAuthenticated: boolean;
}

// Competition types for selection
const COMPETITIONS = [
  { id: 'seag', name: 'SEA Games', frequency: 'Biennial (odd years)' },
  { id: 'sea_age', name: 'SEA Age Group Championships', frequency: 'Annual' },
  { id: 'asian_games', name: 'Asian Games', frequency: 'Quadrennial' },
  { id: 'asian_age', name: 'Asian Age Group Championships', frequency: 'Annual' },
  { id: 'world_champs', name: 'World Championships', frequency: 'Annual' },
  { id: 'world_juniors', name: 'World Junior Championships', frequency: 'Annual' },
  { id: 'olympics', name: 'Olympic Games', frequency: 'Quadrennial' },
  { id: 'commonwealth', name: 'Commonwealth Games', frequency: 'Quadrennial' },
];

export const TeamSelection: React.FC<TeamSelectionProps> = ({ isAuthenticated }) => {
  const [activeSection, setActiveSection] = useState<'overview' | 'selection' | 'longlist' | 'shortlist'>('overview');

  if (!isAuthenticated) {
    return <div>Please log in to access Team Selection.</div>;
  }

  return (
    <div style={{ padding: '20px' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '24px', fontWeight: 'bold', color: '#111', margin: 0, marginBottom: '8px' }}>
          National Team Selection
        </h2>
        <p style={{ color: '#666', fontSize: '14px', margin: 0 }}>
          Manage athlete selection for international competitions
        </p>
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
          { id: 'overview', label: 'Overview' },
          { id: 'selection', label: 'Selection Criteria' },
          { id: 'longlist', label: 'Long List' },
          { id: 'shortlist', label: 'Short List' },
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

      {/* Overview Section */}
      {activeSection === 'overview' && (
        <div>
          {/* Feature Status Banner */}
          <div style={{
            backgroundColor: '#fef3c7',
            border: '1px solid #fcd34d',
            borderRadius: '8px',
            padding: '16px 20px',
            marginBottom: '24px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <span style={{ fontSize: '18px' }}>[ ! ]</span>
              <strong style={{ color: '#92400e' }}>Feature In Development</strong>
            </div>
            <p style={{ color: '#92400e', fontSize: '14px', margin: 0 }}>
              This panel is being built to support national team selection workflow.
              Core functionality will be added incrementally.
            </p>
          </div>

          {/* What This Panel Will Do */}
          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '24px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
            marginBottom: '24px'
          }}>
            <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#cc0000', marginBottom: '20px' }}>
              Planned Features
            </h3>

            {/* Workflow diagram */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '24px',
              flexWrap: 'wrap',
              gap: '8px'
            }}>
              <WorkflowStep number={1} title="Selection" desc="Filter by time standards" />
              <Arrow />
              <WorkflowStep number={2} title="Long List" desc="Collect information" />
              <Arrow />
              <WorkflowStep number={3} title="Short List" desc="Confirm & pay" />
              <Arrow />
              <WorkflowStep number={4} title="Final Roster" desc="Export & submit" />
            </div>

            {/* Feature list */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
              <FeatureCard
                title="Selection Criteria"
                items={[
                  'Filter athletes by AQUA points threshold',
                  'Filter by qualifying times per event',
                  'View rankings within selection criteria',
                  'Compare to historical selections',
                ]}
                status="planned"
              />
              <FeatureCard
                title="Long List Management"
                items={[
                  'Passport expiration date tracking',
                  'Passport validity alerts (6+ months required)',
                  'Uniform/equipment size collection',
                  'School information (for age-group)',
                  'Medical/dietary requirements',
                ]}
                status="planned"
              />
              <FeatureCard
                title="Short List Finalization"
                items={[
                  'Payment confirmation tracking',
                  'Athlete/parent participation confirmation',
                  'Final roster generation',
                  'Export for federation submission',
                ]}
                status="planned"
              />
              <FeatureCard
                title="Communication"
                items={[
                  'Email selected athletes',
                  'Deadline reminders',
                  'Document collection status',
                  'Payment follow-up',
                ]}
                status="planned"
              />
            </div>
          </div>

          {/* Competitions */}
          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '24px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
          }}>
            <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#cc0000', marginBottom: '20px' }}>
              Supported Competitions
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '12px' }}>
              {COMPETITIONS.map((comp) => (
                <div
                  key={comp.id}
                  style={{
                    padding: '12px 16px',
                    backgroundColor: '#f9f9f9',
                    borderRadius: '6px',
                    border: '1px solid #eee'
                  }}
                >
                  <div style={{ fontWeight: '500', color: '#333' }}>{comp.name}</div>
                  <div style={{ fontSize: '12px', color: '#888' }}>{comp.frequency}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Selection Criteria Section */}
      {activeSection === 'selection' && (
        <div style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          padding: '24px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#cc0000', marginBottom: '20px' }}>
            Selection Criteria Setup
          </h3>
          <p style={{ color: '#666', marginBottom: '20px', fontSize: '14px' }}>
            Define qualifying standards for each competition. Athletes meeting these criteria
            will be eligible for selection.
          </p>

          {/* Placeholder form */}
          <div style={{ display: 'grid', gap: '16px', maxWidth: '500px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500', fontSize: '14px' }}>
                Competition
              </label>
              <select
                style={{ width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid #ddd' }}
                disabled
              >
                <option>Select competition...</option>
                {COMPETITIONS.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500', fontSize: '14px' }}>
                Selection Method
              </label>
              <select
                style={{ width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid #ddd' }}
                disabled
              >
                <option>AQUA Points Threshold</option>
                <option>Qualifying Times</option>
                <option>Top N Rankings</option>
              </select>
            </div>
          </div>

          <div style={{
            marginTop: '24px',
            padding: '20px',
            backgroundColor: '#f9f9f9',
            borderRadius: '8px',
            textAlign: 'center',
            color: '#888'
          }}>
            <p style={{ margin: 0 }}>Selection criteria configuration coming soon</p>
          </div>
        </div>
      )}

      {/* Long List Section */}
      {activeSection === 'longlist' && (
        <div style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          padding: '24px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#cc0000', marginBottom: '8px' }}>
            Long List
          </h3>
          <p style={{ color: '#666', marginBottom: '20px', fontSize: '14px' }}>
            Athletes who meet selection criteria. Collect required information before finalizing.
          </p>

          {/* Info collection checklist */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '12px',
            marginBottom: '24px'
          }}>
            <ChecklistItem label="Passport Expiry Dates" checked={false} />
            <ChecklistItem label="Uniform Sizes" checked={false} />
            <ChecklistItem label="School Information" checked={false} />
            <ChecklistItem label="Medical/Dietary" checked={false} />
            <ChecklistItem label="Travel Documents" checked={false} />
            <ChecklistItem label="Emergency Contacts" checked={false} />
          </div>

          <div style={{
            padding: '40px',
            backgroundColor: '#f9f9f9',
            borderRadius: '8px',
            textAlign: 'center',
            color: '#888'
          }}>
            <p style={{ margin: 0, marginBottom: '8px' }}>No active selections</p>
            <p style={{ margin: 0, fontSize: '13px' }}>Create a selection in the Selection Criteria tab first</p>
          </div>
        </div>
      )}

      {/* Short List Section */}
      {activeSection === 'shortlist' && (
        <div style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          padding: '24px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#cc0000', marginBottom: '8px' }}>
            Short List (Final Team)
          </h3>
          <p style={{ color: '#666', marginBottom: '20px', fontSize: '14px' }}>
            Athletes who have confirmed participation and completed payment.
          </p>

          {/* Confirmation checklist */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '12px',
            marginBottom: '24px'
          }}>
            <ChecklistItem label="Payment Confirmed" checked={false} />
            <ChecklistItem label="Athlete Confirmed" checked={false} />
            <ChecklistItem label="Parent Confirmed" checked={false} />
            <ChecklistItem label="Passport Valid" checked={false} />
          </div>

          <div style={{
            padding: '40px',
            backgroundColor: '#f9f9f9',
            borderRadius: '8px',
            textAlign: 'center',
            color: '#888'
          }}>
            <p style={{ margin: 0, marginBottom: '8px' }}>No finalized selections</p>
            <p style={{ margin: 0, fontSize: '13px' }}>Move athletes from Long List after confirmation</p>
          </div>

          {/* Export button (disabled) */}
          <div style={{ marginTop: '20px' }}>
            <button
              disabled
              style={{
                padding: '10px 20px',
                backgroundColor: '#e5e7eb',
                color: '#9ca3af',
                border: 'none',
                borderRadius: '4px',
                cursor: 'not-allowed',
                fontSize: '14px',
                fontWeight: '500'
              }}
            >
              Export Final Roster
            </button>
          </div>
        </div>
      )}

      {/* Database info */}
      <div style={{
        marginTop: '24px',
        padding: '16px',
        backgroundColor: '#f0fdf4',
        borderRadius: '8px',
        border: '1px solid #86efac'
      }}>
        <h4 style={{ fontSize: '14px', fontWeight: '600', color: '#166534', marginBottom: '8px' }}>
          Database Tables (Planned)
        </h4>
        <ul style={{ fontSize: '13px', color: '#166534', margin: 0, paddingLeft: '20px' }}>
          <li><code>team_selections</code> - Competition, year, selection type, criteria</li>
          <li><code>selection_athletes</code> - Athlete link, status, sizes, passport check, payment, confirmation</li>
          <li>Uses existing <code>athletes</code> table for athlete data and passport_expiry_date</li>
        </ul>
      </div>
    </div>
  );
};

// Helper components
const WorkflowStep: React.FC<{ number: number; title: string; desc: string }> = ({ number, title, desc }) => (
  <div style={{ textAlign: 'center', minWidth: '100px' }}>
    <div style={{
      width: '40px',
      height: '40px',
      borderRadius: '50%',
      backgroundColor: '#cc0000',
      color: 'white',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      margin: '0 auto 8px',
      fontWeight: 'bold'
    }}>
      {number}
    </div>
    <div style={{ fontWeight: '600', fontSize: '14px', color: '#333' }}>{title}</div>
    <div style={{ fontSize: '12px', color: '#888' }}>{desc}</div>
  </div>
);

const Arrow: React.FC = () => (
  <div style={{ color: '#ccc', fontSize: '24px' }}>→</div>
);

const FeatureCard: React.FC<{ title: string; items: string[]; status: 'done' | 'in-progress' | 'planned' }> = ({
  title, items, status
}) => (
  <div style={{
    padding: '16px',
    backgroundColor: '#f9f9f9',
    borderRadius: '8px',
    border: '1px solid #eee'
  }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
      <h4 style={{ margin: 0, fontSize: '15px', fontWeight: '600', color: '#333' }}>{title}</h4>
      <span style={{
        fontSize: '11px',
        padding: '2px 8px',
        borderRadius: '10px',
        backgroundColor: status === 'done' ? '#dcfce7' : status === 'in-progress' ? '#fef3c7' : '#f3f4f6',
        color: status === 'done' ? '#166534' : status === 'in-progress' ? '#92400e' : '#6b7280'
      }}>
        {status === 'done' ? 'Done' : status === 'in-progress' ? 'In Progress' : 'Planned'}
      </span>
    </div>
    <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '13px', color: '#666' }}>
      {items.map((item, i) => <li key={i} style={{ marginBottom: '4px' }}>{item}</li>)}
    </ul>
  </div>
);

const ChecklistItem: React.FC<{ label: string; checked: boolean }> = ({ label, checked }) => (
  <div style={{
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '10px 12px',
    backgroundColor: checked ? '#f0fdf4' : '#f9f9f9',
    borderRadius: '6px',
    border: `1px solid ${checked ? '#86efac' : '#eee'}`
  }}>
    <span style={{
      width: '18px',
      height: '18px',
      borderRadius: '4px',
      border: `2px solid ${checked ? '#10b981' : '#ddd'}`,
      backgroundColor: checked ? '#10b981' : 'white',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: 'white',
      fontSize: '12px'
    }}>
      {checked && 'OK'}
    </span>
    <span style={{ fontSize: '13px', color: checked ? '#166534' : '#666' }}>{label}</span>
  </div>
);

export default TeamSelection;
