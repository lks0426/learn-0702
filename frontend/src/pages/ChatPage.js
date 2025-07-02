import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import apiService from '../services/apiService';
// Styles are in App.css

function ChatPage({ currentUser }) {
  const [conversations, setConversations] = useState([]);
  const { conversationId: paramConvId } = useParams();
  const navigate = useNavigate();

  const [currentConversationId, setCurrentConversationId] = useState(paramConvId);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fetch all conversations for the sidebar
  useEffect(() => {
    const fetchConversations = async () => {
      try {
        const convs = await apiService.getConversations();
        setConversations(convs.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)));
        if (!paramConvId && convs.length > 0) {
          // If no specific conversation ID in URL, try to load the latest one
          // navigate(`/chat/${convs[0].id}`, { replace: true });
          // setCurrentConversationId(convs[0].id);
        } else if (paramConvId) {
          setCurrentConversationId(paramConvId);
        }
      } catch (err) {
        console.error("Failed to fetch conversations:", err);
        setError("Could not load conversation list.");
      }
    };
    if (currentUser) {
      fetchConversations();
    }
  }, [currentUser, paramConvId, navigate]);

  // Fetch messages for the current conversation
  useEffect(() => {
    const fetchMessages = async () => {
      if (currentConversationId) {
        setIsLoading(true);
        setError('');
        try {
          const convDetails = await apiService.getConversationDetails(currentConversationId);
          setMessages(convDetails.messages.sort((a,b) => new Date(a.timestamp) - new Date(b.timestamp)));
        } catch (err) {
          console.error(`Failed to fetch messages for ${currentConversationId}:`, err);
          setError("Could not load messages for this conversation.");
          // if (err.response?.status === 404) navigate("/chat"); // Or show an error
        } finally {
          setIsLoading(false);
        }
      } else {
        setMessages([]); // Clear messages if no conversation is selected
      }
    };
    fetchMessages();
  }, [currentConversationId]);


  const handleNewConversation = async () => {
    try {
      const newConv = await apiService.createConversation('New Chat');
      setConversations(prev => [newConv, ...prev]);
      navigate(`/chat/${newConv.id}`);
      setCurrentConversationId(newConv.id);
      setMessages([]); // Start with a blank slate for messages
    } catch (err) {
      console.error("Failed to create new conversation:", err);
      setError("Could not start a new chat.");
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || !currentConversationId || !currentUser) return;

    const userMessageContent = newMessage;
    setNewMessage(''); // Clear input early

    // Optimistically display user's message
    const tempUserMessageId = `temp-user-${Date.now()}`;
    const userMessageForDisplay = {
      id: tempUserMessageId,
      content: userMessageContent,
      sender: 'user',
      timestamp: new Date().toISOString(),
      conversation_id: currentConversationId,
    };
    setMessages(prev => [...prev, userMessageForDisplay]);
    setIsLoading(true);
    setError(''); // Clear previous errors

    // Prepare AI message placeholder for streaming
    const tempAiMessageId = `temp-ai-${Date.now()}`;
    const aiMessagePlaceholder = {
      id: tempAiMessageId,
      content: '', // Initially empty, will be filled by stream
      sender: 'ai',
      timestamp: new Date().toISOString(), // This will be updated when final AI message is persisted
      conversation_id: currentConversationId,
      isStreaming: true,
    };
    setMessages(prev => [...prev, aiMessagePlaceholder]);

    try {
      // 1. Send user message to backend (it will be persisted)
      // We can get the persisted user message back to update its ID if needed
      const persistedUserMessage = await apiService.sendMessage(currentConversationId, userMessageContent, 'user');
      // Update user message in state with persisted ID (optional, but good for consistency)
      setMessages(prev => prev.map(m => m.id === tempUserMessageId ? { ...persistedUserMessage, id: persistedUserMessage.id || tempUserMessageId } : m));

      // 2. Call AI Agent service for streaming reply
      apiService.getAiReplyStream(
        currentUser.username, // or user.id
        currentConversationId,
        userMessageContent,
        undefined, // use default model in AI agent
        (chunk) => { // onChunk
          setMessages(prevMessages =>
            prevMessages.map(msg =>
              msg.id === tempAiMessageId
                ? { ...msg, content: msg.content + chunk }
                : msg
            )
          );
        },
        async () => { // onComplete: stream finished from AI Agent
          // The AI agent's stream_openai_response `finally` block handles persisting the full AI message.
          // Here, we just update the UI state to mark streaming as complete for this message.
          // And potentially refetch the AI message from backend to get its final persisted state.

          // To get the final AI message (with correct ID and timestamp from DB):
          // We need to know the full content of the AI message that was streamed to persist it on backend.
          // The current AI agent `stream_openai_response`'s `finally` block does this.
          // After it's stored, we might want to fetch it to update the frontend state.

          // For now, let's assume the AI message in state is complete.
          // We will remove isStreaming flag.
          // The AI agent's `stream_openai_response` `finally` block has already called
          // `cache_utils.add_message_to_redis_history` and `db_utils.store_message_embedding`.
          // The backend also needs to be informed of this AI message to store it in its Message table.
          // This is a slight architectural complexity with frontend calling AI agent directly.

          // Let's adjust: AI agent's `stream_openai_response` `finally` block should also call
          // backend's `/conversations/{id}/messages/` endpoint to store the AI message.
          // This is not implemented yet in AI agent.
          // For now, the frontend will do it after stream completion.

          let finalAiContent = "";
          setMessages(prevMessages => {
            const finalMessages = prevMessages.map(msg => {
              if (msg.id === tempAiMessageId) {
                finalAiContent = msg.content; // Grab the fully streamed content
                return { ...msg, isStreaming: false };
              }
              return msg;
            });
            return finalMessages;
          });

          if (finalAiContent) {
            try {
              const persistedAiMessage = await apiService.sendMessage(currentConversationId, finalAiContent, 'ai');
              setMessages(prev => prev.map(m => m.id === tempAiMessageId ? { ...persistedAiMessage, id: persistedAiMessage.id || tempAiMessageId } : m));
            } catch (persistError) {
              console.error("Failed to persist AI message to backend:", persistError);
              setError("Error saving AI response. The conversation might be out of sync.");
            }
          }
          setIsLoading(false);
        },
        (streamError) => { // onError
          console.error("Streaming error:", streamError);
          setError(`AI Connection Error: ${streamError.message}`);
          setMessages(prev => prev.filter(m => m.id !== tempAiMessageId)); // Remove placeholder
          setIsLoading(false);
        }
      );

    } catch (err) {
      console.error("Failed to send message or initiate AI reply:", err);
      setError(err.response?.data?.detail || "Failed to send message.");
      setMessages(prev => prev.filter(m => m.id !== tempUserMessageId && m.id !== tempAiMessageId)); // Clean up optimistic messages
      setIsLoading(false);
    }
    // No `finally` here as setIsLoading(false) is handled by onComplete/onError of stream
  };

  const switchConversation = (convId) => {
    if (convId !== currentConversationId) {
      navigate(`/chat/${convId}`);
      setCurrentConversationId(convId);
    }
  };

  return (
    <div className="chat-page-container" style={{display: 'flex', height: 'calc(100vh - 120px)', width: '100%'}}>
      <div className="chat-sidebar">
        <h3>Conversations</h3>
        <button onClick={handleNewConversation} className="new-chat-button">
          + New Chat
        </button>
        {error && <p style={{color: 'red'}}>{error}</p>}
        <ul>
          {conversations.map(conv => (
            <li
              key={conv.id}
              onClick={() => switchConversation(conv.id)}
              className={conv.id === currentConversationId ? 'active-conversation' : ''}
            >
              {conv.title || `Chat ${conv.id.substring(0, 8)}`}
            </li>
          ))}
        </ul>
      </div>

      <div className="chat-main">
        {currentConversationId ? (
          <>
            <div className="message-list">
              {messages.map((msg, index) => (
                <div key={msg.id || index} className={`message ${msg.sender}`}>
                  <div className="message-sender">{msg.sender === 'user' ? (currentUser?.username || 'User') : 'AI'}</div>
                  <div className="message-content">
                    {msg.content}
                    {msg.isStreaming && <span className="streaming-indicator">▍</span>}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} /> {/* For auto-scrolling */}
              {/* isLoading && general thinking indicator can be removed if streaming indicator is enough */}
              {/* {isLoading && messages.length > 0 && !messages.some(m=>m.isStreaming) && <div className="message ai"><div className="message-content"><i>Processing...</i></div></div>} */}
            </div>
            <form onSubmit={handleSendMessage} className="chat-input-container">
              <input
                type="text"
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                placeholder="Type your message..."
                disabled={isLoading}
              />
              <button type="submit" disabled={isLoading || !newMessage.trim()}>
                Send
              </button>
            </form>
          </>
        ) : (
          <div style={{textAlign: 'center', padding: '20px'}}>
            <h2>Select a conversation or start a new one.</h2>
          </div>
        )}
      </div>
    </div>
  );
}

export default ChatPage;
