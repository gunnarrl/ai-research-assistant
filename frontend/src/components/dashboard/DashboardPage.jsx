// frontend/src/components/dashboard/DashboardPage.jsx
import React, { useState, useEffect } from 'react';
import Header from '../Header';
import FileUploadForm from '../files/FileUploadForm';

const BACKEND_URL = "http://127.0.0.1:8000";

const DashboardPage = ({ token, onSelectDocument, onLogout }) => {
  const [documents, setDocuments] = useState([]);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  // For file upload
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);

  const fetchDocuments = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/documents`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error('Failed to fetch documents.');
      const data = await response.json();
      setDocuments(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [token]);

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
    if (!selectedFile) return;
    setIsUploading(true);
    setError('');

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await fetch(`${BACKEND_URL}/upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      });
      if (!response.ok) {
         const errorData = await response.json();
         throw new Error(errorData.detail || 'Upload failed');
      }
      // Re-fetch documents to show the new one
      await fetchDocuments();
      setSelectedFile(null); // Reset file input
      event.target.reset(); // Clear the form
    } catch (err) {
      setError(err.message);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="bg-slate-50 min-h-screen flex items-center justify-center font-sans p-4">
      <div className="w-full max-w-4xl bg-white rounded-2xl shadow-xl p-8 space-y-8">
        <div className="flex justify-between items-center">
          <h2 className="text-3xl font-bold text-gray-900">My Documents</h2>
          <button onClick={onLogout} className="px-4 py-2 bg-gray-200 text-gray-800 font-semibold rounded-lg hover:bg-gray-300">
            Logout
          </button>
        </div>

        {error && <p className="text-red-500">{error}</p>}

        <div>
          <h3 className="text-xl font-bold text-gray-800 mb-4">Upload New Document</h3>
          <FileUploadForm 
            onFileChange={handleFileChange}
            onSubmit={handleFileUpload}
            isLoading={isUploading}
            hasFile={!!selectedFile}
          />
        </div>
        
        <div>
          <h3 className="text-xl font-bold text-gray-800 mb-4">Existing Documents</h3>
          {isLoading ? (
            <p>Loading documents...</p>
          ) : (
            <div className="space-y-3">
              {documents.length > 0 ? (
                documents.map(doc => (
                  <div key={doc.id} onClick={() => onSelectDocument(doc)} className="p-4 bg-gray-50 rounded-lg border border-gray-200 hover:bg-blue-50 hover:border-blue-300 cursor-pointer">
                    <p className="font-semibold text-gray-800">{doc.filename}</p>
                    <p className="text-sm text-gray-500">Uploaded on: {new Date(doc.upload_date).toLocaleDateString()}</p>
                  </div>
                ))
              ) : (
                <p className="text-gray-500">No documents uploaded yet.</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;