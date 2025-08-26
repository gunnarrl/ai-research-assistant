import React, { useState } from 'react';
import Header from './Header';
import FileUploadForm from './FileUploadForm';
import ResultsDisplay from './ResultsDisplay';

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [summary, setSummary] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleFileChange = (event) => {
    setSummary("");
    setError("");
    const file = event.target.files[0];
    if (file && file.type === "application/pdf") {
      setSelectedFile(file);
    } else {
      setSelectedFile(null);
      if (file) { // Only show error if a file was actually selected
        setError("Please select a valid PDF file.");
      }
    }
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    if (!selectedFile) {
      setError("Please select a file before summarizing.");
      return;
    }
    // API call logic will be added here in the next task
    console.log("Summarizing file:", selectedFile.name);
    // Example of setting loading state
    // setIsLoading(true); 
  };

  return (
    <div className="bg-slate-50 min-h-screen flex items-center justify-center font-sans p-4">
      <div className="w-full max-w-2xl bg-white rounded-2xl shadow-xl p-6 md:p-8 space-y-6">
        <Header />
        <FileUploadForm
          onFileChange={handleFileChange}
          onSubmit={handleSubmit}
          isLoading={isLoading}
          hasFile={!!selectedFile}
        />
        <ResultsDisplay
          error={error}
          summary={summary}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}

export default App;