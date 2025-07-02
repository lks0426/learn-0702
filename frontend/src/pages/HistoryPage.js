import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import apiService from '../services/apiService';
// Styles in App.css

function HistoryPage({ currentUser }) {
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchConversations = async () => {
      if (!currentUser) return;
      setLoading(true);
      try {
        const convs = await apiService.getConversations();
        setConversations(convs.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)));
      } catch (err) {
        console.error("Failed to fetch conversation history:", err);
        setError("Could not load conversation history.");
      } finally {
        setLoading(false);
      }
    };

    fetchConversations();
  }, [currentUser]);

  if (loading) {
    return <div className="loading-container">Loading history...</div>;
  }

  if (error) {
    return <div className="error-message" style={{textAlign: 'center', marginTop: '20px'}}>{error}</div>;
  }

  return (
    <div className="history-page">
      <h2>Conversation History</h2>
      {conversations.length === 0 ? (
        <p>No conversations yet. <Link to="/chat">Start a new chat!</Link></p>
      ) : (
        <ul className="history-list">
          {conversations.map(conv => (
            <li key={conv.id} className="history-item">
              <h3>
                <Link to={`/chat/${conv.id}`}>
                  {conv.title || `Conversation from ${new Date(conv.created_at).toLocaleDateString()}`}
                </Link>
              </h3>
              <p>Created on: {new Date(conv.created_at).toLocaleString()}</p>
              {/* Could show a snippet of the last message if available */}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default HistoryPage;
