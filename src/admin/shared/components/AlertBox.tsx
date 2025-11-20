/**
 * Reusable Alert/Message Box Component
 * For displaying success, error, warning, and info messages
 */

import React from 'react';

export interface AlertBoxProps {
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  title?: string;
  onClose?: () => void;
  dismissible?: boolean;
  className?: string;
}

export const AlertBox: React.FC<AlertBoxProps> = ({
  type,
  message,
  title,
  onClose,
  dismissible = true,
  className = '',
}) => {
  const styles = {
    success: {
      bg: 'bg-green-50',
      border: 'border-green-200',
      icon: '✓',
      iconColor: 'text-green-600',
      textColor: 'text-green-800',
      titleColor: 'text-green-900',
    },
    error: {
      bg: 'bg-red-50',
      border: 'border-red-200',
      icon: '✕',
      iconColor: 'text-red-600',
      textColor: 'text-red-800',
      titleColor: 'text-red-900',
    },
    warning: {
      bg: 'bg-yellow-50',
      border: 'border-yellow-200',
      icon: '⚠',
      iconColor: 'text-yellow-600',
      textColor: 'text-yellow-800',
      titleColor: 'text-yellow-900',
    },
    info: {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      icon: 'ℹ',
      iconColor: 'text-blue-600',
      textColor: 'text-blue-800',
      titleColor: 'text-blue-900',
    },
  };

  const style = styles[type];

  return (
    <div
      className={`
        ${style.bg} ${style.border}
        border rounded-lg p-4 mb-4 flex gap-3
        ${className}
      `.trim()}
      role="alert"
    >
      <span className={`${style.iconColor} text-xl flex-shrink-0 font-bold`}>
        {style.icon}
      </span>
      <div className="flex-1 min-w-0">
        {title && (
          <h3 className={`${style.titleColor} font-semibold text-sm mb-1`}>
            {title}
          </h3>
        )}
        <p className={`${style.textColor} text-sm break-words`}>
          {message}
        </p>
      </div>
      {dismissible && onClose && (
        <button
          onClick={onClose}
          className={`${style.iconColor} flex-shrink-0 hover:opacity-75 transition-opacity`}
          aria-label="Close alert"
        >
          ✕
        </button>
      )}
    </div>
  );
};

AlertBox.displayName = 'AlertBox';
