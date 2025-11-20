/**
 * useFetch Hook
 * Wrapper around fetch with error handling and loading state
 * Provides consistent API call handling across all features
 */

import { useState, useCallback } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

export interface UseFetchOptions extends RequestInit {
  timeout?: number;
}

export interface UseFetchReturn<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  fetch: () => Promise<void>;
}

/**
 * Hook for making API calls with loading and error states
 * @param url - Relative or absolute URL to fetch
 * @param options - Fetch options (method, headers, body, timeout, etc.)
 * @returns Object with data, loading, error, and fetch function
 */
export function useFetch<T = any>(
  url: string,
  options: UseFetchOptions = {}
): UseFetchReturn<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    const { timeout = 30000, ...fetchOptions } = options;

    setLoading(true);
    setError(null);

    try {
      const fullUrl = url.startsWith('http') ? url : `${API_BASE}${url}`;

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      const response = await global.fetch(fullUrl, {
        ...fetchOptions,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const json = await response.json();
      setData(json);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [url, options]);

  return { data, loading, error, fetch };
}

/**
 * Helper to make a one-time API call without hook syntax
 * Useful for event handlers and imperative code
 */
export async function apiCall<T = any>(
  url: string,
  options: UseFetchOptions = {}
): Promise<{ data: T | null; error: string | null }> {
  const { timeout = 30000, ...fetchOptions } = options;

  try {
    const fullUrl = url.startsWith('http') ? url : `${API_BASE}${url}`;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    const response = await global.fetch(fullUrl, {
      ...fetchOptions,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const json = await response.json();
    return { data: json as T, error: null };
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    return { data: null, error: errorMessage };
  }
}
