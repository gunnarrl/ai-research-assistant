// frontend/src/components/dashboard/ArxivSearch.jsx
import React, { useState } from 'react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

// Receive token and onImport function as props
const ArxivSearch = ({ token, onImportSuccess }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [importingId, setImportingId] = useState(null); // Tracks which paper is being imported

  const handleSearch = async (event) => {
    event.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    setError('');
    setResults([]);

    try {
      const response = await fetch(`${BACKEND_URL}/arxiv/search?query=${encodeURIComponent(query)}&max_results=5`);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to fetch search results.');
      }

      const data = await response.json();
      setResults(data);

    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleImport = async (paper) => {
    setImportingId(paper.pdf_url); // Use pdf_url as a unique ID for loading state
    setError('');

    try {
        const response = await fetch(`${BACKEND_URL}/import-from-url`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                pdf_url: paper.pdf_url,
                title: paper.title
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Failed to import paper.");
        }

        // Call the success handler passed from the parent
        onImportSuccess();

    } catch (err) {
        setError(err.message);
    } finally {
        setImportingId(null);
    }
  };

  return (
    <div>
      <h3 className="text-xl font-bold text-gray-800 mb-4">Search & Import from arXiv</h3>
      <form onSubmit={handleSearch} className="flex items-center space-x-2 mb-6">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search for research papers..."
          className="flex-grow px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading || !query.trim()}
          className="px-5 py-2 bg-blue-600 text-white font-semibold rounded-lg shadow-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:bg-gray-400"
        >
          {isLoading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {error && <p className="text-red-500 my-2">{error}</p>}

      <div className="space-y-4">
        {results.length > 0 && results.map((paper, index) => (
          <div key={index} className="p-4 rounded-lg border bg-gray-50 border-gray-200">
            <div className="flex justify-between items-start">
              <div>
                <h4 className="font-bold text-lg text-gray-800">{paper.title}</h4>
                <p className="text-sm text-gray-600 italic">by {paper.authors.join(', ')}</p>
                <p className="mt-2 text-gray-700 text-sm">{paper.summary}</p>
              </div>
              <button
                onClick={() => handleImport(paper)}
                disabled={importingId === paper.pdf_url}
                className="ml-4 px-4 py-2 bg-green-600 text-white text-sm font-semibold rounded-lg shadow-md hover:bg-green-700 disabled:bg-gray-400 flex-shrink-0"
              >
                {importingId === paper.pdf_url ? 'Importing...' : 'Import'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ArxivSearch;