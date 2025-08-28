// frontend/src/components/ChatInput.jsx
import React, { useState } from 'react';

const ChatInput = ({ onSendMessage, isLoading }) => {
  const [question, setQuestion] = useState('');

  const handleSubmit = (event) => {
    event.preventDefault();
    if (!question.trim()) return;
    onSendMessage(question);
    setQuestion('');
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-center space-x-2">
      <input
        type="text"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Ask a question about the document..."
        className="flex-grow px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
        disabled={isLoading}
      />
      <button
        type="submit"
        disabled={isLoading || !question.trim()}
        className="px-5 py-2 bg-blue-600 text-white font-semibold rounded-lg shadow-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors duration-300"
      >
        Send
      </button>
    </form>
  );
};

export default ChatInput;