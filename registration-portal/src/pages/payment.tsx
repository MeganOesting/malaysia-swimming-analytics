import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';

// Registration fee structure
const FEES = {
  athlete: 50,      // RM50 per athlete
  coach: 100,       // RM100 per coach
  technical_official: 50,  // RM50 per TO
};

interface Member {
  id: string;
  fullname: string;
  birthdate: string;
  gender: string;
  types: string[];
  disciplines: string[];
  divisions: string[];
}

interface RegistrationData {
  accountEmail: string;
  accountName: string;
  phone: string;
  accountHolderType: 'self' | 'parent' | null;
  members: Member[];
  submittedAt: string;
}

export default function PaymentPage() {
  const router = useRouter();
  const [registrationData, setRegistrationData] = useState<RegistrationData | null>(null);
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    // Load registration data from sessionStorage
    const stored = sessionStorage.getItem('pendingRegistration');
    if (stored) {
      setRegistrationData(JSON.parse(stored));
    } else {
      // No registration data, redirect back
      router.push('/');
    }
  }, [router]);

  // Calculate total fee
  const calculateTotal = () => {
    if (!registrationData) return 0;
    let total = 0;
    registrationData.members.forEach(member => {
      member.types.forEach(type => {
        if (type === 'athlete') total += FEES.athlete;
        if (type === 'coach') total += FEES.coach;
        if (type === 'technical_official') total += FEES.technical_official;
      });
    });
    return total;
  };

  // Handle payment - This will eventually call RevenueMonster API
  const handlePayment = async () => {
    setProcessing(true);

    // TODO: Replace with actual RevenueMonster integration
    // For now, simulate payment processing
    setTimeout(() => {
      // Create payment record (will be returned from RevenueMonster)
      const paymentRecord = {
        payment_date: new Date().toISOString(),
        payment_amount: calculateTotal(),
        payment_receipt_id: `RM-${Date.now()}`, // Mock receipt ID
        payment_status: 'completed',
        payment_method: 'fpx', // Mock - RevenueMonster will tell us actual method
        rm_transaction_ref: `TXN-${Date.now()}`, // Mock transaction ref
      };

      // Store payment info with registration data
      const completeRegistration = {
        ...registrationData,
        payment: paymentRecord,
        confirmedAt: new Date().toISOString(),
      };

      sessionStorage.setItem('completedRegistration', JSON.stringify(completeRegistration));

      // Navigate to confirmation page
      router.push('/confirmation');
    }, 2000);
  };

  // Shared styles
  const activeButtonStyle: React.CSSProperties = {
    background: '#cc0000',
    color: '#fff',
    border: 'none',
    padding: '15px 40px',
    fontSize: '1.1em',
    fontWeight: 600,
    borderRadius: '4px',
    cursor: processing ? 'not-allowed' : 'pointer',
    opacity: processing ? 0.7 : 1,
  };

  if (!registrationData) {
    return <div style={{ padding: '40px', textAlign: 'center' }}>Loading...</div>;
  }

  const total = calculateTotal();

  return (
    <>
      <Head>
        <title>Payment - Malaysia Aquatics Registration</title>
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
              Registration Payment
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
            {/* Account Summary */}
            <div style={{ marginBottom: '25px', paddingBottom: '15px', borderBottom: '1px solid #eee' }}>
              <h2 style={{ color: '#cc0000', fontSize: '1.1em', marginBottom: '10px' }}>Account Holder</h2>
              <p style={{ margin: '5px 0' }}><strong>Name:</strong> {registrationData.accountName}</p>
              <p style={{ margin: '5px 0' }}><strong>Email:</strong> {registrationData.accountEmail}</p>
              <p style={{ margin: '5px 0' }}><strong>Phone:</strong> {registrationData.phone}</p>
            </div>

            {/* Members Being Registered */}
            <div style={{ marginBottom: '25px', paddingBottom: '15px', borderBottom: '1px solid #eee' }}>
              <h2 style={{ color: '#cc0000', fontSize: '1.1em', marginBottom: '15px' }}>Registration Summary</h2>

              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f5f5f5' }}>
                    <th style={{ textAlign: 'left', padding: '10px', borderBottom: '2px solid #ddd' }}>Member</th>
                    <th style={{ textAlign: 'left', padding: '10px', borderBottom: '2px solid #ddd' }}>Registration Type</th>
                    <th style={{ textAlign: 'right', padding: '10px', borderBottom: '2px solid #ddd' }}>Fee (RM)</th>
                  </tr>
                </thead>
                <tbody>
                  {registrationData.members.map(member => (
                    member.types.map((type, idx) => (
                      <tr key={`${member.id}-${type}`}>
                        <td style={{ padding: '10px', borderBottom: '1px solid #eee' }}>
                          {idx === 0 ? member.fullname : ''}
                        </td>
                        <td style={{ padding: '10px', borderBottom: '1px solid #eee' }}>
                          {type === 'athlete' ? 'Athlete' : type === 'coach' ? 'Coach' : 'Technical Official'}
                        </td>
                        <td style={{ padding: '10px', borderBottom: '1px solid #eee', textAlign: 'right' }}>
                          {type === 'athlete' ? FEES.athlete : type === 'coach' ? FEES.coach : FEES.technical_official}.00
                        </td>
                      </tr>
                    ))
                  ))}
                </tbody>
                <tfoot>
                  <tr style={{ fontWeight: 'bold', backgroundColor: '#f9f9f9' }}>
                    <td colSpan={2} style={{ padding: '12px', textAlign: 'right' }}>Total:</td>
                    <td style={{ padding: '12px', textAlign: 'right', color: '#cc0000', fontSize: '1.2em' }}>
                      RM {total}.00
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>

            {/* Payment Section */}
            <div style={{ textAlign: 'center' }}>
              <p style={{ color: '#666', marginBottom: '20px' }}>
                Click the button below to proceed to secure payment via RevenueMonster.
              </p>

              <button
                type="button"
                onClick={handlePayment}
                disabled={processing}
                style={activeButtonStyle}
              >
                {processing ? 'Processing Payment...' : `Pay RM ${total}.00`}
              </button>

              <p style={{ marginTop: '20px', fontSize: '0.9em', color: '#888' }}>
                Secure payment powered by RevenueMonster
              </p>

              {/* Back button */}
              <button
                type="button"
                onClick={() => router.back()}
                disabled={processing}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#666',
                  cursor: 'pointer',
                  marginTop: '15px',
                  textDecoration: 'underline',
                }}
              >
                Go back and edit registration
              </button>
            </div>
          </div>
        </main>

        {/* Footer */}
        <footer style={{ textAlign: 'center', padding: '30px 20px', color: '#888', fontSize: '0.85em' }}>
          <p style={{ margin: 0 }}>Malaysia Aquatics (Persatuan Akuatik Malaysia)</p>
        </footer>
      </div>
    </>
  );
}
