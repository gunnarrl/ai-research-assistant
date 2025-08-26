import React, { useState } from 'react';

// Assuming these components are in a 'components' subdirectory
import Header from './components/Header.jsx';
import FileUploadForm from './components/FileUploadForm.jsx';
import ResultsDisplay from './components/ResultsDisplay.jsx';

// --- Main App Component ---

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

  // This is the new async function to handle the API call
  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!selectedFile) {
      setError("Please select a file before summarizing.");
      return;
    }

    setIsLoading(true);
    setError("");
    setSummary("");

    // Create a FormData object to send the file
    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await fetch("https://ai-assistant-backend-972171596347.us-central1.run.app/summarize", {
        method: "POST",
        body: formData,
        // Note: Do not set 'Content-Type' header when using FormData,
        // the browser will automatically set it with the correct boundary.
      });

      if (!response.ok) {
        // Try to parse error message from backend, otherwise use default
        const errorData = await response.json().catch(() => null);
        const errorMessage = errorData?.detail || `An error occurred: ${response.statusText}`;
        throw new Error(errorMessage);
      }

      const result = await response.json();
      setSummary(result.summary);

    } catch (err) {
      // Handle network errors or errors thrown from the response check
      setError(err.message);
    } finally {
      // Ensure loading is turned off whether the request succeeds or fails
      setIsLoading(false);
    }
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
