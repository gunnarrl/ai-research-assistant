// frontend/src/App.jsx
import React, { useState, useEffect } from 'react';
import PdfViewer from './components/files/PdfViewer';
import ChatPane from './components/chat/ChatPane';
import LoginPage from './components/auth/LoginPage';
import DashboardPage from './components/dashboard/DashboardPage';

const BACKEND_URL = "http://127.0.0.1:8000";
const TOKEN_KEY = 'authToken';

function App() {
  const [token, setToken] = useState(localStorage.getItem(TOKEN_KEY));
  const [selectedDocument, setSelectedDocument] = useState(null);

  // Chat-specific state
  const [chatHistory, setChatHistory] = useState([]);
  const [isAnswering, setIsAnswering] = useState(false);
  const [pdfUrl, setPdfUrl] = useState(null);

  const handleLoginSuccess = (newToken) => {
    localStorage.setItem(TOKEN_KEY, newToken);
    setToken(newToken);
  };

  const handleLogout = () => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setSelectedDocument(null);
  };

  const handleSelectDocument = async (doc) => {
    // We only have the filename, we need to fetch the file blob to display it.
    // This is a simplified approach. For larger files, you'd get a direct URL from a cloud storage.
    // For now, we simulate selecting the document by just setting it.
    // NOTE: For the PDF viewer to work, we'd need to adjust the flow to have access to the file blob.
    // We will simplify for now and pass a placeholder, focusing on the chat functionality.
    setSelectedDocument(doc);
    setPdfUrl(null); // Cannot display PDF without the file blob, so we clear it.
    setChatHistory([{ sender: 'ai', text: `Selected "${doc.filename}". Ask me anything!` }]);
  };

  const handleSendMessage = async (question) => {
    if (!selectedDocument) return;

    const newUserMessage = { sender: 'user', text: question };
    setChatHistory(prev => [...prev, newUserMessage]);
    setIsAnswering(true);

    try {
      const response = await fetch(`${BACKEND_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` // Add token to chat requests
        },
        body: JSON.stringify({
          document_id: selectedDocument.id,
          question: question,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || `HTTP error! Status: ${response.status}`);
      }

      const result = await response.json();
      const aiResponse = { sender: 'ai', text: result.answer };
      setChatHistory(prev => [...prev, aiResponse]);

    } catch (err) {
      const errorResponse = { sender: 'ai', text: `Sorry, an error occurred: ${err.message}` };
      setChatHistory(prev => [...prev, errorResponse]);
    } finally {
      setIsAnswering(false);
    }
  };


  // --- Conditional Rendering Logic ---

  if (selectedDocument) {
    return (
      <div className="flex w-screen h-screen font-sans">
        {/* Simplified view: In a real app, you'd fetch the PDF blob to view it */}
        <div className="flex-1 flex items-center justify-center bg-gray-100 border-r border-gray-200">
            <p className="text-gray-600 text-center">
                Chatting about <br/>
                <strong className="font-mono">{selectedDocument.filename}</strong>
            </p>
        </div>
        <ChatPane
          chatHistory={chatHistory}
          onSendMessage={handleSendMessage}
          isLoading={isAnswering}
        />
      </div>
    );
  }

  if (token) {
    return <DashboardPage token={token} onSelectDocument={handleSelectDocument} onLogout={handleLogout} />;
  }

  return <LoginPage onLoginSuccess={handleLoginSuccess} />;
}

export default App;