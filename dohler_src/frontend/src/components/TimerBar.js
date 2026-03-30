/**
 * TimerBar Component
 * Visual progress bar for timer
 */
import React from 'react';

export default function TimerBar({ progress, isRunning }) {
  const width = Math.max(0, Math.min(100, progress));
  
  // Calculate color based on progress
  const getProgressColor = () => {
    if (width >= 90) return 'bg-red-500';
    if (width >= 70) return 'bg-yellow-500';
    return 'bg-indigo-600';
  };

  return (
    <div className="w-full">
      {/* Progress Bar */}
      <div className="relative w-full h-4 bg-gray-200 rounded-full overflow-hidden">
        <div 
          className={`absolute inset-0 ${getProgressColor()} rounded-full transition-all duration-1000 ease-out`}
          style={{ width: `${width}%` }}
        ></div>
        
        {/* Animated stripe pattern when running */}
        {isRunning && (
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse"></div>
        )}
      </div>
      
      {/* Progress Text */}
      <div className="flex justify-between items-center mt-2 text-sm">
        <span className="text-gray-500">
          {isRunning ? '⏱️ En progreso' : '⏸️ Esperando'}
        </span>
        <span className={`font-medium ${width >= 100 ? 'text-green-600' : 'text-gray-700'}`}>
          {Math.round(width)}%
        </span>
      </div>
    </div>
  );
}