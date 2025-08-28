// frontend/src/components/ChatPane.jsx
import React, { useState } from 'react';
import ChatWindow from './ChatWindow';
import ChatInput from './ChatInput';

const ChatPane = ({ chatHistory, onSendMessage, isLoading }) => {
  const [isOpen, setIsOpen] = useState(true);

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
        <h2 className="text-xl font-bold">Chat</h2>
        <button onClick={() => setIsOpen(false)} className="text-gray-500 hover:text-gray-800">&times;</button>
      </div>
      <div className="flex-grow flex flex-col p-4 space-y-4">
        <ChatWindow chatHistory={chatHistory} />
        <ChatInput onSendMessage={onSendMessage} isLoading={isLoading} />
      </div>
    </div>
  );
};

export default ChatPane;