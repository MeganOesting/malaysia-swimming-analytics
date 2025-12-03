import React, { useState } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { supabase } from '../lib/supabase';

// Phone country codes (Malaysia first)
const COUNTRY_CODES = [
  { code: '+60', country: 'MY' },
  { code: '+65', country: 'SG' },
  { code: '+1', country: 'US/CA' },
  { code: '+44', country: 'UK' },
  { code: '+61', country: 'AU' },
  { code: '+86', country: 'CN' },
  { code: '+82', country: 'KR' },
  { code: '+81', country: 'JP' },
  { code: '+91', country: 'IN' },
  { code: '+62', country: 'ID' },
  { code: '+63', country: 'PH' },
  { code: '+66', country: 'TH' },
  { code: '+84', country: 'VN' },
  { code: '+852', country: 'HK' },
  { code: '+886', country: 'TW' },
  { code: '+971', country: 'AE' },
  { code: '+673', country: 'BN' },
];

// Member type interface - includes all athlete fields from database
interface Member {
  id: string;
  fullname: string;
  birthdate: string;
  gender: string;
  // Athlete-specific fields from database
  club_code: string;
  club_name: string;
  state_code: string;
  nation: string;
  ic_number: string;
  passport_number: string;
  passport_expiry_date: string;
  phone: string;
  email: string;
  // Registration type selections
  types: string[];
  disciplines: string[];
  divisions: string[];
}

// Malaysian states
const STATES = [
  'Johor', 'Kedah', 'Kelantan', 'Melaka', 'Negeri Sembilan', 'Pahang',
  'Penang', 'Perak', 'Perlis', 'Sabah', 'Sarawak', 'Selangor',
  'Terengganu', 'Kuala Lumpur', 'Labuan', 'Putrajaya'
];

// Sample clubs (would come from database)
const CLUBS = [
  'Pjms Aquatic Swimming Club',
  'Sea Dragon Swimming Club',
  'International School of KL',
  'GC Swimming Club',
  'Aqua Space Swimming And Diving',
  'Istio Swimming Club',
  'Other'
];

// Days, months, years for birthdate dropdowns
const DAYS = Array.from({ length: 31 }, (_, i) => i + 1);
const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
const YEARS = Array.from({ length: 30 }, (_, i) => new Date().getFullYear() - i);

// New Member Form Component
function NewMemberForm({ labelStyle, inputStyle, selectStyle }: {
  labelStyle: React.CSSProperties;
  inputStyle: React.CSSProperties;
  selectStyle: React.CSSProperties;
}) {
  const [fullName, setFullName] = useState('');
  const [birthDay, setBirthDay] = useState('');
  const [birthMonth, setBirthMonth] = useState('');
  const [birthYear, setBirthYear] = useState('');
  const [gender, setGender] = useState('');
  const [state, setState] = useState('');
  const [club, setClub] = useState('');

  const checkboxStyle: React.CSSProperties = { accentColor: '#cc0000', marginRight: '4px' };

  return (
    <div style={{ padding: '10px', backgroundColor: '#f9f9f9', borderRadius: '4px', border: '1px solid #eee' }}>
      {/* Name and Birthdate row */}
      <div style={{ marginBottom: '10px' }}>
        <span style={labelStyle}>Full Name</span>:{' '}
        <input
          type="text"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          placeholder="SURNAME, Given Names"
          style={{ ...inputStyle, width: '250px' }}
        />
        <span style={{ marginLeft: '30px' }}><span style={labelStyle}>Birthdate</span>:{' '}</span>
        <select value={birthDay} onChange={(e) => setBirthDay(e.target.value)} style={{ ...selectStyle, width: '60px' }}>
          <option value="">Day</option>
          {DAYS.map(d => <option key={d} value={d}>{d}</option>)}
        </select>
        <select value={birthMonth} onChange={(e) => setBirthMonth(e.target.value)} style={{ ...selectStyle, width: '100px' }}>
          <option value="">Month</option>
          {MONTHS.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
        </select>
        <select value={birthYear} onChange={(e) => setBirthYear(e.target.value)} style={{ ...selectStyle, width: '70px' }}>
          <option value="">Year</option>
          {YEARS.map(y => <option key={y} value={y}>{y}</option>)}
        </select>
        <span style={{ marginLeft: '30px' }}><span style={labelStyle}>Gender</span>:{' '}</span>
        <label style={{ marginLeft: '8px', cursor: 'pointer' }}>
          <input type="radio" name="gender" value="M" checked={gender === 'M'} onChange={(e) => setGender(e.target.value)} style={{ accentColor: '#cc0000', marginRight: '4px' }} />Male
        </label>
        <label style={{ marginLeft: '8px', cursor: 'pointer' }}>
          <input type="radio" name="gender" value="F" checked={gender === 'F'} onChange={(e) => setGender(e.target.value)} style={{ accentColor: '#cc0000', marginRight: '4px' }} />Female
        </label>
      </div>

      {/* State and Club row */}
      <div style={{ marginBottom: '10px' }}>
        <span style={labelStyle}>State</span>:{' '}
        <select value={state} onChange={(e) => setState(e.target.value)} style={{ ...selectStyle, width: '150px' }}>
          <option value="">Select State</option>
          {STATES.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <span style={{ marginLeft: '30px' }}><span style={labelStyle}>Club</span>:{' '}</span>
        <select value={club} onChange={(e) => setClub(e.target.value)} style={{ ...selectStyle, width: '250px' }}>
          <option value="">Select Club</option>
          {CLUBS.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      {/* Type/Discipline/Division row */}
      <div>
        <span style={labelStyle}>Type</span>:
        <label style={{ marginLeft: '8px', cursor: 'pointer' }}><input type="checkbox" style={checkboxStyle} />Athlete</label>
        <label style={{ marginLeft: '8px', cursor: 'pointer' }}><input type="checkbox" style={checkboxStyle} />Coach</label>
        <label style={{ marginLeft: '8px', cursor: 'pointer' }}><input type="checkbox" style={checkboxStyle} />Technical Official</label>
        <span style={{ marginLeft: '60px' }}><span style={labelStyle}>Discipline</span>:</span>
        <label style={{ marginLeft: '8px', cursor: 'pointer' }}><input type="checkbox" style={checkboxStyle} />Swimming</label>
        <label style={{ marginLeft: '8px', cursor: 'pointer' }}><input type="checkbox" style={checkboxStyle} />Artistic Swimming</label>
        <label style={{ marginLeft: '8px', cursor: 'pointer' }}><input type="checkbox" style={checkboxStyle} />Open Water</label>
        <label style={{ marginLeft: '8px', cursor: 'pointer' }}><input type="checkbox" style={checkboxStyle} />Water Polo</label>
        <label style={{ marginLeft: '8px', cursor: 'pointer' }}><input type="checkbox" style={checkboxStyle} />Diving</label>
        <span style={{ marginLeft: '60px' }}><span style={labelStyle}>Division</span>:</span>
        <label style={{ marginLeft: '8px', cursor: 'pointer' }}><input type="checkbox" style={checkboxStyle} />Open</label>
        <label style={{ marginLeft: '8px', cursor: 'pointer' }}><input type="checkbox" style={checkboxStyle} />Para</label>
        <label style={{ marginLeft: '8px', cursor: 'pointer' }}><input type="checkbox" style={checkboxStyle} />Masters</label>
      </div>
    </div>
  );
}

export default function RegistrationPage() {
  const router = useRouter();

  // Mode: null = not selected, 'find' = find account, 'create' = create new
  const [mode, setMode] = useState<'find' | 'create' | null>(null);

  // Account holder info (pre-populated for testing with Karen Chong - has 4 athletes)
  const [accountEmail, setAccountEmail] = useState('karenchong@rocketmail.com');
  const [accountName, setAccountName] = useState('Karen Chong');
  const [phoneCountryCode, setPhoneCountryCode] = useState('+60');
  const [phoneDigits, setPhoneDigits] = useState('177986998');

  // Found members after account lookup
  const [foundMembers, setFoundMembers] = useState<Member[]>([]);
  const [accountFound, setAccountFound] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  // Selected member for detail view
  const [selectedMember, setSelectedMember] = useState<Member | null>(null);

  // Account holder type: 'self' = registering myself, 'parent' = registering my children
  const [accountHolderType, setAccountHolderType] = useState<'self' | 'parent' | null>(null);

  // Handle account lookup - queries Supabase for athletes matching AcctEmail
  const handleEnter = async () => {
    // Auto-set mode to 'find' when Enter is pressed
    setMode('find');
    setLoading(true);
    setErrorMessage('');

    try {
      // Query Supabase for athletes with matching acct_email (lowercase in Supabase)
      const { data, error } = await supabase
        .from('athletes')
        .select(`
          id,
          fullname,
          birthdate,
          gender,
          club_code,
          club_name,
          state_code,
          nation,
          ic,
          passport_number,
          passport_expiry_date,
          phone,
          memb_email,
          acct_email
        `)
        .ilike('acct_email', accountEmail);

      if (error) {
        console.error('Supabase error:', error);
        setErrorMessage('Error searching database. Please try again.');
        setFoundMembers([]);
      } else if (data && data.length > 0) {
        // Map database records to Member interface
        const members: Member[] = data.map((row: any) => ({
          id: String(row.id),
          fullname: row.fullname || '',
          birthdate: row.birthdate ? row.birthdate.split('T')[0] : '',
          gender: row.gender || '',
          club_code: row.club_code || '',
          club_name: row.club_name || '',
          state_code: row.state_code || '',
          nation: row.nation || '',
          ic_number: row.ic || '',
          passport_number: row.passport_number || '',
          passport_expiry_date: row.passport_expiry_date || '',
          phone: row.phone || '',
          email: row.memb_email || '',
          // Default registration selections
          types: ['athlete'],
          disciplines: ['swimming'],
          divisions: ['open'],
        }));
        setFoundMembers(members);
      } else {
        setFoundMembers([]);
      }
      setAccountFound(true);
    } catch (err) {
      console.error('Error querying database:', err);
      setErrorMessage('Connection error. Please check your internet connection.');
      setFoundMembers([]);
      setAccountFound(true);
    } finally {
      setLoading(false);
    }
  };

  // Toggle member attributes
  const toggleMemberType = (memberId: string, typeId: string) => {
    setFoundMembers(prev => prev.map(m => {
      if (m.id === memberId) {
        const types = m.types.includes(typeId)
          ? m.types.filter(t => t !== typeId)
          : [...m.types, typeId];
        return { ...m, types };
      }
      return m;
    }));
  };

  const toggleMemberDiscipline = (memberId: string, discId: string) => {
    setFoundMembers(prev => prev.map(m => {
      if (m.id === memberId) {
        const disciplines = m.disciplines.includes(discId)
          ? m.disciplines.filter(d => d !== discId)
          : [...m.disciplines, discId];
        return { ...m, disciplines };
      }
      return m;
    }));
  };

  const toggleMemberDivision = (memberId: string, divId: string) => {
    setFoundMembers(prev => prev.map(m => {
      if (m.id === memberId) {
        const divisions = m.divisions.includes(divId)
          ? m.divisions.filter(d => d !== divId)
          : [...m.divisions, divId];
        return { ...m, divisions };
      }
      return m;
    }));
  };

  // Shared styles
  const labelStyle: React.CSSProperties = { fontWeight: 'bold' };
  const inputStyle: React.CSSProperties = {
    marginLeft: '4px',
    padding: '2px 6px',
    borderRadius: '3px',
    border: '1px solid #ccc',
    fontSize: 'inherit',
  };
  const selectStyle: React.CSSProperties = {
    marginLeft: '4px',
    padding: '2px 4px',
    borderRadius: '3px',
    border: '1px solid #ccc',
    fontSize: 'inherit',
  };
  const checkboxStyle: React.CSSProperties = { accentColor: '#cc0000', marginRight: '4px' };

  // Button styles
  const activeButtonStyle: React.CSSProperties = {
    background: '#cc0000',
    color: '#fff',
    border: 'none',
    padding: '10px 30px',
    fontSize: '1em',
    fontWeight: 600,
    borderRadius: '4px',
    cursor: 'pointer',
  };

  const inactiveButtonStyle: React.CSSProperties = {
    background: '#f5a0a0',
    color: '#fff',
    border: 'none',
    padding: '10px 30px',
    fontSize: '1em',
    fontWeight: 400,
    borderRadius: '4px',
    cursor: 'pointer',
  };

  const enterButtonStyle: React.CSSProperties = {
    background: '#cc0000',
    color: '#fff',
    border: 'none',
    padding: '2px 12px',
    fontSize: 'inherit',
    fontWeight: 600,
    borderRadius: '3px',
    cursor: 'pointer',
    marginLeft: '8px',
  };

  return (
    <>
      <Head>
        <title>Malaysia Aquatics Registration</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <div style={{
        fontFamily: 'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
        fontSize: '14px',
        minHeight: '100vh',
        backgroundColor: '#f5f5f5'
      }}>
        {/* Header */}
        <header style={{ backgroundColor: '#e8e8e8', paddingBottom: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
            <img src="/mas-logo.png" alt="MAS Logo" style={{ height: '60px' }} />
          </div>
          <div style={{
            position: 'relative',
            backgroundColor: '#cc0000',
            padding: '30px 20px 50px',
            textAlign: 'center',
          }}>
            <h1 style={{ color: 'white', fontSize: '1.4rem', fontWeight: 600, margin: 0 }}>
              Malaysia Aquatics Registration Form
            </h1>
            <svg style={{ position: 'absolute', bottom: 0, left: 0, width: '100%', height: '30px' }}
              viewBox="0 0 1200 30" preserveAspectRatio="none">
              <path d="M0,30 C300,0 600,30 900,10 C1050,0 1150,20 1200,30 L1200,30 L0,30 Z" fill="#f5f5f5" />
            </svg>
          </div>
        </header>

        {/* Main content */}
        <main style={{ maxWidth: '1400px', margin: '0 auto', padding: '20px' }}>
          <form onSubmit={(e) => e.preventDefault()}>
            <div style={{
              fontSize: '0.9em',
              border: '1px solid #ddd',
              borderRadius: '8px',
              padding: '15px',
              backgroundColor: 'white',
            }}>

              {/* Mode Selection Buttons - At Top, Centered */}
              <div style={{ marginBottom: '20px', display: 'flex', justifyContent: 'center', gap: '15px' }}>
                <button
                  type="button"
                  onClick={() => { setMode('find'); setAccountFound(false); setFoundMembers([]); }}
                  style={mode === 'find' ? activeButtonStyle : (mode === 'create' ? inactiveButtonStyle : activeButtonStyle)}
                >
                  Find My Account
                </button>
                <button
                  type="button"
                  onClick={() => { setMode('create'); setAccountFound(false); setFoundMembers([]); }}
                  style={mode === 'create' ? activeButtonStyle : (mode === 'find' ? inactiveButtonStyle : activeButtonStyle)}
                >
                  Create New Account
                </button>
              </div>

              {/* Account Information Section - Always visible */}
              <div style={{ marginBottom: '15px' }}>
                <div style={{ fontWeight: 'bold', color: '#cc0000', marginBottom: '8px' }}>
                  Account Information
                </div>
                <div style={{ margin: '8px 0', display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '15px' }}>
                  <span>
                    <span style={labelStyle}>Email</span>:{' '}
                    <input
                      type="email"
                      value={accountEmail}
                      onChange={(e) => setAccountEmail(e.target.value)}
                      placeholder="your.email@example.com"
                      style={{ ...inputStyle, width: '200px' }}
                    />
                  </span>
                  <span>
                    <span style={labelStyle}>Phone</span>:{' '}
                    <select
                      value={phoneCountryCode}
                      onChange={(e) => setPhoneCountryCode(e.target.value)}
                      style={{ ...selectStyle, width: '70px' }}
                    >
                      {COUNTRY_CODES.map((cc) => (
                        <option key={cc.code} value={cc.code}>{cc.code}</option>
                      ))}
                    </select>
                    <input
                      type="tel"
                      value={phoneDigits}
                      onChange={(e) => setPhoneDigits(e.target.value.replace(/\D/g, ''))}
                      placeholder="123456789"
                      style={{ ...inputStyle, width: '100px' }}
                    />
                  </span>
                  <span>
                    <span style={labelStyle}>Full Name</span>:{' '}
                    <input
                      type="text"
                      value={accountName}
                      onChange={(e) => setAccountName(e.target.value)}
                      placeholder="Account holder full name"
                      style={{ ...inputStyle, width: '250px' }}
                    />
                  </span>
                </div>
              </div>

              {/* Account Holder Type Question */}
              <div style={{ marginBottom: '15px', display: 'flex', alignItems: 'center' }}>
                <span style={labelStyle}>I am registering</span>:{' '}
                <label style={{ marginLeft: '15px', cursor: 'pointer' }}>
                  <input
                    type="radio"
                    name="accountHolderType"
                    checked={accountHolderType === 'self'}
                    onChange={() => setAccountHolderType('self')}
                    style={{ accentColor: '#cc0000', marginRight: '4px' }}
                  />
                  Myself (as athlete, coach, or official)
                </label>
                <label style={{ marginLeft: '25px', cursor: 'pointer' }}>
                  <input
                    type="radio"
                    name="accountHolderType"
                    checked={accountHolderType === 'parent'}
                    onChange={() => setAccountHolderType('parent')}
                    style={{ accentColor: '#cc0000', marginRight: '4px' }}
                  />
                  My child(ren) as their parent/guardian
                </label>
                <button
                  type="button"
                  onClick={handleEnter}
                  disabled={!accountHolderType || loading}
                  style={{
                    marginLeft: '25px',
                    padding: '4px 16px',
                    borderRadius: '3px',
                    border: 'none',
                    fontSize: 'inherit',
                    cursor: (accountHolderType && !loading) ? 'pointer' : 'not-allowed',
                    backgroundColor: (accountHolderType && !loading) ? '#cc0000' : '#f5a0a0',
                    color: '#fff',
                    fontWeight: (accountHolderType && !loading) ? 600 : 400,
                  }}
                >
                  {loading ? 'Searching...' : 'Enter'}
                </button>
              </div>

              {/* Error Message Display */}
              {errorMessage && (
                <div style={{ marginTop: '15px', padding: '10px', backgroundColor: '#f8d7da', borderRadius: '4px', color: '#721c24' }}>
                  {errorMessage}
                </div>
              )}

              {/* Found Members Section - Show after account lookup */}
              {mode === 'find' && accountFound && foundMembers.length > 0 && !selectedMember && (
                <div style={{ marginTop: '20px' }}>
                  <div style={{ fontWeight: 'bold', color: '#cc0000', marginBottom: '12px' }}>
                    Members Found ({foundMembers.length}) - Select a member to review/update
                  </div>

                  {/* Member list with radio buttons - like athlete panel */}
                  <div style={{
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    maxHeight: '300px',
                    overflowY: 'auto'
                  }}>
                    {foundMembers.map((member) => (
                      <div
                        key={member.id}
                        style={{
                          padding: '0.5rem 0.75rem',
                          borderBottom: '1px solid #eee',
                          backgroundColor: '#ffffff',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.75rem'
                        }}
                        onClick={() => setSelectedMember(member)}
                      >
                        <input
                          type="radio"
                          name="member-selection"
                          checked={false}
                          onChange={() => setSelectedMember(member)}
                          style={{ cursor: 'pointer', flexShrink: 0, accentColor: '#cc0000' }}
                        />
                        <div style={{ fontWeight: '600', fontSize: '0.9rem', color: '#cc0000', width: '220px', flexShrink: 0 }}>
                          {member.fullname}
                        </div>
                        <div style={{ fontFamily: 'monospace', color: '#666', fontSize: '0.75rem', width: '70px', flexShrink: 0 }}>
                          ID: {member.id}
                        </div>
                        <div style={{ color: '#333', fontSize: '0.8rem', width: '100px', flexShrink: 0 }}>
                          {member.birthdate}
                        </div>
                        <div style={{ color: '#333', fontSize: '0.8rem', width: '30px', flexShrink: 0 }}>
                          {member.gender}
                        </div>
                        <div style={{ color: '#666', fontSize: '0.75rem', flex: 1 }}>
                          {member.club_name || '(no club)'}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Selected Member Detail View - Full athlete record edit */}
              {mode === 'find' && accountFound && selectedMember && (
                <div style={{ marginTop: '20px' }}>
                  {/* Header with close button */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px', paddingBottom: '10px', borderBottom: '2px solid #cc0000' }}>
                    <h3 style={{ margin: 0, color: '#cc0000', fontSize: '1.1em' }}>
                      Review & Update: <span style={{ fontWeight: 'bold' }}>{selectedMember.fullname}</span>
                    </h3>
                    <button
                      type="button"
                      onClick={() => setSelectedMember(null)}
                      style={{
                        padding: '4px 12px',
                        backgroundColor: '#666',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '0.85em',
                        fontWeight: '600'
                      }}
                    >
                      Back to List
                    </button>
                  </div>

                  {/* Athlete record fields in grid layout */}
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: '12px',
                    fontSize: '0.9em'
                  }}>
                    {/* Row 1: Full Name and ID */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <label style={{ fontWeight: '500', minWidth: '100px', color: '#333' }}>Full Name:</label>
                      <input type="text" defaultValue={selectedMember.fullname} style={{ ...inputStyle, flex: 1, color: '#666' }} />
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <label style={{ fontWeight: '500', minWidth: '100px', color: '#333' }}>Member ID:</label>
                      <input type="text" value={selectedMember.id} disabled style={{ ...inputStyle, flex: 1, backgroundColor: '#f0f0f0', color: '#999' }} />
                    </div>

                    {/* Row 2: Birthdate and Gender */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <label style={{ fontWeight: '500', minWidth: '100px', color: '#333' }}>Birthdate:</label>
                      <select defaultValue={selectedMember.birthdate?.split('-')[2] || ''} style={{ ...selectStyle, width: '60px', color: '#666' }}>
                        <option value="">DD</option>
                        {DAYS.map(d => <option key={d} value={d}>{d}</option>)}
                      </select>
                      <select defaultValue={selectedMember.birthdate?.split('-')[1] || ''} style={{ ...selectStyle, width: '90px', color: '#666' }}>
                        <option value="">Month</option>
                        {MONTHS.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
                      </select>
                      <select defaultValue={selectedMember.birthdate?.split('-')[0] || ''} style={{ ...selectStyle, width: '70px', color: '#666' }}>
                        <option value="">YYYY</option>
                        {YEARS.map(y => <option key={y} value={y}>{y}</option>)}
                      </select>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <label style={{ fontWeight: '500', minWidth: '100px', color: '#333' }}>Gender:</label>
                      <label style={{ cursor: 'pointer', color: '#666' }}>
                        <input type="radio" name="editGender" defaultChecked={selectedMember.gender === 'M'} style={{ accentColor: '#cc0000', marginRight: '4px' }} />Male
                      </label>
                      <label style={{ marginLeft: '15px', cursor: 'pointer', color: '#666' }}>
                        <input type="radio" name="editGender" defaultChecked={selectedMember.gender === 'F'} style={{ accentColor: '#cc0000', marginRight: '4px' }} />Female
                      </label>
                    </div>

                    {/* Row 3: Club and State */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <label style={{ fontWeight: '500', minWidth: '100px', color: '#333' }}>Club:</label>
                      <input
                        type="text"
                        defaultValue={selectedMember.club_name || ''}
                        placeholder="Club name"
                        style={{ ...inputStyle, flex: 1, color: selectedMember.club_name ? '#333' : '#666' }}
                      />
                      {selectedMember.club_code && (
                        <span style={{ color: '#999', fontSize: '0.8em' }}>({selectedMember.club_code})</span>
                      )}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <label style={{ fontWeight: '500', minWidth: '100px', color: '#333' }}>State:</label>
                      <select
                        defaultValue={selectedMember.state_code || ''}
                        style={{ ...selectStyle, flex: 1, color: selectedMember.state_code ? '#333' : '#666' }}
                      >
                        <option value="">Select State</option>
                        <option value="JHR">Johor</option>
                        <option value="KDH">Kedah</option>
                        <option value="KTN">Kelantan</option>
                        <option value="MLK">Melaka</option>
                        <option value="NSN">Negeri Sembilan</option>
                        <option value="PHG">Pahang</option>
                        <option value="PNG">Penang</option>
                        <option value="PRK">Perak</option>
                        <option value="PLS">Perlis</option>
                        <option value="SBH">Sabah</option>
                        <option value="SWK">Sarawak</option>
                        <option value="SEL">Selangor</option>
                        <option value="TRG">Terengganu</option>
                        <option value="KUL">Kuala Lumpur</option>
                        <option value="LBN">Labuan</option>
                        <option value="PJY">Putrajaya</option>
                      </select>
                    </div>

                    {/* Row 4: IC Number - show as single field with parsed value */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <label style={{ fontWeight: '500', minWidth: '100px', color: '#333' }}>IC Number:</label>
                      <input
                        type="text"
                        defaultValue={selectedMember.ic_number || ''}
                        placeholder="YYMMDD-PB-####"
                        style={{ ...inputStyle, flex: 1, color: selectedMember.ic_number ? '#333' : '#666' }}
                      />
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <label style={{ fontWeight: '500', minWidth: '100px', color: '#333' }}>Nation:</label>
                      <input
                        type="text"
                        defaultValue={selectedMember.nation || 'MAS'}
                        style={{ ...inputStyle, width: '60px', color: '#333' }}
                      />
                    </div>

                    {/* Row 5: Passport */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <label style={{ fontWeight: '500', minWidth: '100px', color: '#333' }}>Passport #:</label>
                      <input
                        type="text"
                        defaultValue={selectedMember.passport_number || ''}
                        placeholder="Passport number"
                        style={{ ...inputStyle, flex: 1, color: selectedMember.passport_number ? '#333' : '#666' }}
                      />
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <label style={{ fontWeight: '500', minWidth: '100px', color: '#333' }}>Passport Expiry:</label>
                      <input
                        type="date"
                        defaultValue={selectedMember.passport_expiry_date?.split('T')[0] || ''}
                        style={{ ...inputStyle, flex: 1, color: selectedMember.passport_expiry_date ? '#333' : '#666' }}
                      />
                    </div>

                    {/* Row 6: Athlete's Phone and Email (not account holder's) */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <label style={{ fontWeight: '500', minWidth: '100px', color: '#333' }}>Phone:</label>
                      <input
                        type="tel"
                        defaultValue={selectedMember.phone || ''}
                        placeholder="Phone number"
                        style={{ ...inputStyle, flex: 1, color: selectedMember.phone ? '#333' : '#666' }}
                      />
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <label style={{ fontWeight: '500', minWidth: '100px', color: '#333' }}>Email:</label>
                      <input
                        type="email"
                        defaultValue={selectedMember.email || ''}
                        placeholder="Email address"
                        style={{ ...inputStyle, flex: 1, color: selectedMember.email ? '#333' : '#666' }}
                      />
                    </div>

                    {/* Row 7: Emergency Contact */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <label style={{ fontWeight: '500', minWidth: '100px', color: '#333' }}>Emergency Contact:</label>
                      <input type="text" placeholder="Contact name" style={{ ...inputStyle, flex: 1, color: '#666' }} />
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <label style={{ fontWeight: '500', minWidth: '100px', color: '#333' }}>Emergency Phone:</label>
                      <input type="tel" placeholder="Emergency phone" style={{ ...inputStyle, flex: 1, color: '#666' }} />
                    </div>
                  </div>

                  {/* Type/Discipline/Division Section */}
                  <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#f9f9f9', borderRadius: '4px' }}>
                    <div style={{ marginBottom: '10px' }}>
                      <span style={labelStyle}>Registration Type</span>:
                      <label style={{ marginLeft: '15px', cursor: 'pointer' }}>
                        <input type="checkbox" checked={selectedMember.types.includes('athlete')} onChange={() => toggleMemberType(selectedMember.id, 'athlete')} style={checkboxStyle} />Athlete
                      </label>
                      <label style={{ marginLeft: '15px', cursor: 'pointer' }}>
                        <input type="checkbox" checked={selectedMember.types.includes('coach')} onChange={() => toggleMemberType(selectedMember.id, 'coach')} style={checkboxStyle} />Coach
                      </label>
                      <label style={{ marginLeft: '15px', cursor: 'pointer' }}>
                        <input type="checkbox" checked={selectedMember.types.includes('technical_official')} onChange={() => toggleMemberType(selectedMember.id, 'technical_official')} style={checkboxStyle} />Technical Official
                      </label>
                    </div>
                    <div style={{ marginBottom: '10px' }}>
                      <span style={labelStyle}>Discipline</span>:
                      <label style={{ marginLeft: '15px', cursor: 'pointer' }}>
                        <input type="checkbox" checked={selectedMember.disciplines.includes('swimming')} onChange={() => toggleMemberDiscipline(selectedMember.id, 'swimming')} style={checkboxStyle} />Swimming
                      </label>
                      <label style={{ marginLeft: '15px', cursor: 'pointer' }}>
                        <input type="checkbox" checked={selectedMember.disciplines.includes('artistic_swimming')} onChange={() => toggleMemberDiscipline(selectedMember.id, 'artistic_swimming')} style={checkboxStyle} />Artistic Swimming
                      </label>
                      <label style={{ marginLeft: '15px', cursor: 'pointer' }}>
                        <input type="checkbox" checked={selectedMember.disciplines.includes('open_water')} onChange={() => toggleMemberDiscipline(selectedMember.id, 'open_water')} style={checkboxStyle} />Open Water
                      </label>
                      <label style={{ marginLeft: '15px', cursor: 'pointer' }}>
                        <input type="checkbox" checked={selectedMember.disciplines.includes('water_polo')} onChange={() => toggleMemberDiscipline(selectedMember.id, 'water_polo')} style={checkboxStyle} />Water Polo
                      </label>
                      <label style={{ marginLeft: '15px', cursor: 'pointer' }}>
                        <input type="checkbox" checked={selectedMember.disciplines.includes('diving')} onChange={() => toggleMemberDiscipline(selectedMember.id, 'diving')} style={checkboxStyle} />Diving
                      </label>
                    </div>
                    <div>
                      <span style={labelStyle}>Division</span>:
                      <label style={{ marginLeft: '15px', cursor: 'pointer' }}>
                        <input type="checkbox" checked={selectedMember.divisions.includes('open')} onChange={() => toggleMemberDivision(selectedMember.id, 'open')} style={checkboxStyle} />Open
                      </label>
                      <label style={{ marginLeft: '15px', cursor: 'pointer' }}>
                        <input type="checkbox" checked={selectedMember.divisions.includes('para')} onChange={() => toggleMemberDivision(selectedMember.id, 'para')} style={checkboxStyle} />Para
                      </label>
                      <label style={{ marginLeft: '15px', cursor: 'pointer' }}>
                        <input type="checkbox" checked={selectedMember.divisions.includes('masters')} onChange={() => toggleMemberDivision(selectedMember.id, 'masters')} style={checkboxStyle} />Masters
                      </label>
                    </div>
                  </div>

                  {/* Confirm button */}
                  <div style={{ marginTop: '20px', display: 'flex', gap: '10px' }}>
                    <button
                      type="button"
                      onClick={() => {
                        // Mark member as confirmed and go back to list
                        setSelectedMember(null);
                      }}
                      style={activeButtonStyle}
                    >
                      Confirm & Return to List
                    </button>
                  </div>
                </div>
              )}

              {/* Code of Conduct and Submit - only show when no member selected */}
              {mode === 'find' && accountFound && foundMembers.length > 0 && !selectedMember && (
                <>
                  {/* Code of Conduct Section */}
                  <div style={{ marginTop: '20px' }}>
                    <div style={{ fontWeight: 'bold', color: '#cc0000', marginBottom: '12px' }}>
                      Code of Conduct Agreements
                    </div>

                    {/* Parent CoC - show if registering as parent */}
                    {accountHolderType === 'parent' && (
                      <div style={{ marginBottom: '10px', padding: '10px', backgroundColor: '#fff3cd', borderRadius: '4px' }}>
                        <label style={{ cursor: 'pointer' }}>
                          <input type="checkbox" style={{ accentColor: '#cc0000', marginRight: '8px' }} />
                          <span style={labelStyle}>Parent/Guardian Code of Conduct</span>
                          <span style={{ color: '#666', marginLeft: '10px' }}>(Required for all parents/guardians)</span>
                        </label>
                      </div>
                    )}

                    {/* Athlete CoC - show if any member has athlete type */}
                    {foundMembers.some(m => m.types.includes('athlete')) && (
                      <div style={{ marginBottom: '10px', padding: '10px', backgroundColor: '#e7f3ff', borderRadius: '4px' }}>
                        <label style={{ cursor: 'pointer' }}>
                          <input type="checkbox" style={{ accentColor: '#cc0000', marginRight: '8px' }} />
                          <span style={labelStyle}>Athlete Code of Conduct</span>
                          <span style={{ color: '#666', marginLeft: '10px' }}>(Required for athletes)</span>
                        </label>
                      </div>
                    )}

                    {/* Coach CoC - show if any member has coach type */}
                    {foundMembers.some(m => m.types.includes('coach')) && (
                      <div style={{ marginBottom: '10px', padding: '10px', backgroundColor: '#d4edda', borderRadius: '4px' }}>
                        <label style={{ cursor: 'pointer' }}>
                          <input type="checkbox" style={{ accentColor: '#cc0000', marginRight: '8px' }} />
                          <span style={labelStyle}>Coach Code of Conduct</span>
                          <span style={{ color: '#666', marginLeft: '10px' }}>(Required for coaches)</span>
                        </label>
                      </div>
                    )}

                    {/* Technical Official CoC - show if any member has technical_official type */}
                    {foundMembers.some(m => m.types.includes('technical_official')) && (
                      <div style={{ marginBottom: '10px', padding: '10px', backgroundColor: '#f8d7da', borderRadius: '4px' }}>
                        <label style={{ cursor: 'pointer' }}>
                          <input type="checkbox" style={{ accentColor: '#cc0000', marginRight: '8px' }} />
                          <span style={labelStyle}>Technical Official Code of Conduct</span>
                          <span style={{ color: '#666', marginLeft: '10px' }}>(Required for technical officials)</span>
                        </label>
                      </div>
                    )}
                  </div>

                  {/* Submit Registration Button */}
                  <div style={{ marginTop: '20px', textAlign: 'center' }}>
                    <button
                      type="button"
                      onClick={() => {
                        // Store registration data in sessionStorage for payment page
                        const registrationData = {
                          accountEmail,
                          accountName,
                          phone: `${phoneCountryCode}${phoneDigits}`,
                          accountHolderType,
                          members: foundMembers,
                          submittedAt: new Date().toISOString(),
                        };
                        sessionStorage.setItem('pendingRegistration', JSON.stringify(registrationData));
                        router.push('/payment');
                      }}
                      style={activeButtonStyle}
                    >
                      Submit Registration
                    </button>
                  </div>
                </>
              )}

              {/* No members found - Show new member form */}
              {mode === 'find' && accountFound && foundMembers.length === 0 && (
                <div style={{ marginTop: '20px' }}>
                  <div style={{ padding: '15px', backgroundColor: '#fff3cd', borderRadius: '4px', color: '#856404', marginBottom: '15px' }}>
                    No members found for this account. Add your first member below:
                  </div>
                  <NewMemberForm labelStyle={labelStyle} inputStyle={inputStyle} selectStyle={selectStyle} />
                </div>
              )}

              {/* Create New Account Flow - Show new member form */}
              {mode === 'create' && (
                <div style={{ marginTop: '20px' }}>
                  <div style={{ fontWeight: 'bold', color: '#cc0000', marginBottom: '12px' }}>
                    Add Member
                  </div>
                  <NewMemberForm labelStyle={labelStyle} inputStyle={inputStyle} selectStyle={selectStyle} />
                </div>
              )}

            </div>
          </form>
        </main>

        {/* Footer */}
        <footer style={{ textAlign: 'center', padding: '30px 20px', color: '#888', fontSize: '0.85em' }}>
          <p style={{ margin: 0 }}>Malaysia Aquatics (Persatuan Akuatik Malaysia)</p>
          <p style={{ margin: '4px 0 0 0' }}>
            Need help? Contact{' '}
            <a href="mailto:registration@malaysiaaquatics.org" style={{ color: '#cc0000' }}>
              registration@malaysiaaquatics.org
            </a>
          </p>
        </footer>
      </div>
    </>
  );
}
