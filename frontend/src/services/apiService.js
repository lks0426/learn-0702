import axios from 'axios';

// Determine the base URL for the API
// In development, React app runs on 3000, backend on 8000.
// We'll use a proxy in package.json for local dev, or configure Nginx for production.
// For direct calls from client (e.g. if not using proxy or if services are on different domains without Nginx)
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || '/api/v1/backend'; // Use Nginx gateway

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Function to set the auth token for subsequent requests
const setAuthToken = (token) => {
  if (token) {
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete apiClient.defaults.headers.common['Authorization'];
  }
};

// --- Auth Services ---
const login = async (username, password) => {
  // FastAPI's OAuth2PasswordRequestForm expects form data
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  const response = await apiClient.post('/token', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
  return response.data; // { access_token, token_type }
};

const signup = async (username, email, password, fullName = '') => {
  const response = await apiClient.post('/users/', {
    username,
    email,
    password,
    full_name: fullName,
  });
  return response.data; // User data
};

const getCurrentUser = async () => {
  const response = await apiClient.get('/users/me/');
  return response.data; // User data
};

// --- Conversation Services ---
const createConversation = async (title = '') => {
  const response = await apiClient.post('/conversations/', { title });
  return response.data; // Conversation data
};

const getConversations = async () => {
  const response = await apiClient.get('/conversations/');
  return response.data; // List of conversations
};

const getConversationDetails = async (conversationId) => {
  const response = await apiClient.get(`/conversations/${conversationId}`);
  return response.data; // Detailed conversation data with messages
};

// --- Message Services ---
const sendMessage = async (conversationId, content, sender = 'user') => {
  // This endpoint in the backend should ideally handle interaction with the AI Agent
  // and then return the AI's response, or at least confirm message persistence.
  // For now, it just posts the user's message. The AI call logic is in backend.
  const response = await apiClient.post(
    `/conversations/${conversationId}/messages/`,
    { content, sender }
  );
  return response.data; // The newly created message (user's message)
};


// This is a MOCK function for how frontend might get AI response.
// In reality, the backend's POST /conversations/{id}/messages/ should trigger AI
// and the response might be part of that, or a separate call if streaming.
// For now, let's assume the backend's POST message endpoint will be enhanced
// to return both user message and AI response, or the AI agent is called separately.

// For this learning project, we'll make a direct call from frontend to AI Agent Service.
// This is NOT recommended for production due to security (exposing AI agent) and complexity.
// In production, backend API should proxy requests to AI Agent Service.
const AI_AGENT_API_BASE_URL = process.env.REACT_APP_AI_AGENT_API_BASE_URL || '/api/v1/agent'; // Should be relative now

// getAiReply will be handled differently for streaming, typically directly in the component
// or via a modified service function that returns a ReadableStream or calls a callback.
// For simplicity, we might call fetch directly in ChatPage.js for the streaming part.
// However, let's define a function that initiates the streaming fetch.

const getAiReplyStream = async (
  userId,
  sessionId,
  message,
  model = 'gpt-4o-mini',
  onChunk, // Callback function to handle each received chunk: (chunk: string) => void
  onComplete, // Callback function when stream is complete: () => void
  onError     // Callback function for errors: (error: Error) => void
) => {
  // WARNING: Direct frontend to AI service call. For learning purposes only.
  // In production, backend API should proxy requests to AI Agent Service.

  // Construct the full URL for the AI agent chat endpoint
  // If AI_AGENT_API_BASE_URL is relative (e.g., /api/v1/agent), it will be resolved against current origin.
  const url = `${AI_AGENT_API_BASE_URL}/chat`;

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // Include Authorization header if your AI agent service is protected by the same JWT
        // This depends on whether the Nginx gateway forwards auth or if AI agent has its own auth.
        // For now, assuming AI agent is internally trusted or has simpler auth if any.
        // 'Authorization': `Bearer ${localStorage.getItem('token')}`, // Example if needed
      },
      body: JSON.stringify({
        user_id: userId,
        session_id: sessionId,
        message: message,
        model: model,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(`API error: ${response.status} ${errorData.detail || ''}`);
    }

    if (!response.body) {
      throw new Error('ReadableStream not available in response body.');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let reading = true;
    while (reading) {
      const { done, value } = await reader.read();
      if (done) {
        reading = false;
        break;
      }
      const chunk = decoder.decode(value, { stream: true });
      onChunk(chunk);
    }
    onComplete();

  } catch (error) {
    console.error("Error getting AI reply stream:", error);
    onError(error);
  }
};


const apiService = {
  setAuthToken,
  login,
  signup,
  getCurrentUser,
  createConversation,
  getConversations,
  getConversationDetails,
  sendMessage,
  // getAiReply, // Replaced by getAiReplyStream for streaming
  getAiReplyStream,
};

export default apiService;
