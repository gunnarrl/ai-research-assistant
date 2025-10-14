// frontend/src/components/chat/BibliographyDisplay.jsx
import React from 'react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

const BibliographyDisplay = ({ citations, documentId, token }) => {
  if (!citations || citations.length === 0) {
    return (
      <div className="p-4 h-full flex items-center justify-center">
        <p className="text-gray-500 text-sm">No citations extracted for this document.</p>
      </div>
    );
  }

  const handleExport = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/documents/${documentId}/citations/export?format=bibtex`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) {
        throw new Error('Failed to download BibTeX file.');
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      // Extract filename from content-disposition header, or use a default
      const contentDisposition = response.headers.get('content-disposition');
      let filename = 'citations.bib';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch.length > 1) {
          filename = filenameMatch[1];
        }
      }
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Export failed:", error);
      alert("Could not export citations.");
    }
  };


  return (
    <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg space-y-3 text-sm h-full flex flex-col">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-lg font-bold text-gray-800">Bibliography</h3>
        <button
          onClick={handleExport}
          className="px-3 py-1 bg-blue-600 text-white text-xs font-semibold rounded-lg shadow-sm hover:bg-blue-700"
        >
          Export as BibTeX
        </button>
      </div>
      <div className="flex-1 overflow-y-auto pr-2 space-y-4">
        {citations.map((citation) => (
          <div key={citation.id} className="text-gray-700">
            <p className="font-semibold text-gray-800">{citation.data.title}</p>
            <p className="text-xs text-gray-500">
              {citation.data.authors && citation.data.authors.join(', ')} ({citation.data.year})
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default BibliographyDisplay;