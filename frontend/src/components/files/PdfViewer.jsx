// frontend/src/components/PdfViewer.jsx
import React from 'react';

const PdfViewer = ({ pdfUrl }) => {
  if (!pdfUrl) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-100 border-r border-gray-200">
        <p className="text-gray-500">Upload a PDF to view it here.</p>
      </div>
    );
  }

  return (
    <div className="flex-1 border-r border-gray-200">
      <embed src={pdfUrl} type="application/pdf" width="100%" height="100%" />
    </div>
  );
};

export default PdfViewer;