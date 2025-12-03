/**
 * MAP - Malaysia Age Points Landing Page
 * Reference links and resources
 */

import React from 'react';
import { useRouter } from 'next/router';

export default function MapPage() {
  const router = useRouter();

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f9fafb', padding: '2rem' }}>
      {/* Header */}
      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 'bold', color: '#111827' }}>
            MAP - Malaysia Age Points
          </h1>
          <button
            onClick={() => router.push('/')}
            style={{
              padding: '6px 16px',
              backgroundColor: '#cc0000',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontSize: '0.9rem',
              cursor: 'pointer',
              fontWeight: '600'
            }}
          >
            Back to Main
          </button>
        </div>

        {/* Reference Links */}
        <div style={{ backgroundColor: '#fff', borderRadius: '8px', padding: '1.5rem', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '1rem', color: '#374151' }}>
            Reference Links
          </h2>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            <li style={{ marginBottom: '0.75rem' }}>
              <a
                href="https://data.usaswimming.org/datahub/usas/timeseventrank"
                target="_blank"
                rel="noopener noreferrer"
                style={{ color: '#cc0000', textDecoration: 'none', fontWeight: '500' }}
              >
                USA Times Database
              </a>
            </li>
            <li style={{ marginBottom: '0.75rem' }}>
              <a
                href="https://data.usaswimming.org/datahub/alltimetop100search"
                target="_blank"
                rel="noopener noreferrer"
                style={{ color: '#cc0000', textDecoration: 'none', fontWeight: '500' }}
              >
                USA Swimming Top 100
              </a>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
