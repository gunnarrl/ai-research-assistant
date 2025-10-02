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
    // This function will now fetch the PDF content
    setSelectedDocument(doc);
    setChatHistory([{ sender: 'ai', text: `Selected "${doc.filename}". Ask me anything!` }]);
    setPdfUrl(null); // Clear previous PDF

    try {
        const response = await fetch(`${BACKEND_URL}/documents/${doc.id}/file`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.status === 401) {
            handleLogout();
            return;
        }

        if (!response.ok) {
            throw new Error("Could not fetch PDF file.");
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        setPdfUrl(url);

    } catch (err) {
        console.error("Failed to load PDF:", err);
        // Optionally set an error state to show in the UI
    }
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
        {/* Replace the simplified view with the actual PdfViewer component */}
        <div className="flex-1">
          <PdfViewer pdfUrl={pdfUrl} />
        </div>
        
        <ChatPane
          chatHistory={chatHistory}
          onSendMessage={handleSendMessage}
          isLoading={isAnswering}
          onReturnToDashboard={handleReturnToDashboard}
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