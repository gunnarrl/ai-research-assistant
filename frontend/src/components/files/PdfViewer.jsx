// frontend/src/components/PdfViewer.jsx
import React from 'react';

const PdfViewer = ({ pdfUrl }) => {
  if (!pdfUrl) {
    return (
      // Use h-full to make this container take up all available vertical space
      <div className="w-full h-full flex items-center justify-center bg-gray-100 border-r border-gray-200">
        <p className="text-gray-500">Loading PDF...</p>
      </div>
    );
  }

  return (
    // Use h-full here as well
    <div className="w-full h-full border-r border-gray-200">
      <embed src={pdfUrl} type="application/pdf" width="100%" height="100%" />
    </div>
  );
};

export default PdfViewer;