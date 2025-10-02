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

  const handleReturnToDashboard = () => {
    setSelectedDocument(null);
    setChatHistory([]); // Clear chat history when going back
  };

   const handleSendMessage = async (question) => {
    if (!selectedDocument) return;

    // 1. Add user's message and a placeholder for the AI's response
    const newUserMessage = { sender: 'user', text: question };
    const aiPlaceholder = { sender: 'ai', text: '' };
    setChatHistory(prev => [...prev, newUserMessage, aiPlaceholder]);
    setIsAnswering(true);

    try {
      const response = await fetch(`${BACKEND_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          document_id: selectedDocument.id,
          question: question,
        }),
      });

      if (!response.ok || !response.body) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || `HTTP error! Status: ${response.status}`);
      }

      // 2. Process the streaming response
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          break;
        }
        const chunk = decoder.decode(value, { stream: true });
        
        // 3. Append the incoming chunk to the last AI message in the history
        setChatHistory(prev => {
          const lastMessage = prev[prev.length - 1];
          if (lastMessage && lastMessage.sender === 'ai') {
            const updatedLastMessage = { ...lastMessage, text: lastMessage.text + chunk };
            return [...prev.slice(0, -1), updatedLastMessage];
          }
          return prev;
        });
      }

    } catch (err) {
      // If an error occurs, update the placeholder with the error message
      setChatHistory(prev => {
        const lastMessage = prev[prev.length - 1];
        if (lastMessage && lastMessage.sender === 'ai') {
          const updatedLastMessage = { ...lastMessage, text: `Sorry, an error occurred: ${err.message}` };
          return [...prev.slice(0, -1), updatedLastMessage];
        }
        return prev;
      });
    } finally {
      setIsAnswering(false);
    }
  };



  // --- Conditional Rendering Logic ---

  if (selectedDocument) {
    return (
      <div className="flex w-screen h-screen font-sans">
        <div className="w-2/3 h-full border-r border-gray-200">
          <PdfViewer pdfUrl={pdfUrl} />
        </div>
          {/* ... (left side of the chat view) ... */}
        <ChatPane
          chatHistory={chatHistory}
          onSendMessage={handleSendMessage}
          isLoading={isAnswering}
          onReturnToDashboard={handleReturnToDashboard} // Pass the new function as a prop
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