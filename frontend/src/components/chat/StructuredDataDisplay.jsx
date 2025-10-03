// frontend/src/components/chat/StructuredDataDisplay.jsx
import React from 'react';

const StructuredDataDisplay = ({ data }) => {
  // Don't render anything if data is null or empty
  if (!data || Object.keys(data).length === 0 || data.error) {
    return null;
  }

  const { methodology, dataset, key_findings } = data;

  return (
    <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg space-y-3 text-sm h-full overflow-y-auto">
      <h3 className="text-lg font-bold text-gray-800 mb-2">Extracted Insights</h3>
      
      {methodology && (
        <div>
          <h4 className="font-semibold text-gray-700">Methodology</h4>
          <p className="text-gray-600">{methodology}</p>
        </div>
      )}

      {dataset && (
        <div>
          <h4 className="font-semibold text-gray-700">Dataset</h4>
          <p className="text-gray-600">{dataset}</p>
        </div>
      )}

      {key_findings && key_findings.length > 0 && (
        <div>
          <h4 className="font-semibold text-gray-700">Key Findings</h4>
          <ul className="list-disc list-inside text-gray-600 space-y-1">
            {key_findings.map((finding, index) => (
              <li key={index}>{finding}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default StructuredDataDisplay;