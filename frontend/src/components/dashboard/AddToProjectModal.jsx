// frontend/src/components/dashboard/AddToProjectModal.jsx
import React, { useState } from 'react';

const AddToProjectModal = ({ projects, onAddToProject, onCancel }) => {
  const [selectedProjectId, setSelectedProjectId] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (selectedProjectId) {
      onAddToProject(selectedProjectId);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
        <h3 className="text-xl font-bold text-gray-800 mb-4">Add to Project</h3>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <select
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              className="w-full px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
            >
              <option value="" disabled>Select a project</option>
              {projects.map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={onCancel}
                className="px-4 py-2 bg-gray-200 text-gray-800 font-semibold rounded-lg hover:bg-gray-300"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={!selectedProjectId}
                className="px-4 py-2 bg-blue-600 text-white font-semibold rounded-lg shadow-md hover:bg-blue-700 disabled:bg-gray-400"
              >
                Add
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddToProjectModal;