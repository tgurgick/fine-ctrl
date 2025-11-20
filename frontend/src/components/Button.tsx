import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'success' | 'outline';
  size?: 'xs' | 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  disabled,
  leftIcon,
  rightIcon,
  className = '',
  ...props
}) => {
  const baseStyles =
    'inline-flex items-center justify-center font-medium rounded-lg ' +
    'transition-all duration-200 ease-out ' +
    'focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 ' +
    'disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none ' +
    'active:scale-[0.98]';

  const variantStyles = {
    primary:
      'bg-primary-600 text-white shadow-sm ' +
      'hover:bg-primary-700 hover:shadow-md ' +
      'focus-visible:ring-primary-500',
    secondary:
      'bg-neutral-100 text-neutral-900 border border-neutral-200 ' +
      'hover:bg-neutral-200 hover:border-neutral-300 ' +
      'focus-visible:ring-neutral-400',
    ghost:
      'bg-transparent text-neutral-700 ' +
      'hover:bg-neutral-100 ' +
      'focus-visible:ring-neutral-400',
    danger:
      'bg-error-600 text-white shadow-sm ' +
      'hover:bg-error-700 hover:shadow-md ' +
      'focus-visible:ring-error-500',
    success:
      'bg-success-600 text-white shadow-sm ' +
      'hover:bg-success-700 hover:shadow-md ' +
      'focus-visible:ring-success-500',
    outline:
      'bg-white text-neutral-700 border-2 border-neutral-300 ' +
      'hover:border-primary-500 hover:text-primary-700 hover:bg-primary-50 ' +
      'focus-visible:ring-primary-500',
  };

  const sizeStyles = {
    xs: 'px-2.5 py-1.5 text-xs gap-1',
    sm: 'px-3 py-2 text-sm gap-1.5',
    md: 'px-4 py-2.5 text-sm gap-2',
    lg: 'px-5 py-3 text-base gap-2.5',
  };

  return (
    <button
      className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <>
          <svg
            className="animate-spin h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          <span>Loading...</span>
        </>
      ) : (
        <>
          {leftIcon && <span className="flex-shrink-0">{leftIcon}</span>}
          {children}
          {rightIcon && <span className="flex-shrink-0">{rightIcon}</span>}
        </>
      )}
    </button>
  );
};
