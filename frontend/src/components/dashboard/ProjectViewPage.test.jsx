// frontend/src/components/dashboard/ProjectViewPage.test.jsx
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ProjectViewPage from './ProjectViewPage';

const mockProjectDetails = {
  id: 1,
  name: 'Test Project',
  members: [
    { id: 1, email: 'user1@test.com' },
    { id: 2, email: 'user2@test.com' },
  ],
  documents: [
    { id: 101, filename: 'shared_doc1.pdf' },
  ],
};

describe('ProjectViewPage Component', () => {
  beforeEach(() => {
    // Mock the global fetch function
    globalThis.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockProjectDetails),
      })
    );
  });

  it('shows a loading state and then renders project details', async () => {
    render(<ProjectViewPage project={{ id: 1, name: 'Test Project' }} token="fake-token" />);

    // Check for the initial loading state
    expect(screen.getByText('Loading project...')).toBeInTheDocument();

    // Wait for the component to re-render after fetching data
    await waitFor(() => {
      // Check for project name (might appear twice, once in the h2)
      expect(screen.getAllByText('Test Project')[0]).toBeInTheDocument();
    });

    // Verify members and documents are rendered
    expect(screen.getByText('user1@test.com')).toBeInTheDocument();
    expect(screen.getByText('user2@test.com')).toBeInTheDocument();
    expect(screen.getByText('shared_doc1.pdf')).toBeInTheDocument();
  });
});