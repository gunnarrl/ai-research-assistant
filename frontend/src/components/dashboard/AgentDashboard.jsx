// frontend/src/components/dashboard/AgentDashboard.jsx

import React, { useState, useEffect } from 'react';

const BACKEND_URL = "http://127.0.0.1:8000";

const AgentDashboard = ({ token }) => {
  const [topic, setTopic] = useState('');
  const [activeReview, setActiveReview] = useState(null);
  const [isLoading, setIsLoading] = useState(false); // Used for starting a new review
  const [isChecking, setIsChecking] = useState(true); // NEW: For the initial check
  const [error, setError] = useState('');

  // --- NEW: Effect to check for an active review on component mount ---
  useEffect(() => {
    const checkForActiveReview = async () => {
      setIsChecking(true);
      try {
        const response = await fetch(`${BACKEND_URL}/agent/literature-review/active`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (response.ok) {
          const data = await response.json();
          if (data) {
            setActiveReview(data); // If an active review is found, set it
          }
        }
      } catch (err) {
        console.error("Failed to check for active review:", err);
      } finally {
        setIsChecking(false);
      }
    };
    checkForActiveReview();
  }, [token]);

  const handleStartReview = async (e) => {
    e.preventDefault();
    if (!topic.trim()) return;

    setIsLoading(true);
    setError('');
    setActiveReview(null);

    try {
      const response = await fetch(`${BACKEND_URL}/agent/literature-review`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ topic })
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Failed to start agent.');
      }
      const data = await response.json();
      setActiveReview(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const renderStatus = () => {
    if (!activeReview) return null;

    const statusMap = {
      PENDING: "Agent is starting...",
      SEARCHING: "Searching for relevant papers on arXiv...",
      SUMMARIZING: "Downloading and summarizing selected papers...",
      SYNTHESIZING: "Synthesizing the final literature review...",
      FAILED: "The agent encountered an error."
    };

    if (activeReview.status === 'COMPLETED') return null;

    return (
      <div className="mt-6 flex items-center justify-center space-x-3 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
        <p className="text-blue-700 font-medium">{statusMap[activeReview.status] || 'Processing...'}</p>
      </div>
    );
  };
  
  const renderResult = () => {
    if (!activeReview || activeReview.status !== 'COMPLETED') return null;
    
    return (
      <div className="mt-6 p-4 bg-gray-50 border border-gray-200 rounded-lg">
        <h4 className="text-lg font-bold text-gray-800 mb-2">Literature Review on "{activeReview.topic}"</h4>
        <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">{activeReview.result}</p>
      </div>
    );
  };


  if (isChecking) {
    return (
      <div>
        <h3 className="text-xl font-bold text-gray-800 mb-4">Literature Review Agent</h3>
        <p className="text-gray-500">Checking for active reviews...</p>
      </div>
    );
  }
  
  return (
    <div>
      <h3 className="text-xl font-bold text-gray-800 mb-4">Literature Review Agent</h3>
      <form onSubmit={handleStartReview} className="flex items-center space-x-2 mb-2">
        <input
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="Enter a research topic..."
          className="flex-grow px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
          disabled={isLoading || (activeReview && activeReview.status !== 'COMPLETED' && activeReview.status !== 'FAILED')}
        />
        <button
          type="submit"
          disabled={isLoading || !topic.trim() || (activeReview && activeReview.status !== 'COMPLETED' && activeReview.status !== 'FAILED')}
          className="px-5 py-2 bg-purple-600 text-white font-semibold rounded-lg shadow-md hover:bg-purple-700 disabled:bg-gray-400"
        >
          {isLoading ? 'Starting...' : 'Start Review'}
        </button>
      </form>
      {error && <p className="text-red-500 my-2">{error}</p>}
      
      {renderStatus()}
      {renderResult()}
    </div>
  );
};

export default AgentDashboard;