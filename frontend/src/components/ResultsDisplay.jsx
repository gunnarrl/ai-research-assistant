// ResultsDisplay Component: Shows the summary, error messages, or a loading spinner.
import React from 'react';

const ResultsDisplay = ({ error, summary, isLoading }) => {
  if (isLoading) {
    return (
      <div className="flex justify-center items-center p-4">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg" role="alert">
          <strong className="font-bold">Error: </strong>
          <span className="block sm:inline">{error}</span>
        </div>
      )}
      {summary && (
        <div className="p-5 bg-gray-50 rounded-lg border border-gray-200">
          <h2 className="text-xl font-bold text-gray-800 mb-3">Summary</h2>
          <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">{summary}</p>
        </div>
      )}
    </div>
  );
};

export default ResultsDisplay;