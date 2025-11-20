import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  variant?: 'default' | 'filled';
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  helperText,
  leftIcon,
  rightIcon,
  variant = 'filled',
  className = '',
  id,
  ...props
}) => {
  const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');

  const variantStyles = {
    default: 'bg-white border-neutral-300 focus:border-primary-500',
    filled: 'bg-neutral-50 border-neutral-200 focus:bg-white focus:border-primary-500',
  };

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={inputId}
          className="block text-sm font-medium text-neutral-700 mb-2"
        >
          {label}
        </label>
      )}
      <div className="relative">
        {leftIcon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-neutral-400">
            {leftIcon}
          </div>
        )}
        <input
          id={inputId}
          className={`
            block w-full rounded-lg border shadow-sm
            transition-all duration-200
            text-neutral-900 placeholder:text-neutral-400
            focus:outline-none focus:ring-4 focus:ring-primary-500/10
            disabled:bg-neutral-100 disabled:text-neutral-500 disabled:cursor-not-allowed
            ${leftIcon ? 'pl-10' : 'pl-3.5'}
            ${rightIcon ? 'pr-10' : 'pr-3.5'}
            py-2.5
            ${error
              ? 'border-error-500 focus:border-error-500 focus:ring-error-500/10'
              : variantStyles[variant]
            }
            ${className}
          `}
          {...props}
        />
        {rightIcon && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none text-neutral-400">
            {rightIcon}
          </div>
        )}
      </div>
      {error && (
        <p className="mt-2 text-sm text-error-600 flex items-center gap-1">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          {error}
        </p>
      )}
      {helperText && !error && (
        <p className="mt-2 text-sm text-neutral-500">
          {helperText}
        </p>
      )}
    </div>
  );
};
