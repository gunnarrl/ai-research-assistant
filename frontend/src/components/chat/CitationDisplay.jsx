// frontend/src/components/chat/CitationDisplay.jsx
import React, { useState } from 'react';

const BACKEND_URL = "http://127.0.0.1:8000";

const CitationDisplay = ({ documentId, token }) => {
  const [bibtex, setBibtex] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleGenerateCitation = async () => {
    setIsLoading(true);
    setError('');
    setBibtex('');

    try {
      const response = await fetch(`${BACKEND_URL}/documents/${documentId}/generate-bibtex`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) {
        throw new Error('Failed to generate citation.');
      }
      
      // We expect plain text for the BibTeX content
      const bibtexText = await response.text();
      setBibtex(bibtexText);

    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = () => {
    if (!bibtex) return;
    const blob = new Blob([bibtex], { type: 'application/x-bibtex' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `citation_${documentId}.bib`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg h-full flex flex-col">
      <h3 className="text-lg font-bold text-gray-800 mb-4">Source Citation</h3>
      
      {!bibtex && (
        <div className="flex-1 flex items-center justify-center">
          <button
            onClick={handleGenerateCitation}
            disabled={isLoading}
            className="px-4 py-2 bg-blue-600 text-white font-semibold rounded-lg shadow-md hover:bg-blue-700 disabled:bg-gray-400"
          >
            {isLoading ? 'Generating...' : 'Generate BibTeX Citation'}
          </button>
        </div>
      )}

      {error && <p className="text-red-500 text-sm">{error}</p>}

      {bibtex && (
        <div className="flex-1 flex flex-col min-h-0">
          <pre className="text-xs bg-white p-3 rounded border border-gray-300 overflow-auto flex-1">
            <code>{bibtex}</code>
          </pre>
          <button
            onClick={handleDownload}
            className="mt-4 px-4 py-2 bg-green-600 text-white font-semibold rounded-lg shadow-md hover:bg-green-700"
          >
            Download .bib File
          </button>
        </div>
      )}
    </div>
  );
};

export default CitationDisplay;