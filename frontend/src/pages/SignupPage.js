import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import apiService from '../services/apiService';
// Using App.css for styles

function SignupPage({ onSignupSuccess }) {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (password.length < 6) { // Example basic validation
        setError("Password must be at least 6 characters long.");
        return;
    }
    try {
      await apiService.signup(username, email, password, fullName);
      // Automatically log in the user after successful signup
      const loginData = await apiService.login(username, password);
      onSignupSuccess(loginData.access_token);
      navigate('/chat'); // Redirect to chat page
    } catch (err) {
      setError(err.response?.data?.detail || 'Signup failed. Please try again.');
      console.error("Signup error:", err);
    }
  };

  return (
    <div className="form-container">
      <h2>Sign Up</h2>
      {error && <p className="error-message">{error}</p>}
      <form onSubmit={handleSubmit}>
        <div>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>
        <div>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div>
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <div>
          <input
            type="text"
            placeholder="Full Name (Optional)"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
          />
        </div>
        <button type="submit">Sign Up</button>
      </form>
      <p className="form-link">
        Already have an account? <Link to="/login">Login</Link>
      </p>
    </div>
  );
}

export default SignupPage;
