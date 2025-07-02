import redis # type: ignore
import os
import logging
import json
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_CHAT_HISTORY_TTL_SECONDS = int(os.getenv("REDIS_CHAT_HISTORY_TTL_SECONDS", 24 * 60 * 60)) # Default 1 day

# Global Redis client instance for AI Agent
ai_redis_client = None

def get_ai_redis_client():
    global ai_redis_client
    if ai_redis_client is None:
        try:
            logger.info(f"AI Agent: Attempting to connect to Redis at {REDIS_HOST}:{REDIS_PORT}")
            client_params = {
                "host": REDIS_HOST,
                "port": REDIS_PORT,
                "decode_responses": False # Important: Store as bytes to handle JSON manually for lists/dicts
            }
            if REDIS_PASSWORD:
                client_params["password"] = REDIS_PASSWORD

            ai_redis_client = redis.Redis(**client_params) # type: ignore
            ai_redis_client.ping()
            logger.info("AI Agent: Successfully connected to Redis.")
        except redis.exceptions.ConnectionError as e:
            logger.error(f"AI Agent: Could not connect to Redis: {e}")
            ai_redis_client = None
    return ai_redis_client

def get_chat_history_from_redis(session_id: str, max_turns: int) -> List[Dict[str, str]]:
    """
    Retrieves chat history for a session from Redis.
    Each turn (user message + AI response) is stored as a single JSON string in a Redis list.
    """
    client = get_ai_redis_client()
    if not client:
        logger.warning("AI Agent: Redis client not available for get_chat_history_from_redis.")
        return []

    key = f"chat_history:{session_id}"
    try:
        # Get the last N*2 elements (N turns, each turn has user and assistant message)
        # LRANGE key start stop (stop is inclusive)
        # LRANGE key -N*2 -1 gets the last N*2 elements
        raw_messages = client.lrange(key, -(max_turns * 2), -1)
        history = []
        for raw_msg in raw_messages:
            if raw_msg: # Ensure raw_msg is not None
                 history.append(json.loads(raw_msg.decode('utf-8'))) # Decode bytes then JSON loads
        return history
    except Exception as e:
        logger.error(f"AI Agent: Error retrieving chat history for session {session_id} from Redis: {e}")
        return []

def add_message_to_redis_history(session_id: str, role: str, content: str, max_turns: int):
    """
    Adds a message to the chat history in Redis for a session.
    Maintains a capped list of messages.
    """
    client = get_ai_redis_client()
    if not client:
        logger.warning("AI Agent: Redis client not available for add_message_to_redis_history.")
        return

    key = f"chat_history:{session_id}"
    message_data = {"role": role, "content": content}
    try:
        # Add the new message (as JSON string)
        client.rpush(key, json.dumps(message_data))
        # Trim the list to keep only the last N*2 messages
        # LTRIM key start stop (keeps elements from start to stop, inclusive)
        # LTRIM key -N*2 -1 keeps the last N*2 elements
        client.ltrim(key, -(max_turns * 2), -1)
        # Set TTL for the entire history key, refreshing it on each addition
        client.expire(key, REDIS_CHAT_HISTORY_TTL_SECONDS)
    except Exception as e:
        logger.error(f"AI Agent: Error adding message to chat history for session {session_id} in Redis: {e}")

# Initialize on module load (optional)
# get_ai_redis_client()

# Example usage in main.py (AI Agent):
# from .cache_utils import get_ai_redis_client, get_chat_history_from_redis, add_message_to_redis_history
#
# @app.on_event("startup")
# async def startup_event():
#     # ... other startup ...
#     redis_client = get_ai_redis_client()
#     if redis_client:
#         logger.info("AI Agent Redis client initialized.")
#     else:
#         logger.warning("AI Agent Redis client failed to initialize.")
#
# # In chat endpoint:
# # history = get_chat_history_from_redis(session_id, MAX_CHAT_TURNS_HISTORY)
# # add_message_to_redis_history(session_id, "user", user_message_content, MAX_CHAT_TURNS_HISTORY)
# # add_message_to_redis_history(session_id, "assistant", ai_reply_content, MAX_CHAT_TURNS_HISTORY)
