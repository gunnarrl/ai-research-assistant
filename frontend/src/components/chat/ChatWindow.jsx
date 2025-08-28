// frontend/src/components/ChatWindow.jsx
import React from 'react';

const ChatWindow = ({ chatHistory }) => {
  return (
    <div className="flex-grow p-4 bg-gray-50 border border-gray-200 rounded-lg h-96 overflow-y-auto">
      <div className="space-y-4">
        {chatHistory.map((message, index) => (
          <div key={index} className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-xs md:max-w-md lg:max-w-lg px-4 py-2 rounded-xl whitespace-pre-wrap ${
                message.sender === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-gray-800'
              }`}
            >
              {message.text}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ChatWindow;