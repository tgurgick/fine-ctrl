import React from 'react';

interface ProgressBarProps {
  progress: number; // 0-100
  label?: string;
  className?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({ progress, label, className = '' }) => {
  const clampedProgress = Math.min(100, Math.max(0, progress));

  return (
    <div className={`w-full ${className}`}>
      {label && (
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-700">{label}</span>
          <span className="text-sm font-medium text-gray-700">{Math.round(clampedProgress)}%</span>
        </div>
      )}
      <div className="w-full bg-gray-200 rounded-full h-2.5">
        <div
          className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
          style={{ width: `${clampedProgress}%` }}
        ></div>
      </div>
    </div>
  );
};
