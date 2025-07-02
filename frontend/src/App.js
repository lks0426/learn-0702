import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom';
import './App.css';
import apiService from './services/apiService';
import ChatPage from './pages/ChatPage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import HistoryPage from './pages/HistoryPage'; // Placeholder for history page

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUser = async () => {
      if (token) {
        try {
          apiService.setAuthToken(token);
          const user = await apiService.getCurrentUser();
          setCurrentUser(user);
        } catch (error) {
          console.error("Failed to fetch user or token invalid:", error);
          localStorage.removeItem('token');
          apiService.setAuthToken(null);
          setToken(null);
          setCurrentUser(null);
        }
      }
      setLoading(false);
    };
    fetchUser();
  }, [token]);

  const handleLogin = (newToken) => {
    localStorage.setItem('token', newToken);
    setToken(newToken);
    // User will be fetched by useEffect
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    apiService.setAuthToken(null);
    setToken(null);
    setCurrentUser(null);
  };

  if (loading) {
    return <div className="loading-container">Loading...</div>;
  }

  return (
    <Router>
      <div className="App">
        <nav className="app-nav">
          <Link to="/">Home</Link>
          {token && <Link to="/chat">Chat</Link>}
          {token && <Link to="/history">History</Link>}
          {token ? (
            <button onClick={handleLogout} className="nav-button logout-button">Logout ({currentUser?.username})</button>
          ) : (
            <>
              <Link to="/login">Login</Link>
              <Link to="/signup">Sign Up</Link>
            </>
          )}
        </nav>

        <Routes>
          <Route path="/" element={
            <div className="home-page">
              <h1>Welcome to the AI Agent</h1>
              {token ? <p>Go to <Link to="/chat">Chat</Link> to start a conversation.</p> : <p>Please <Link to="/login">Login</Link> or <Link to="/signup">Sign Up</Link>.</p>}
            </div>
          } />
          <Route
            path="/login"
            element={!token ? <LoginPage onLogin={handleLogin} /> : <Navigate to="/chat" />}
          />
          <Route
            path="/signup"
            element={!token ? <SignupPage onSignupSuccess={handleLogin} /> : <Navigate to="/chat" />}
          />
          <Route
            path="/chat"
            element={token ? <ChatPage currentUser={currentUser} /> : <Navigate to="/login" />}
          />
          <Route
            path="/chat/:conversationId" // For specific conversations
            element={token ? <ChatPage currentUser={currentUser} /> : <Navigate to="/login" />}
          />
          <Route
            path="/history"
            element={token ? <HistoryPage currentUser={currentUser} /> : <Navigate to="/login" />}
          />
          {/* Add other routes as needed */}
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
