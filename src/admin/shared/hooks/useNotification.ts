/**
 * useNotification Hook
 * Manages success/error notification state for a feature
 * Provides consistent message handling across all features
 */

import { useState, useCallback } from 'react';

export type NotificationType = 'success' | 'error' | 'info' | 'warning';

export interface Notification {
  message: string;
  type: NotificationType;
  id: string;
}

export interface UseNotificationReturn {
  notifications: Notification[];
  success: (message: string) => void;
  error: (message: string) => void;
  info: (message: string) => void;
  warning: (message: string) => void;
  clear: (id?: string) => void;
  clearAll: () => void;
}

/**
 * Hook for managing notification/toast messages
 * @param autoHideDuration - Time in ms before notification auto-hides (0 = no auto-hide)
 * @returns Object with notifications array and methods to show/clear them
 */
export function useNotification(autoHideDuration: number = 5000): UseNotificationReturn {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const addNotification = useCallback(
    (message: string, type: NotificationType) => {
      const id = `${Date.now()}-${Math.random()}`;
      setNotifications(prev => [...prev, { message, type, id }]);

      if (autoHideDuration > 0) {
        setTimeout(() => {
          setNotifications(prev => prev.filter(n => n.id !== id));
        }, autoHideDuration);
      }
    },
    [autoHideDuration]
  );

  const success = useCallback(
    (message: string) => addNotification(message, 'success'),
    [addNotification]
  );

  const error = useCallback(
    (message: string) => addNotification(message, 'error'),
    [addNotification]
  );

  const info = useCallback(
    (message: string) => addNotification(message, 'info'),
    [addNotification]
  );

  const warning = useCallback(
    (message: string) => addNotification(message, 'warning'),
    [addNotification]
  );

  const clear = useCallback((id?: string) => {
    if (id) {
      setNotifications(prev => prev.filter(n => n.id !== id));
    }
  }, []);

  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  return {
    notifications,
    success,
    error,
    info,
    warning,
    clear,
    clearAll,
  };
}

/**
 * Helper to show a simple success/error message
 * Can be used standalone without the hook
 */
export function showNotification(
  message: string,
  type: NotificationType = 'info'
): void {
  if (typeof window !== 'undefined') {
    // Could integrate with a toast library here if needed
    const bgColor = {
      success: 'bg-green-600',
      error: 'bg-red-600',
      warning: 'bg-yellow-600',
      info: 'bg-blue-600',
    }[type];

    console.log(`[${type.toUpperCase()}] ${message}`);
  }
}
