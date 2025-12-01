import React from 'react';

const Loading = ({ message = 'Loading...', fullScreen = false }) => {
  if (fullScreen) {
    return (
      <div className="min-h-screen bg-gradient-blue flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-white mb-4"></div>
          <div className="text-white text-2xl font-semibold">{message}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="text-center py-12">
      <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-blue-500 mb-4"></div>
      <div className="text-gray-600 text-lg">{message}</div>
    </div>
  );
};

export default Loading;
