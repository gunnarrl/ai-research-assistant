// frontend/src/components/dashboard/ProjectViewPage.jsx
import React, { useState, useEffect, useCallback } from 'react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

const ProjectViewPage = ({ project, token, onReturnToDashboard, onSelectDocument }) => {
  const [projectDetails, setProjectDetails] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [newMemberEmail, setNewMemberEmail] = useState('');

  const fetchProjectDetails = useCallback(async () => {
    setIsLoading(true);
    setError('');
    try {
      const response = await fetch(`${BACKEND_URL}/projects/${project.id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error("Failed to fetch project details.");
      const data = await response.json();
      setProjectDetails(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [project.id, token]);

  useEffect(() => {
    fetchProjectDetails();
  }, [project.id, token, fetchProjectDetails]);

  const handleAddMember = async (e) => {
    e.preventDefault();
    if (!newMemberEmail.trim()) return;
    setError('');
    try {
      const response = await fetch(`${BACKEND_URL}/projects/${project.id}/members`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ email: newMemberEmail })
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Failed to add member.");
      }
      setNewMemberEmail('');
      await fetchProjectDetails(); // Refresh details
    } catch (err) {
      setError(err.message);
    }
  };

  if (isLoading) return <p>Loading project...</p>;

  return (
    <div className="bg-slate-50 min-h-screen flex items-center justify-center font-sans p-4">
      <div className="w-full max-w-4xl bg-white rounded-2xl shadow-xl p-8 space-y-8">
        <div className="flex justify-between items-center">
          <div>
            <button onClick={onReturnToDashboard} className="text-sm text-blue-600 hover:underline mb-2">
              &larr; Back to Dashboard
            </button>
            <h2 className="text-3xl font-bold text-gray-900">{projectDetails?.name}</h2>
          </div>
        </div>

        {error && <p className="text-red-500 my-4">{error}</p>}

        {/* Members Section */}
        <div>
          <h3 className="text-xl font-bold text-gray-800 mb-4">Members</h3>
          <form onSubmit={handleAddMember} className="flex items-center space-x-2 mb-4">
            <input
              type="email"
              value={newMemberEmail}
              onChange={(e) => setNewMemberEmail(e.target.value)}
              placeholder="Invite user by email..."
              className="flex-grow px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg focus:outline-none"
            />
            <button type="submit" className="px-4 py-2 bg-blue-600 text-white font-semibold rounded-lg">
              Add Member
            </button>
          </form>
          <div className="space-y-2">
            {projectDetails?.members.map(member => (
              <div key={member.id} className="p-3 bg-gray-50 rounded-md text-sm">{member.email}</div>
            ))}
          </div>
        </div>

        <div className="border-t border-gray-200"></div>

        {/* Documents Section */}
        <div>
          <h3 className="text-xl font-bold text-gray-800 mb-4">Documents in this Project</h3>
          <div className="space-y-3">
            {projectDetails?.documents.length > 0 ? (
              projectDetails.documents.map(doc => (
                <div 
                  key={doc.id}
                  onClick={() => onSelectDocument(doc)}
                  className="p-4 rounded-lg border bg-gray-50 border-gray-200 cursor-pointer hover:bg-gray-100"
                >
                  <p className="font-semibold text-gray-800">{doc.filename}</p>
                </div>
              ))
            ) : (
              <p className="text-gray-500">No documents have been added to this project yet.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProjectViewPage;