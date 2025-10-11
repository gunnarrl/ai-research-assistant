// frontend/src/components/chat/ChatPane.jsx
import React, { useState } from 'react';
import ChatWindow from './ChatWindow';
import ChatInput from './ChatInput';
import StructuredDataDisplay from './StructuredDataDisplay';
import BibliographyDisplay from './BibliographyDisplay';
import CitationDisplay from './CitationDisplay';

// Add 'document' to the destructured props
const ChatPane = ({ document, chatHistory, onSendMessage, isLoading, onReturnToDashboard, citations, token }) => {
  const [isOpen, setIsOpen] = useState(true);
  const [activeTab, setActiveTab] = useState('insights');

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="absolute bottom-4 right-4 bg-blue-600 text-white rounded-full p-4 shadow-lg hover:bg-blue-700"
      >
        Open Chat
      </button>
    );
  }

return (
    <div className="w-full md:w-1/2 lg:w-1/3 flex flex-col bg-white shadow-lg border-l border-gray-200 h-full">
      <div className="p-4 border-b flex justify-between items-center">
        <button onClick={onReturnToDashboard} className="text-sm text-blue-600 hover:underline">
          &larr; Back to Dashboard
        </button>
        <h2 className="text-xl font-bold">Chat</h2>
        <button onClick={() => setIsOpen(false)} className="text-gray-500 hover:text-gray-800">&times;</button>
      </div>

      <div className="flex-grow flex flex-col p-4 min-h-0">
        <div className="flex-1 flex flex-col space-y-4 min-h-0">
          
          {/* --- TAB CONTAINER --- */}
          <div className="flex-none h-1/3 flex flex-col">
            <div className="flex border-b border-gray-200">
              <button
                onClick={() => setActiveTab('insights')}
                className={`px-4 py-2 text-sm font-medium ${activeTab === 'insights' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
              >
                Insights
              </button>
              {/* --- ADD CITATION TAB BUTTON --- */}
              <button
                onClick={() => setActiveTab('citation')}
                className={`px-4 py-2 text-sm font-medium ${activeTab === 'citation' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
              >
                Citation
              </button>
              <button
                onClick={() => setActiveTab('bibliography')}
                className={`px-4 py-2 text-sm font-medium ${activeTab === 'bibliography' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
              >
                Bibliography
              </button>
            </div>
            <div className="flex-1 min-h-0">
              {activeTab === 'insights' && <StructuredDataDisplay data={document?.structured_data} />}
              {/* --- RENDER NEW COMPONENT --- */}
              {activeTab === 'citation' && <CitationDisplay documentId={document?.id} token={token} />}
              {activeTab === 'bibliography' && <BibliographyDisplay citations={citations} documentId={document?.id} token={token} />}
            </div>
          </div>
          {/* --- CHAT WINDOW --- */}
          <ChatWindow chatHistory={chatHistory} />
        </div>
        
        <div className="flex-none pt-4">
          <ChatInput onSendMessage={onSendMessage} isLoading={isLoading} />
        </div>
      </div>
    </div>
  );
};

export default ChatPane;