/**
 * Reusable Button Component
 * Consistent styling across the admin panel
 */

import React from 'react';

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'success';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  fullWidth?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      loading = false,
      fullWidth = false,
      disabled = false,
      className = '',
      children,
      ...props
    },
    ref
  ) => {
    const baseStyles =
      'font-medium rounded transition-colors duration-200 flex items-center justify-center gap-2';

    const variantStyles = {
      primary:
        'text-white hover:opacity-90 disabled:opacity-50',
      secondary:
        'bg-gray-600 text-white hover:bg-gray-700 disabled:opacity-50',
      danger:
        'bg-red-700 text-white hover:bg-red-800 disabled:opacity-50',
      success:
        'bg-green-600 text-white hover:bg-green-700 disabled:opacity-50',
    };

    // Primary variant uses inline style for exact #cc0000 color per CLAUDE.md
    const primaryStyle = variant === 'primary' ? { backgroundColor: '#cc0000', color: 'white' } : undefined;

    // Disabled style uses standard gray per CLAUDE.md for all variants
    const disabledInlineStyle = (disabled || loading) && variant !== 'primary' ? { backgroundColor: '#9ca3af' } : undefined;

    const sizeStyles = {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2 text-base',
      lg: 'px-6 py-3 text-lg',
    };

    const widthStyle = fullWidth ? 'w-full' : '';
    const disabledStyle = disabled || loading ? 'opacity-75 cursor-not-allowed' : '';

    const finalClassName = `
      ${baseStyles}
      ${variantStyles[variant]}
      ${sizeStyles[size]}
      ${widthStyle}
      ${disabledStyle}
      ${className}
    `.trim();

    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={finalClassName}
        style={{ ...primaryStyle, ...disabledInlineStyle }}
        {...props}
      >
        {loading && (
          <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
        )}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
