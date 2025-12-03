import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';

interface Member {
  id: string;
  fullname: string;
  birthdate: string;
  gender: string;
  types: string[];
  disciplines: string[];
  divisions: string[];
}

interface PaymentRecord {
  payment_date: string;
  payment_amount: number;
  payment_receipt_id: string;
  payment_status: string;
  payment_method: string;
  rm_transaction_ref: string;
}

interface CompletedRegistration {
  accountEmail: string;
  accountName: string;
  phone: string;
  accountHolderType: 'self' | 'parent' | null;
  members: Member[];
  submittedAt: string;
  payment: PaymentRecord;
  confirmedAt: string;
}

export default function ConfirmationPage() {
  const router = useRouter();
  const [registration, setRegistration] = useState<CompletedRegistration | null>(null);
  const [saving, setSaving] = useState(true);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    // Load completed registration from sessionStorage
    const stored = sessionStorage.getItem('completedRegistration');
    if (stored) {
      const data = JSON.parse(stored) as CompletedRegistration;
      setRegistration(data);

      // TODO: Save to Supabase database
      // This will save:
      // 1. Updated athlete records (any changes made during registration)
      // 2. Registration status for 2026 (registration_year, payment info)
      // 3. Payment record linked to each athlete
      saveToDatabase(data);
    } else {
      // No completed registration, redirect to home
      router.push('/');
    }
  }, [router]);

  // Save registration and payment data to database
  const saveToDatabase = async (data: CompletedRegistration) => {
    setSaving(true);

    // TODO: Replace with actual Supabase API call
    // For each member:
    // 1. Update athlete record with any changes
    // 2. Insert registration_2026 record with payment info:
    //    - athlete_id
    //    - registration_year: 2026
    //    - payment_date: data.payment.payment_date
    //    - payment_amount: data.payment.payment_amount
    //    - payment_receipt_id: data.payment.payment_receipt_id
    //    - payment_status: data.payment.payment_status
    //    - payment_method: data.payment.payment_method
    //    - rm_transaction_ref: data.payment.rm_transaction_ref
    //    - submitted_at: data.submittedAt
    //    - confirmed_at: data.confirmedAt

    console.log('Saving to database:', data);

    // Simulate API call
    setTimeout(() => {
      setSaving(false);
      setSaved(true);

      // Clear session storage after successful save
      sessionStorage.removeItem('pendingRegistration');
      sessionStorage.removeItem('completedRegistration');
    }, 1500);
  };

  const formatDate = (isoString: string) => {
    return new Date(isoString).toLocaleString('en-MY', {
      dateStyle: 'full',
      timeStyle: 'short',
    });
  };

  if (!registration) {
    return <div style={{ padding: '40px', textAlign: 'center' }}>Loading...</div>;
  }

  return (
    <>
      <Head>
        <title>Registration Complete - Malaysia Aquatics</title>
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
            backgroundColor: '#28a745',
            padding: '30px 20px 50px',
            textAlign: 'center',
          }}>
            <h1 style={{ color: 'white', fontSize: '1.4rem', fontWeight: 600, margin: 0 }}>
              Registration Complete!
            </h1>
            <svg style={{ position: 'absolute', bottom: 0, left: 0, width: '100%', height: '30px' }}
              viewBox="0 0 1200 30" preserveAspectRatio="none">
              <path d="M0,30 C300,0 600,30 900,10 C1050,0 1150,20 1200,30 L1200,30 L0,30 Z" fill="#f5f5f5" />
            </svg>
          </div>
        </header>

        {/* Main content */}
        <main style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
          <div style={{
            border: '1px solid #ddd',
            borderRadius: '8px',
            padding: '25px',
            backgroundColor: 'white',
          }}>
            {/* Success Message */}
            <div style={{
              textAlign: 'center',
              padding: '20px',
              marginBottom: '25px',
              backgroundColor: '#d4edda',
              borderRadius: '8px',
              border: '1px solid #c3e6cb',
            }}>
              <div style={{ fontSize: '3em', marginBottom: '10px' }}>OK</div>
              <h2 style={{ color: '#155724', margin: '0 0 10px 0' }}>Payment Successful!</h2>
              <p style={{ color: '#155724', margin: 0 }}>
                Your registration has been confirmed and saved to our records.
              </p>
            </div>

            {/* Payment Receipt */}
            <div style={{ marginBottom: '25px', paddingBottom: '15px', borderBottom: '1px solid #eee' }}>
              <h3 style={{ color: '#cc0000', fontSize: '1.1em', marginBottom: '15px' }}>Payment Receipt</h3>

              <table style={{ width: '100%' }}>
                <tbody>
                  <tr>
                    <td style={{ padding: '8px 0', color: '#666' }}>Receipt ID:</td>
                    <td style={{ padding: '8px 0', fontWeight: 'bold' }}>{registration.payment.payment_receipt_id}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px 0', color: '#666' }}>Transaction Reference:</td>
                    <td style={{ padding: '8px 0' }}>{registration.payment.rm_transaction_ref}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px 0', color: '#666' }}>Payment Date:</td>
                    <td style={{ padding: '8px 0' }}>{formatDate(registration.payment.payment_date)}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px 0', color: '#666' }}>Payment Method:</td>
                    <td style={{ padding: '8px 0', textTransform: 'uppercase' }}>{registration.payment.payment_method}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px 0', color: '#666' }}>Status:</td>
                    <td style={{ padding: '8px 0' }}>
                      <span style={{
                        backgroundColor: '#28a745',
                        color: 'white',
                        padding: '2px 8px',
                        borderRadius: '3px',
                        fontSize: '0.9em',
                        textTransform: 'uppercase',
                      }}>
                        {registration.payment.payment_status}
                      </span>
                    </td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px 0', color: '#666', fontWeight: 'bold' }}>Amount Paid:</td>
                    <td style={{ padding: '8px 0', fontWeight: 'bold', color: '#cc0000', fontSize: '1.2em' }}>
                      RM {registration.payment.payment_amount}.00
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Registered Members */}
            <div style={{ marginBottom: '25px', paddingBottom: '15px', borderBottom: '1px solid #eee' }}>
              <h3 style={{ color: '#cc0000', fontSize: '1.1em', marginBottom: '15px' }}>Registered Members</h3>

              {registration.members.map(member => (
                <div key={member.id} style={{
                  padding: '10px',
                  marginBottom: '10px',
                  backgroundColor: '#f9f9f9',
                  borderRadius: '4px',
                }}>
                  <div style={{ fontWeight: 'bold' }}>{member.fullname}</div>
                  <div style={{ color: '#666', fontSize: '0.9em' }}>
                    ID: {member.id} | {member.types.join(', ')} | {member.disciplines.join(', ')}
                  </div>
                </div>
              ))}
            </div>

            {/* Database Save Status */}
            <div style={{
              padding: '15px',
              backgroundColor: saving ? '#fff3cd' : '#d4edda',
              borderRadius: '4px',
              textAlign: 'center',
              marginBottom: '20px',
            }}>
              {saving ? (
                <span style={{ color: '#856404' }}>Saving registration to database...</span>
              ) : (
                <span style={{ color: '#155724' }}>Registration saved to database successfully!</span>
              )}
            </div>

            {/* Confirmation Email Notice */}
            <div style={{ textAlign: 'center', color: '#666', marginBottom: '20px' }}>
              <p>A confirmation email has been sent to:</p>
              <p style={{ fontWeight: 'bold', color: '#333' }}>{registration.accountEmail}</p>
            </div>

            {/* Return Home Button */}
            <div style={{ textAlign: 'center' }}>
              <button
                type="button"
                onClick={() => router.push('/')}
                style={{
                  background: '#cc0000',
                  color: '#fff',
                  border: 'none',
                  padding: '12px 30px',
                  fontSize: '1em',
                  fontWeight: 600,
                  borderRadius: '4px',
                  cursor: 'pointer',
                }}
              >
                Return to Registration Home
              </button>
            </div>
          </div>
        </main>

        {/* Footer */}
        <footer style={{ textAlign: 'center', padding: '30px 20px', color: '#888', fontSize: '0.85em' }}>
          <p style={{ margin: 0 }}>Malaysia Aquatics (Persatuan Akuatik Malaysia)</p>
          <p style={{ margin: '4px 0 0 0' }}>
            Questions? Contact{' '}
            <a href="mailto:registration@malaysiaaquatics.org" style={{ color: '#cc0000' }}>
              registration@malaysiaaquatics.org
            </a>
          </p>
        </footer>
      </div>
    </>
  );
}
