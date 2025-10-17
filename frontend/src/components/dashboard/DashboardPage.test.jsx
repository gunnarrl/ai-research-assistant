// frontend/src/components/dashboard/DashboardPage.test.jsx
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import DashboardPage from './DashboardPage';

// Mock child components that are not the focus of this test
vi.mock('./ArxivSearch', () => ({ default: () => <div>ArxivSearch Mock</div> }));
vi.mock('./ProjectsDashboard', () => ({ default: () => <div>ProjectsDashboard Mock</div> }));
vi.mock('./AgentDashboard', () => ({ default: () => <div>AgentDashboard Mock</div> }));

const mockDocuments = [
  { id: 1, filename: 'document1.pdf', upload_date: new Date().toISOString(), status: 'COMPLETED' },
  { id: 2, filename: 'document2.pdf', upload_date: new Date().toISOString(), status: 'PROCESSING' },
];

describe('DashboardPage Component', () => {
  beforeEach(() => {
    // Mock the global fetch function before each test
    globalThis.fetch = vi.fn((url) => {
      let data;
      if (url.endsWith('/documents')) {
        data = mockDocuments;
      } else if (url.endsWith('/projects')) {
        data = [];
      } else if (url.endsWith('/agent/literature-reviews')) {
        data = [];
      } else {
        data = {};
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(data),
      });
    });
  });

  it('shows a loading state and then renders documents', async () => {
    render(<DashboardPage token="fake-token" />);

    // Check for the initial loading state
    expect(screen.getByText('Loading documents...')).toBeInTheDocument();

    // Wait for the component to re-render after fetching data
    await waitFor(() => {
      expect(screen.getByText('document1.pdf')).toBeInTheDocument();
    });

    // Check that both completed and processing documents are rendered
    expect(screen.getByText('document2.pdf')).toBeInTheDocument();
    expect(screen.getByText('Processing...')).toBeInTheDocument();
    
  });
});