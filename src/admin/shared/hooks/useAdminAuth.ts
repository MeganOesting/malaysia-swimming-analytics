/**
 * useAdminAuth Hook
 * Manages authentication state for the admin panel
 * Returns auth state and methods to update it
 */

import { useState, useCallback, useEffect } from 'react';
import { AuthState } from '../types/admin';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

export interface UseAdminAuthReturn extends AuthState {
  authenticate: (password: string) => Promise<boolean>;
  logout: () => void;
  clearError: () => void;
}

export function useAdminAuth(): UseAdminAuthReturn {
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    password: '',
    error: '',
  });

  // Restore auth state from localStorage on component mount
  useEffect(() => {
    const savedAuth = localStorage.getItem('adminAuth');
    if (savedAuth) {
      try {
        const auth = JSON.parse(savedAuth);
        if (auth.isAuthenticated) {
          setAuthState(auth);
        }
      } catch (err) {
        // Clear invalid localStorage data
        localStorage.removeItem('adminAuth');
      }
    }
  }, []);

  const authenticate = useCallback(async (password: string): Promise<boolean> => {
    try {
      const response = await fetch(`${API_BASE}/api/admin/authenticate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ password }),
      });

      if (response.ok) {
        const newAuthState = {
          isAuthenticated: true,
          password,
          error: '',
        };
        setAuthState(newAuthState);
        // Save auth state to localStorage
        localStorage.setItem('adminAuth', JSON.stringify(newAuthState));
        return true;
      } else {
        setAuthState(prev => ({
          ...prev,
          error: 'Invalid password',
        }));
        return false;
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Authentication failed';
      setAuthState(prev => ({
        ...prev,
        error: errorMessage,
      }));
      return false;
    }
  }, []);

  const logout = useCallback(() => {
    setAuthState({
      isAuthenticated: false,
      password: '',
      error: '',
    });
    // Clear auth state from localStorage
    localStorage.removeItem('adminAuth');
  }, []);

  const clearError = useCallback(() => {
    setAuthState(prev => ({
      ...prev,
      error: '',
    }));
  }, []);

  return {
    ...authState,
    authenticate,
    logout,
    clearError,
  };
}
