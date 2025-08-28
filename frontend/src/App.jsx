// frontend/src/App.jsx
import React, { useState } from 'react';
import Header from './components/Header.jsx';
import FileUploadForm from './components/files/FileUploadForm.jsx';
import PdfViewer from './components/files/PdfViewer.jsx';
import ChatPane from './components/chat/ChatPane.jsx';

const BACKEND_URL = "http://127.0.0.1:8000";

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [pdfUrl, setPdfUrl] = useState(null);
  const [documentId, setDocumentId] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isAnswering, setIsAnswering] = useState(false);
  const [error, setError] = useState("");

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file && file.type === "application/pdf") {
      setSelectedFile(file);
      setError("");
    } else {
      setSelectedFile(null);
      if (file) setError("Please select a valid PDF file.");
    }
  };

  // --- REAL API CALLS ---

  const handleFileUpload = async (event) => {
    event.preventDefault();
    if (!selectedFile) {
      setError("Please select a file before uploading.");
      return;
    }

    setIsUploading(true);
    setError("");

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await fetch(`${BACKEND_URL}/upload`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || `HTTP error! Status: ${response.status}`);
      }

      const result = await response.json();
      setDocumentId(result.document_id);

      const fileUrl = URL.createObjectURL(selectedFile);
      setPdfUrl(fileUrl);
      
      setChatHistory([{ sender: 'ai', text: `File "${selectedFile.name}" is ready. Ask me anything!` }]);

    } catch (err) {
      setError(err.message);
      setPdfUrl(null); // Clear viewer on error
    } finally {
      setIsUploading(false);
    }
  };

  const handleSendMessage = async (question) => {
    if (!documentId) {
      setError("An active document is required to chat.");
      return;
    }

    // a. Add user's message to history immediately
    const newUserMessage = { sender: 'user', text: question };
    setChatHistory(prev => [...prev, newUserMessage]);
    setIsAnswering(true);

    try {
      // b. Make a fetch call to the POST /chat endpoint
      const response = await fetch(`${BACKEND_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          document_id: documentId,
          question: question,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || `HTTP error! Status: ${response.status}`);
      }

      const result = await response.json();
      
      // d. Add the AI's message to the chat history
      const aiResponse = { sender: 'ai', text: result.answer };
      setChatHistory(prev => [...prev, aiResponse]);

    } catch (err) {
      const errorResponse = { sender: 'ai', text: `Sorry, an error occurred: ${err.message}` };
      setChatHistory(prev => [...prev, errorResponse]);
    } finally {
      // c. Reset loading indicator
      setIsAnswering(false);
    }
  };

  // The main view once a file has been processed
  if (documentId) {
    return (
      <div className="flex w-screen h-screen font-sans">
        <PdfViewer pdfUrl={pdfUrl} />
        <ChatPane
          chatHistory={chatHistory}
          onSendMessage={handleSendMessage}
          isLoading={isAnswering}
        />
      </div>
    );
  }

  // The initial upload view
  return (
    <div className="bg-slate-50 min-h-screen flex items-center justify-center font-sans p-4">
      <div className="w-full max-w-2xl bg-white rounded-2xl shadow-xl p-6 md:p-8 space-y-6">
        <Header />
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg" role="alert">
            <span className="block sm:inline">{error}</span>
          </div>
        )}
        <FileUploadForm
          onFileChange={handleFileChange}
          onSubmit={handleFileUpload}
          isLoading={isUploading}
          hasFile={!!selectedFile}
        />
      </div>
    </div>
  );
}

export default App;