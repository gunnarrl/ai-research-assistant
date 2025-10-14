// frontend/src/components/dashboard/ProjectsDashboard.jsx
import React, { useState } from 'react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

const ProjectsDashboard = ({ projects, token, onProjectCreated, onSelectProject }) => {
  const [newProjectName, setNewProjectName] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState('');

  const handleCreateProject = async (e) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;

    setIsCreating(true);
    setError('');

    try {
      const response = await fetch(`${BACKEND_URL}/projects`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ name: newProjectName })
      });
      if (!response.ok) {
        throw new Error('Failed to create project.');
      }
      // Notify parent to refetch the projects list
      onProjectCreated();
      setNewProjectName('');
    } catch (err) {
      setError(err.message);
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div>
      <h3 className="text-xl font-bold text-gray-800 mb-4">My Projects</h3>
      {error && <p className="text-red-500 mb-4">{error}</p>}
      
      {/* Create Project Form */}
      <form onSubmit={handleCreateProject} className="flex items-center space-x-2 mb-6">
        <input
          type="text"
          value={newProjectName}
          onChange={(e) => setNewProjectName(e.target.value)}
          placeholder="New project name..."
          className="flex-grow px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
        />
        <button
          type="submit"
          disabled={isCreating || !newProjectName.trim()}
          className="px-5 py-2 bg-green-600 text-white font-semibold rounded-lg shadow-md hover:bg-green-700 disabled:bg-gray-400"
        >
          {isCreating ? 'Creating...' : 'Create Project'}
        </button>
      </form>

      {/* Projects List */}
      <div className="space-y-3">
        {projects.length > 0 ? (
          projects.map(project => (
            <div 
              key={project.id} 
              // Add onClick handler here
              onClick={() => onSelectProject(project)}
              className="p-4 rounded-lg border bg-gray-50 border-gray-200 cursor-pointer hover:bg-gray-100"
            >
              <p className="font-semibold text-gray-800">{project.name}</p>
            </div>
          ))
        ) : (
          <p className="text-gray-500">You are not a member of any projects yet.</p>
        )}
      </div>
    </div>
  );
};

export default ProjectsDashboard;