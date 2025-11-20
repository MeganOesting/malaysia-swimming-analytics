import React, { useState, ReactNode } from 'react';

interface AdminAuthGuardProps {
    children: ReactNode;
    isAuthenticated: boolean;
    setIsAuthenticated: (auth: boolean) => void;
}

export default function AdminAuthGuard({
    children,
    isAuthenticated,
    setIsAuthenticated,
}: AdminAuthGuardProps) {
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        try {
            const response = await fetch('http://localhost:8000/api/admin/authenticate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ password }),
            });

            const result = await response.json();

            if (response.ok) {
                setIsAuthenticated(true);
                localStorage.setItem('admin_authenticated', 'true');
                setPassword('');
                setError('');
            } else {
                setError(result.detail || result.message || 'Invalid password');
            }
        } catch (err: any) {
            setError(err.message || 'Authentication failed');
        }
    };

    if (!isAuthenticated) {
        return (
            <div style={{
                fontFamily: 'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
                minHeight: '100vh',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: '#f5f5f5'
            }}>
                <div style={{
                    backgroundColor: 'white',
                    padding: '2rem',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
                    width: '100%',
                    maxWidth: '400px'
                }}>
                    <h1 style={{
                        textAlign: 'center',
                        marginBottom: '1.5rem',
                        color: '#333'
                    }}>
                        🏊 Malaysia Swimming Analytics
                    </h1>
                    <p style={{
                        textAlign: 'center',
                        marginBottom: '1rem',
                        color: '#666',
                        fontSize: '0.9rem'
                    }}>
                        Admin Panel - Enter password to access
                    </p>

                    <form onSubmit={handleLogin}>
                        <div style={{ marginBottom: '1rem' }}>
                            <label style={{
                                display: 'block',
                                marginBottom: '0.5rem',
                                fontWeight: '500'
                            }}>
                                Admin Password:
                            </label>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                style={{
                                    width: '100%',
                                    padding: '0.75rem',
                                    border: '1px solid #ddd',
                                    borderRadius: '4px',
                                    fontSize: '1rem',
                                    boxSizing: 'border-box'
                                }}
                                required
                            />
                        </div>

                        {error && (
                            <div style={{
                                color: '#dc2626',
                                marginBottom: '1rem',
                                padding: '0.75rem',
                                backgroundColor: '#fef2f2',
                                borderRadius: '4px',
                                border: '1px solid #fecaca'
                            }}>
                                {error}
                            </div>
                        )}

                        <button
                            type="submit"
                            style={{
                                width: '100%',
                                padding: '0.75rem',
                                backgroundColor: '#cc0000',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                fontSize: '1rem',
                                cursor: 'pointer',
                                fontWeight: '600'
                            }}
                        >
                            Login
                        </button>
                    </form>
                </div>
            </div>
        );
    }

    return <>{children}</>;
}
