// FileUploadForm Component: Handles the file input and submit button.
import React from 'react';

const FileUploadForm = ({ onFileChange, onSubmit, isLoading, hasFile }) => (
  <form onSubmit={onSubmit} className="space-y-4">
    <div>
      <label htmlFor="file-upload" className="sr-only">Choose a file</label>
      <input
        id="file-upload"
        type="file"
        accept=".pdf"
        onChange={onFileChange}
        className="block w-full text-sm text-slate-500
          file:mr-4 file:py-2 file:px-4
          file:rounded-full file:border-0
          file:text-sm file:font-semibold
          file:bg-blue-50 file:text-blue-700
          hover:file:bg-blue-100"
      />
    </div>
    <button
      type="submit"
      disabled={!hasFile || isLoading}
      className="w-full px-5 py-3 bg-blue-600 text-white font-semibold rounded-lg shadow-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-opacity-75 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors duration-300"
    >
      {isLoading ? 'Summarizing...' : 'Summarize'}
    </button>
  </form>
);

export default FileUploadForm;