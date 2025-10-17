// frontend/src/components/auth/LoginPage.test.jsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import LoginPage from './LoginPage';

// Mock the GoogleLogin component as it's not relevant to this unit test
vi.mock('@react-oauth/google', () => ({
  useGoogleLogin: () => vi.fn(),
}));

describe('LoginPage Component', () => {
  it('allows a user to fill out the form and attempt to log in', async () => {
    const user = userEvent.setup();
    const handleLoginSuccess = vi.fn(); // A "spy" function to track calls

    // 1. Render the component with the mock function
    render(<LoginPage onLoginSuccess={handleLoginSuccess} />);

    // 2. Find the input fields and button
    const emailInput = screen.getByPlaceholderText('Email address');
    const passwordInput = screen.getByPlaceholderText('Password');
    // Use an exact match for the name to avoid matching "Sign in with Google"
    const signInButton = screen.getByRole('button', { name: 'Sign in' });

    // 3. Simulate user typing into the fields
    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password123');

    // 4. Assert that the values were entered correctly
    expect(emailInput.value).toBe('test@example.com');
    expect(passwordInput.value).toBe('password123');

    // 5. Simulate user clicking the sign-in button
    await user.click(signInButton);
  });

  it('toggles between login and register modes', async () => {
    const user = userEvent.setup();
    render(<LoginPage onLoginSuccess={() => {}} />);

    // Initially, find the main sign-in button specifically and exactly.
    expect(screen.getByRole('button', { name: 'Sign in' })).toBeInTheDocument();
    
    // Find and click the "Sign Up" button
    const signUpToggle = screen.getByRole('button', { name: /sign up/i });
    await user.click(signUpToggle);

    // Now, the main button should say "Create Account"
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument();
  });
});