from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import openai # type: ignore
import os
import asyncio # For async generator
from dotenv import load_dotenv
import logging
import hashlib
from typing import List, Optional, AsyncGenerator

from sqlalchemy.orm import Session
from . import db_utils # Assuming db_utils.py is in the same directory (app/)
from . import cache_utils # For Redis chat history

# Load environment variables
load_dotenv()

# --- Configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = "text-embedding-ada-002" # Or "text-embedding-3-small" etc.
MAX_CHAT_TURNS_HISTORY = int(os.getenv("MAX_CHAT_TURNS_HISTORY", "7")) # Max turns (user + AI) for direct context

if not OPENAI_API_KEY:
    logging.warning("OPENAI_API_KEY not found in environment variables. OpenAI calls will fail.")

app = FastAPI(
    title="AI Agent Service with pgvector & Streaming",
    description="Service for handling AI-powered chat (with streaming) and semantic search using pgvector.",
    version="0.1.2"
)

# --- Pydantic Models ---
class ChatRequest(BaseModel):
    user_id: str
    session_id: str
    message: str
    model: str = "gpt-4o-mini"

class ChatResponseChunk(BaseModel): # For documenting the structure of streamed chunks (optional)
    delta: str # The chunk of text from AI
    is_final: bool = False # Indicates if this is the last chunk for the AI's turn
    # session_id: str # Could be included in each chunk if needed by client

# --- Helper Functions ---
def get_md5_hash(text: str) -> str:
    return hashlib.md5(text.encode('utf-8')).hexdigest()

async def get_embedding(text: str, model: str = OPENAI_EMBEDDING_MODEL) -> list[float]:
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured for embeddings.")
    try:
        text = text.replace("\n", " ")
        response = await openai.embeddings.create(input=[text], model=model)
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error getting embedding from OpenAI: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get text embedding: {str(e)}")

# --- Streaming Chat Logic ---
async def stream_openai_response(
    model: str,
    messages_for_openai: list,
    session_id: str, # For potential use in chunk metadata
    db: Session # For storing full AI reply embedding at the end
) -> AsyncGenerator[str, None]:

    full_ai_reply_content = ""
    try:
        stream = await openai.chat.completions.create(
            model=model,
            messages=messages_for_openai, # type: ignore
            stream=True
        )
        async for chunk in stream:
            content_delta = chunk.choices[0].delta.content
            if content_delta:
                full_ai_reply_content += content_delta
                # Yield just the text delta for simple streaming
                # For more structured streaming (e.g. JSON objects per chunk):
                # yield json.dumps({"delta": content_delta, "session_id": session_id, "is_final": False}) + "\n"
                yield content_delta
                await asyncio.sleep(0.01) # Small sleep to allow other tasks, adjust as needed

    except openai.APIError as e:
        logger.error(f"OpenAI API Error during streaming chat for session {session_id}: {e}")
        error_message = f"Error from AI: {str(e)}"
        # yield json.dumps({"delta": error_message, "session_id": session_id, "is_final": True}) + "\n"
        yield error_message # stream error back
    except Exception as e:
        logger.error(f"Generic error during streaming chat for session {session_id}: {e}")
        error_message = f"An unexpected error occurred: {str(e)}"
        # yield json.dumps({"delta": error_message, "session_id": session_id, "is_final": True}) + "\n"
        yield error_message # stream error back
    finally:
        # This block executes after the generator is exhausted or closed.
        # Store the full AI reply and its embedding here.
        if full_ai_reply_content:
            logger.info(f"Full AI reply for session {session_id} (length {len(full_ai_reply_content)}): {full_ai_reply_content[:100]}...")
            cache_utils.add_message_to_redis_history(session_id, "assistant", full_ai_reply_content, MAX_CHAT_TURNS_HISTORY)
            try:
                ai_embedding = await get_embedding(full_ai_reply_content)
                db_utils.store_message_embedding(
                    db,
                    session_id=session_id,
                    sender="ai",
                    content=full_ai_reply_content,
                    embedding=ai_embedding,
                    content_hash=get_md5_hash(full_ai_reply_content)
                )
                logger.info(f"Stored embedding for full AI reply for session {session_id}.")
            except Exception as e:
                logger.error(f"Failed to store AI reply embedding after stream for session {session_id}: {e}")
        # Signal end of stream if using structured JSON chunks
        # yield json.dumps({"delta": "", "session_id": session_id, "is_final": True}) + "\n"


# --- API Endpoints ---
@app.post("/chat") # No response_model here for StreamingResponse with raw text
async def chat_endpoint_streaming(
    request: ChatRequest,
    db: Session = Depends(db_utils.get_db_session)
):
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured.")

    session_id = request.session_id
    user_message_content = request.message

    # 1. Get embedding for user's message and store it
    user_embedding = None
    try:
        user_embedding = await get_embedding(user_message_content)
        db_utils.store_message_embedding(
            db, session_id=session_id, sender="user", content=user_message_content,
            embedding=user_embedding, content_hash=get_md5_hash(user_message_content)
        )
    except Exception as e:
        logger.error(f"Failed to store user message embedding for session {session_id}: {e}")

    # 2. Retrieve relevant context using pgvector (RAG)
    retrieved_context_str = ""
    if user_embedding:
        try:
            similar_contents = db_utils.find_similar_message_contents(
                db, session_id=session_id, query_embedding=user_embedding,
                top_k=3, similarity_threshold=0.70
            )
            if similar_contents:
                retrieved_context_str = "\n\nRelevant past context:\n" + "\n---\n".join(similar_contents)
                logger.info(f"Retrieved {len(similar_contents)} similar messages for RAG for session {session_id}")
        except Exception as e:
            logger.error(f"Failed to retrieve similar messages (RAG) for session {session_id}: {e}")

    # 3. Add user message to short-term chat turn history (Redis)
    cache_utils.add_message_to_redis_history(session_id, "user", user_message_content, MAX_CHAT_TURNS_HISTORY)
    current_chat_turns = cache_utils.get_chat_history_from_redis(session_id, MAX_CHAT_TURNS_HISTORY)

    # 4. Prepare messages for OpenAI chat completion
    system_prompt = "You are a helpful AI assistant. "
    if retrieved_context_str:
        system_prompt += "Use the following relevant past context if helpful to answer the current user query."
        system_prompt += retrieved_context_str

    messages_for_openai = [{"role": "system", "content": system_prompt}] + current_chat_turns

    logger.info(f"Initiating stream to OpenAI chat model ({request.model}) for session {session_id}. Base message count: {len(messages_for_openai)}")

    # 5. Return StreamingResponse
    # The stream_openai_response generator will handle storing the full AI reply and its embedding in its `finally` block.
    return StreamingResponse(
        stream_openai_response(request.model, messages_for_openai, session_id, db),
        media_type="text/plain" # Or "application/x-ndjson" if streaming JSON objects
    )


@app.get("/health")
async def health_check(db: Session = Depends(db_utils.get_db_session)):
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        logger.error(f"Health check DB connection error: {e}")
        db_ok = False

    redis_ok = False
    try:
        client = cache_utils.get_ai_redis_client()
        if client and client.ping():
            redis_ok = True
    except Exception as e:
        logger.error(f"Health check Redis connection error: {e}")
        redis_ok = False

    return {
        "name": "AI Agent Service",
        "version": "0.1.2",
        "status": "OK" if db_ok and redis_ok else "DEGRADED",
        "openai_configured": bool(OPENAI_API_KEY),
        "database_connected": db_ok,
        "redis_connected": redis_ok
    }

# --- Logging Setup ---
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    logger.info("AI Agent Service (with pgvector & Streaming) starting up...")
    logger.info(f"OpenAI API Key Loaded: {'Yes' if OPENAI_API_KEY else 'No'}")

    db_conn_for_startup = None
    try:
        db_conn_for_startup = next(db_utils.get_db_session())
        logger.info(f"Attempting to connect to database for setup: {db_utils.engine.url}")
        db_utils.init_pgvector(db_conn_for_startup)
        db_utils.create_embeddings_table(db_conn_for_startup)
        logger.info("Database and pgvector initialization complete.")
    except Exception as e:
        logger.error(f"CRITICAL: Failed during database/pgvector initialization: {e}")
    finally:
        if db_conn_for_startup:
            db_conn_for_startup.close()

    ai_redis = cache_utils.get_ai_redis_client()
    if ai_redis:
        logger.info("AI Agent Redis client initialized successfully.")
    else:
        logger.warning("AI Agent Redis client failed to initialize. Chat history will be impaired.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("AI Agent Service shutting down...")
