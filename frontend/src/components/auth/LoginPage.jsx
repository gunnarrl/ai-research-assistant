// frontend/src/components/auth/LoginPage.jsx
import React, { useState } from 'react';
import { useGoogleLogin } from '@react-oauth/google';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

const LoginPage = ({ onLoginSuccess }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  
  // State to toggle between Login and Register modes
  const [isLoginMode, setIsLoginMode] = useState(true);

  const handleGoogleLogin = useGoogleLogin({
    flow: 'auth-code',
    onSuccess: async (codeResponse) => {
        try {
            // Send the authorization code to your backend
            const response = await fetch(`${BACKEND_URL}/auth/google`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ code: codeResponse.code }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Google sign-in failed on the server.");
            }

            const data = await response.json();
            onLoginSuccess(data.access_token);

        } catch (err) {
            setError(err.message);
        }
    },
    onError: errorResponse => {
        console.error("Google login failed:", errorResponse);
        setError("Google login failed. Please try again.");
    },
  });


  const handleLogin = async () => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const response = await fetch(`${BACKEND_URL}/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData.toString(),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Login failed');
    }

    const data = await response.json();
    onLoginSuccess(data.access_token);
  };

  const handleRegister = async () => {
    const response = await fetch(`${BACKEND_URL}/users/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Registration failed');
    }

    // After successful registration, automatically log the user in
    await handleLogin();
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    try {
      if (isLoginMode) {
        await handleLogin();
      } else {
        await handleRegister();
      }
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="bg-slate-50 min-h-screen flex items-center justify-center font-sans p-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl p-8 space-y-6">
        {/* ... (h2 title remains the same) ... */}

        {/* Add the Google Login Button */}
        <button
          type="button"
          onClick={() => handleGoogleLogin()}
          className="w-full flex items-center justify-center px-5 py-3 border border-gray-300 rounded-lg shadow-sm bg-white text-gray-700 font-medium hover:bg-gray-50 focus:outline-none"
        >
          <svg className="w-5 h-5 mr-2" viewBox="0 0 48 48">
            <path fill="#4285F4" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l8.35 6.53C12.43 13.72 17.74 9.5 24 9.5z"></path>
            <path fill="#34A853" d="M46.98 24.55c0-1.57-.15-3.09-.42-4.55H24v8.51h12.8c-.57 3.39-2.21 6.28-4.79 8.21l7.34 5.73C44.77 38.21 46.98 31.85 46.98 24.55z"></path>
            <path fill="#FBBC05" d="M10.91 28.74c-.48-1.45-.76-2.99-.76-4.6s.28-3.15.76-4.6L2.56 13.22C.96 16.32 0 19.96 0 24s.96 7.68 2.56 10.78l8.35-6.54z"></path>
            <path fill="#EA4335" d="M24 48c6.48 0 11.93-2.13 15.89-5.82l-7.34-5.73c-2.16 1.45-4.96 2.3-8.55 2.3-6.26 0-11.57-4.22-13.47-9.91l-8.35 6.53C6.51 42.62 14.62 48 24 48z"></path>
            <path fill="none" d="M0 0h48v48H0z"></path>
          </svg>
          Sign in with Google
        </button>

        {/* Separator */}
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-300"></div>
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 bg-white text-gray-500">Or continue with</span>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && <p className="text-red-500 text-sm text-center">{error}</p>}
          <div>
            <label htmlFor="email-address" className="sr-only">Email address</label>
            <input
              id="email-address"
              name="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
              placeholder="Email address"
            />
          </div>
          <div>
            <label htmlFor="password" className="sr-only">Password</label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
              placeholder="Password"
            />
          </div>
          <button
            type="submit"
            className="w-full px-5 py-3 bg-blue-600 text-white font-semibold rounded-lg shadow-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-400"
          >
            {isLoginMode ? 'Sign in' : 'Create Account'}
          </button>
        </form>
        <p className="text-center text-sm text-gray-600">
          {isLoginMode ? "Don't have an account? " : "Already have an account? "}
          <button
            type="button"
            onClick={() => {
              setIsLoginMode(!isLoginMode);
              setError(''); // Clear errors when switching modes
            }}
            className="font-medium text-blue-600 hover:text-blue-500 focus:outline-none"
          >
            {isLoginMode ? 'Sign Up' : 'Sign In'}
          </button>
        </p>
      </div>
    </div>
  );
};

export default LoginPage;