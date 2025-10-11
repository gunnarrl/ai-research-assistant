// gunnarrl/ai-research-assistant/ai-research-assistant-bug-fixing/frontend/src/components/dashboard/LiteratureReviewViewPage.jsx

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const LiteratureReviewViewPage = ({ review, onReturnToDashboard }) => {
  return (
    <div className="bg-slate-50 min-h-screen font-sans p-4">
      <div className="w-full max-w-4xl mx-auto bg-white rounded-2xl shadow-xl p-8 space-y-8">
        <div className="flex justify-between items-center">
          <div>
            <button onClick={onReturnToDashboard} className="text-sm text-blue-600 hover:underline mb-2">
              &larr; Back to Dashboard
            </button>
            <h2 className="text-3xl font-bold text-gray-900">{review.topic}</h2>
          </div>
        </div>
        <div>
          <h3 className="text-xl font-bold text-gray-800 mb-4">Literature Review</h3>
          {/* --- 2. REPLACE <p> WITH THE ReactMarkdown COMPONENT --- */}
          <div className="prose max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {review.result}
            </ReactMarkdown>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiteratureReviewViewPage;