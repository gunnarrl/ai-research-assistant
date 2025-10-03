// frontend/src/components/chat/MultiDocList.jsx
import React from 'react';

const MultiDocList = ({ documents, currentDocId, onSelect }) => {
  return (
    <div className="h-full flex flex-col">
      <h3 className="text-lg font-bold text-gray-800 mb-4 p-2">Selected Documents</h3>
      <div className="flex-1 overflow-y-auto">
        <ul className="space-y-2">
          {documents.map(doc => (
            <li key={doc.id}>
              <button
                onClick={() => onSelect(doc.id)}
                className={`w-full text-left p-2 rounded-md text-sm ${
                  doc.id === currentDocId
                    ? 'bg-blue-600 text-white font-semibold'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                {doc.filename}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default MultiDocList;