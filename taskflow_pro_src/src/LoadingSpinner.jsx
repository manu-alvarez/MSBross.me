import React from 'react';

const LoadingSpinner = ({ message = 'Cargando...' }) => (
  <div className="min-h-screen flex items-center justify-center p-4">
    <div className="text-center">
      <div className="inline-block w-12 h-12 border-4 border-purple-200 border-t-purple-600 rounded-full animate-spin" />
      <p className="mt-3 text-white/80">{message}</p>
    </div>
  </div>
);

export default LoadingSpinner;
