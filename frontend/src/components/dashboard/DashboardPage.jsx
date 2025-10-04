// frontend/src/components/dashboard/DashboardPage.jsx
import React, { useState, useEffect } from 'react';
import Header from '../Header'; 
import FileUploadForm from '../files/FileUploadForm';
import ArXivSearch from './ArXivSearch';
import ProjectsDashboard from './ProjectsDashboard';
import AddToProjectModal from './AddToProjectModal';
import AgentDashboard from './AgentDashboard';

const BACKEND_URL = "http://127.0.0.1:8000";

const DashboardPage = ({ token, onSelectDocument, onLogout, onStartMultiChat, onSelectProject }) => {
  const [documents, setDocuments] = useState([]);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [projects, setProjects] = useState([]);

  // For file upload
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);

  // For multi-select
  const [selectedDocs, setSelectedDocs] = useState([]);

  // --- State for the "Add to Project" modal ---
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [docToAdd, setDocToAdd] = useState(null);

  // This function needs to be defined inside the component or passed as a prop
  const fetchDocuments = async () => {
    setError('');
    try {
      const response = await fetch(`${BACKEND_URL}/documents`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.status === 401) {
        onLogout();
        return;
      }
      if (!response.ok) throw new Error('Failed to fetch documents.');

      const data = await response.json();
      // Ensure data is an array before setting state to prevent render errors
      if (Array.isArray(data)) {
        setDocuments(data);
      } else {
        setDocuments([]); // Default to empty array if response is not as expected
      }

    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchProjects = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/projects`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.status === 401) onLogout();
      if (!response.ok) throw new Error('Failed to fetch projects.');
      const data = await response.json();
      setProjects(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    setIsLoading(true);
    Promise.all([fetchDocuments(), fetchProjects()]).finally(() => setIsLoading(false));
  }, [token]);

  useEffect(() => {
    const hasProcessingDocuments = documents.some(doc => doc.status === 'PROCESSING');
    
    if (hasProcessingDocuments) {
      const intervalId = setInterval(() => {
        fetchDocuments();
      }, 3000); 

      return () => clearInterval(intervalId);
    }
  }, [documents]);

  const handleOpenAddToProjectModal = (doc) => {
    setDocToAdd(doc);
    setIsModalOpen(true);
  };

  const handleAddToProject = async (projectId) => {
    if (!docToAdd) return;
    try {
      const response = await fetch(`${BACKEND_URL}/projects/${projectId}/documents`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ document_id: docToAdd.id })
      });
      if (!response.ok) throw new Error("Failed to add document to project.");
      // You could add a success message here
    } catch (err) {
      setError(err.message);
    } finally {
      setIsModalOpen(false);
      setDocToAdd(null);
    }
  };


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

  const handleDeleteDocument = async (docId) => {
    // Confirm with the user before deleting
    if (!window.confirm("Are you sure you want to permanently delete this document?")) {
      return;
    }

    setError('');
    try {
      const response = await fetch(`${BACKEND_URL}/documents/${docId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.status === 401) {
        onLogout();
        return;
      }
      if (!response.ok) {
        throw new Error('Failed to delete document.');
      }

      // If successful, remove the document from the local state for an immediate UI update
      setDocuments(prevDocs => prevDocs.filter(doc => doc.id !== docId));
      
    } catch (err) {
      setError(err.message);
    }
  };

  const handleCheckboxChange = (docId) => {
    setSelectedDocs(prevSelected => {
      if (prevSelected.includes(docId)) {
        // If it's already selected, remove it
        return prevSelected.filter(id => id !== docId);
      } else {
        // If it's not selected, add it
        return [...prevSelected, docId];
      }
    });
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
      
      if (response.status === 401) {
        onLogout();
        return;
      }

      if (!response.ok) {
         const errorData = await response.json();
         throw new Error(errorData.detail || 'Upload failed');
      }

      await fetchDocuments();
      setSelectedFile(null);
      event.target.reset();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="bg-slate-50 min-h-screen flex items-center justify-center font-sans p-4">
      {isModalOpen && (
        <AddToProjectModal
          projects={projects}
          onAddToProject={handleAddToProject}
          onCancel={() => setIsModalOpen(false)}
        />
      )}
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

        <div className="border-t border-gray-200 my-8"></div>

          <div>
            <ArXivSearch token={token} onImportSuccess={fetchDocuments} />
          </div>

        <div className="border-t border-gray-200 my-8"></div>

          <div>
            <AgentDashboard token={token} />
          </div>
        
        <div className="border-t border-gray-200 my-8"></div>
          <div>
            <ProjectsDashboard 
              projects={projects}
              token={token}
              onProjectCreated={fetchProjects}
              onSelectProject={onSelectProject}
            />
          </div>

        <div className="border-t border-gray-200 my-8"></div>

        <div>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-bold text-gray-800">Existing Documents</h3>
            {selectedDocs.length > 0 && (
              <button
                onClick={() => {
                  const docsToChat = documents.filter(doc => selectedDocs.includes(doc.id));
                  onStartMultiChat(docsToChat);
                }} 
                 className="px-4 py-2 bg-green-600 text-white font-semibold rounded-lg shadow-md hover:bg-green-700"
               >
                 {`Chat with Selected (${selectedDocs.length})`}
              </button>
            )}
          </div>
          {isLoading ? (
            <p>Loading documents...</p>
          ) : (
            <div className="space-y-3">
              {documents.length > 0 ? (
                documents.map(doc => {
                  const isProcessing = doc.status === 'PROCESSING';
                  const isFailed = doc.status === 'FAILED';
                  const isClickable = !isProcessing && !isFailed;

                  return (
                    <div
                      key={doc.id}
                      className={`p-4 rounded-lg border flex justify-between items-center ${
                        isClickable
                          ? 'bg-gray-50 border-gray-200'
                          : 'bg-gray-100 border-gray-200 cursor-not-allowed opacity-60'
                      }`}
                    >
                      <div className="flex items-center space-x-4">
                        <input
                          type="checkbox"
                          className="h-5 w-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          disabled={!isClickable}
                          checked={selectedDocs.includes(doc.id)}
                          onChange={() => handleCheckboxChange(doc.id)}
                        />
                        <div 
                          onClick={isClickable ? () => onSelectDocument(doc) : undefined}
                          className={isClickable ? 'cursor-pointer' : ''}
                        >
                          <p className={`font-semibold ${isClickable ? 'text-gray-800' : 'text-gray-500'}`}>{doc.filename}</p>
                          <p className="text-sm text-gray-500">Uploaded on: {new Date(doc.upload_date).toLocaleDateString()}</p>
                        </div>
                      </div>

                      <div className="flex items-center space-x-4">
                        {isProcessing && (
                          <div className="flex items-center space-x-2">
                            <span className="text-sm text-gray-500">Processing...</span>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                          </div>
                        )}
                        {isFailed && (
                          <span className="text-sm text-red-500 font-semibold">Processing Failed</span>
                        )}
                        
                        <button
                          onClick={() => handleOpenAddToProjectModal(doc)}
                          className="text-gray-400 hover:text-blue-600 focus:outline-none"
                          title="Add to project"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
                            <path stroke="#fff" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 11v4m-2-2h4" />
                          </svg>
                        </button>

                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteDocument(doc.id);
                          }}
                          className="text-gray-400 hover:text-red-600 focus:outline-none"
                          title="Delete document"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  );
                })
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