// frontend/src/components/chat/ChatPane.test.jsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import ChatPane from './ChatPane';

// Mock child components to isolate the ChatPane logic
vi.mock('./StructuredDataDisplay', () => ({ default: () => <div>Insights Tab Content</div> }));
vi.mock('./CitationDisplay', () => ({ default: () => <div>Citation Tab Content</div> }));
vi.mock('./BibliographyDisplay', () => ({ default: () => <div>Bibliography Tab Content</div> }));
vi.mock('./ChatWindow', () => ({ default: () => <div>Chat History</div> }));

describe('ChatPane Component', () => {
  const mockDocument = { id: 1, structured_data: { methodology: 'test' } };
  
  it('renders the default insights tab and allows tab switching', async () => {
    const user = userEvent.setup();
    render(<ChatPane document={mockDocument} chatHistory={[]} onSendMessage={() => {}} />);

    // Initially, the Insights tab should be active
    expect(screen.getByText('Insights Tab Content')).toBeInTheDocument();

    // Click on the Citation tab
    await user.click(screen.getByRole('button', { name: 'Citation' }));
    expect(screen.getByText('Citation Tab Content')).toBeInTheDocument();
    expect(screen.queryByText('Insights Tab Content')).not.toBeInTheDocument();
    
    // Click on the Bibliography tab
    await user.click(screen.getByRole('button', { name: 'Bibliography' }));
    expect(screen.getByText('Bibliography Tab Content')).toBeInTheDocument();
    expect(screen.queryByText('Citation Tab Content')).not.toBeInTheDocument();
  });

  it('allows the user to type and send a message', async () => {
    const user = userEvent.setup();
    const handleSendMessage = vi.fn(); // Create a spy function

    render(<ChatPane document={mockDocument} chatHistory={[]} onSendMessage={handleSendMessage} />);

    const input = screen.getByPlaceholderText(/ask a question/i);
    const sendButton = screen.getByRole('button', { name: 'Send' });

    // Simulate typing a question
    await user.type(input, 'What is the methodology?');
    expect(input.value).toBe('What is the methodology?');

    // Click the send button
    await user.click(sendButton);

    // Assert that our spy function was called with the correct text
    expect(handleSendMessage).toHaveBeenCalledOnce();
    expect(handleSendMessage).toHaveBeenCalledWith('What is the methodology?');

    // Assert that the input field was cleared after sending
    expect(input.value).toBe('');
  });
});