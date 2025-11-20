/**
 * Shared hooks index
 * Re-exports all shared hooks for easy importing
 */

export { useAdminAuth, type UseAdminAuthReturn } from './useAdminAuth';
export { useFetch, apiCall, type UseFetchOptions, type UseFetchReturn } from './useFetch';
export { useNotification, showNotification, type NotificationType, type Notification, type UseNotificationReturn } from './useNotification';
