// frontend/src/App.jsx
import React, { useState } from 'react';
import Header from './components/Header.jsx';
import FileUploadForm from './components/files/FileUploadForm.jsx';
import PdfViewer from './components/files/PdfViewer.jsx';
import ChatPane from './components/chat/ChatPane.jsx';

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

  const handleFileUpload = async (event) => {
    event.preventDefault();
    if (!selectedFile) {
      setError("Please select a file first.");
      return;
    }
    setIsUploading(true);
    setError("");

    // Create a URL for the PDF viewer
    const fileUrl = URL.createObjectURL(selectedFile);
    setPdfUrl(fileUrl);
    
    // Simulate a successful upload for now
    setTimeout(() => {
      const mockDocumentId = 1;
      setDocumentId(mockDocumentId);
      setChatHistory([{ sender: 'ai', text: `File ready. Ask me anything about ${selectedFile.name}.` }]);
      setIsUploading(false);
    }, 1000);
  };

  const handleSendMessage = (question) => {
    const newUserMessage = { sender: 'user', text: question };
    const mockAiResponse = { sender: 'ai', text: 'This is a placeholder AI response.' };
    setChatHistory(prev => [...prev, newUserMessage, mockAiResponse]);
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