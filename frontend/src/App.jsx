// frontend/src/App.jsx
import React, { useState, useEffect } from 'react';
import PdfViewer from './components/files/PdfViewer';
import ChatPane from './components/chat/ChatPane';
import LoginPage from './components/auth/LoginPage';
import DashboardPage from './components/dashboard/DashboardPage';
import ProjectViewPage from './components/dashboard/ProjectViewPage';
import MultiDocList from './components/chat/MultiDocList';
import LiteratureReviewViewPage from './components/dashboard/LiteratureReviewViewPage';


const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;
const TOKEN_KEY = 'authToken';

function App() {
  const [token, setToken] = useState(localStorage.getItem(TOKEN_KEY));
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [isAnswering, setIsAnswering] = useState(false);
  const [pdfUrl, setPdfUrl] = useState(null);
  const [selectedLitReview, setSelectedLitReview] = useState(null);


  // --- NEW AND UPDATED STATE FOR MULTI-CHAT ---
  const [multiChatDocs, setMultiChatDocs] = useState([]); // Will store full document objects
  const [currentMultiViewDocId, setCurrentMultiViewDocId] = useState(null); // Tracks which PDF to show

  const [citations, setCitations] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);

  // --- REFACTORED PDF FETCHING LOGIC ---
  const fetchAndDisplayPdf = async (docId) => {
    if (!token) return;
    setPdfUrl(null); // Clear previous PDF while loading new one

    try {
      const response = await fetch(`${BACKEND_URL}/documents/${docId}/file`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error("Could not fetch PDF file.");
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      setPdfUrl(url);
    } catch (err) {
      console.error("Failed to load PDF:", err);
    }
  };

  // --- EFFECT TO FETCH PDF WHEN VIEW SELECTION CHANGES ---
  useEffect(() => {
    if (currentMultiViewDocId) {
      fetchAndDisplayPdf(currentMultiViewDocId);
    }
  }, [currentMultiViewDocId, token]);


  const handleLoginSuccess = (newToken) => {
    localStorage.setItem(TOKEN_KEY, newToken);
    setToken(newToken);
  };

   const handleLogout = () => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setSelectedDocument(null);
    setMultiChatDocs([]);
    setCitations([]); // <-- Clear citations on logout
  };

  const handleSelectDocument = async (doc) => {
    setSelectedDocument(doc);
    setChatHistory([{ sender: 'ai', text: `Selected "${doc.filename}". Ask me anything!` }]);
    fetchAndDisplayPdf(doc.id);
    
    // --- NEW: FETCH CITATIONS ---
    setCitations([]); // Clear previous citations
    try {
      const response = await fetch(`${BACKEND_URL}/documents/${doc.id}/citations`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error("Could not fetch citations.");
      const data = await response.json();
      setCitations(data);
    } catch (err) {
      console.error("Failed to load citations:", err);
    }
  };

  const handleSelectProject = (project) => {
    setSelectedProject(project);
  };

  const handleSelectLitReview = (review) => {
    setSelectedLitReview(review);
  };

  // --- UPDATED MULTI-CHAT HANDLERS ---
  const handleStartMultiChat = (docs) => {
    setMultiChatDocs(docs);
    setSelectedDocument(null); 
    setChatHistory([{ sender: 'ai', text: `Chatting with ${docs.length} documents. Ask me anything!` }]);
    // Select the first doc in the list to view by default
    if (docs.length > 0) {
      setCurrentMultiViewDocId(docs[0].id);
    }
  };
  
  const handleSelectMultiViewDoc = (docId) => {
    setCurrentMultiViewDocId(docId);
  };

  const handleReturnToDashboard = () => {
    setSelectedDocument(null);
    setMultiChatDocs([]);
    setCurrentMultiViewDocId(null);
    setSelectedProject(null);
    setSelectedLitReview(null);
    setChatHistory([]);
    setCitations([]);
    if (pdfUrl) {
      URL.revokeObjectURL(pdfUrl);
      setPdfUrl(null);
    }
  };

  // --- UPDATED handleSendMessage TO USE THE NEW STATE ---
  const handleSendMessage = async (question) => {
    const isMultiChat = multiChatDocs.length > 0;
    if (!selectedDocument && !isMultiChat) return;

    const newUserMessage = { sender: 'user', text: question };
    const aiPlaceholder = { sender: 'ai', text: '' };
    setChatHistory(prev => [...prev, newUserMessage, aiPlaceholder]);
    setIsAnswering(true);

    const endpoint = isMultiChat ? `${BACKEND_URL}/chat/multi` : `${BACKEND_URL}/chat`;
    const body = isMultiChat 
      ? JSON.stringify({ document_ids: multiChatDocs.map(d => d.id), question: question })
      : JSON.stringify({ document_id: selectedDocument.id, question: question });

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: body,
      });

      if (!response.ok || !response.body) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || `HTTP error! Status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
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

  if (selectedLitReview) {
    return <LiteratureReviewViewPage
              review={selectedLitReview}
              token={token}
              onReturnToDashboard={handleReturnToDashboard}
            />
  }

  // --- UPDATED RENDER LOGIC ---
  if (selectedDocument) {
    // Single-doc view remains a two-panel layout
    return (
      <div className="flex w-screen h-screen font-sans">
        <div className="flex-1">
          <PdfViewer pdfUrl={pdfUrl} />
        </div>
        <ChatPane
          document={selectedDocument}
          chatHistory={chatHistory}
          onSendMessage={handleSendMessage}
          isLoading={isAnswering}
          onReturnToDashboard={handleReturnToDashboard}
          citations={citations} // <-- Pass citations
          token={token}         // <-- Pass token
        />
      </div>
    );
  }

  if (multiChatDocs.length > 0) {
    // Find the full document object that is currently being viewed in the PDF panel
    const currentViewedDoc = multiChatDocs.find(doc => doc.id === currentMultiViewDocId) || { structured_data: null };

    // Multi-doc view is now a three-panel layout
    return (
      <div className="flex w-screen h-screen font-sans">
        <div className="w-64 bg-gray-100 border-r border-gray-200 p-2">
          <MultiDocList 
            documents={multiChatDocs}
            currentDocId={currentMultiViewDocId}
            onSelect={handleSelectMultiViewDoc}
          />
        </div>
        <div className="flex-1">
          <PdfViewer pdfUrl={pdfUrl} />
        </div>
        <ChatPane
          document={currentViewedDoc}
          chatHistory={chatHistory}
          onSendMessage={handleSendMessage}
          isLoading={isAnswering}
          onReturnToDashboard={handleReturnToDashboard}
          citations={citations}
          token={token}
        />
      </div>
    );
  }

  if (selectedProject) {
    return <ProjectViewPage 
              project={selectedProject}
              token={token}
              onReturnToDashboard={handleReturnToDashboard}
              onSelectDocument={handleSelectDocument}
            />
  }

  if (token) {
    return <DashboardPage 
              token={token} 
              onSelectDocument={handleSelectDocument} 
              onLogout={handleLogout}
              onStartMultiChat={handleStartMultiChat}
              onSelectProject={handleSelectProject} // <-- Pass down the handler
              onSelectLitReview={handleSelectLitReview}
            />;
  }

  return <LoginPage onLoginSuccess={handleLoginSuccess} />;
}

export default App;