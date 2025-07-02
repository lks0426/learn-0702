from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import List, Annotated # Optional removed as not used directly here

from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import SessionLocal, engine, create_db_and_tables

# --- Configuration ---
# These should be loaded from environment variables (e.g., via .env file)
# For simplicity in this example, they are hardcoded but .env loading is preferred.
# from dotenv import load_dotenv
import os
# load_dotenv() # Ideally call this if running standalone, or rely on Docker Compose env vars

SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key_for_jwt_change_this_12345")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


app = FastAPI(
    title="AI Agent Backend API",
    description="API for managing users, conversations, and AI interactions.",
    version="0.1.0"
)

# --- Security ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # Relative URL for token endpoint

# --- Database Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Helper Functions ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15) # Default expiry
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user_from_token(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
        # token_data = schemas.TokenData(username=username) # Not strictly needed if only username is used
    except JWTError:
        raise credentials_exception

    user = crud.get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: Annotated[models.User, Depends(get_current_user_from_token)]):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# --- API Endpoints ---

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
async def create_new_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user_by_username = crud.get_user_by_username(db, username=user.username)
    if db_user_by_username:
        raise HTTPException(status_code=400, detail="Username already registered")
    db_user_by_email = crud.get_user_by_email(db, email=user.email)
    if db_user_by_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user.password)
    return crud.create_user(db=db, user=user, hashed_password=hashed_password)


@app.get("/users/me/", response_model=schemas.User)
async def read_users_me(current_user: Annotated[models.User, Depends(get_current_active_user)]):
    # current_user is already a models.User instance, Pydantic will map it to schemas.User
    return current_user


@app.get("/health", response_model=schemas.HealthCheck)
async def health_check():
    # Add DB check later if needed
    return {"name": "AI Agent Backend API", "version": "0.1.0", "status": "OK"}

# Conversation Endpoints
@app.post("/conversations/", response_model=schemas.Conversation, status_code=status.HTTP_201_CREATED)
async def create_new_conversation(
    conversation: schemas.ConversationCreate,
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    return crud.create_conversation(db=db, conversation=conversation, user_id=current_user.id)

@app.get("/conversations/", response_model=List[schemas.ConversationListing])
async def get_user_conversations(
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    conversations = crud.get_conversations_by_user(db=db, user_id=current_user.id, skip=skip, limit=limit)
    return conversations

@app.get("/conversations/{conversation_id}", response_model=schemas.Conversation)
async def get_single_conversation(
    conversation_id: int,
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    db_conversation = crud.get_conversation(db=db, conversation_id=conversation_id, user_id=current_user.id)
    if db_conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found or access denied")
    # The conversation model should have messages relationship correctly loaded if using default relationship loading
    # or specify lazy='joined' / selectinload in model relationship for eager loading.
    # For this schema, messages are expected. SQLAlchemy handles this.
    return db_conversation


@app.post("/conversations/{conversation_id}/messages/", response_model=schemas.Message, status_code=status.HTTP_201_CREATED)
async def add_message_to_existing_conversation(
    conversation_id: int,
    message: schemas.MessageCreate,
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    # Check if conversation exists and belongs to the user
    db_conversation = crud.get_conversation(db=db, conversation_id=conversation_id, user_id=current_user.id)
    if not db_conversation:
        raise HTTPException(status_code=404, detail="Conversation not found or access denied")

    # Here, the backend receives a message (likely from the user via frontend).
    # It stores this message.
    user_db_message = crud.create_message(db=db, message=message, conversation_id=conversation_id)

    # TODO LATER: Trigger AI Agent interaction.
    # Option 1: Backend calls AI Agent service, gets reply, stores AI message.
    # Option 2: Frontend calls AI Agent service (as currently implemented for simplicity), then calls this endpoint again for AI message.
    # Option 3: This endpoint returns user_db_message, frontend calls AI agent, then frontend calls a *new* endpoint to post AI's message.

    # For now, this endpoint just stores the message it received.
    # If the sender is 'user', the frontend will then call the AI agent.
    # If the sender is 'ai' (called by frontend after AI agent reply), it's also just stored.
    return user_db_message

# --- Logging and Startup/Shutdown ---
import logging
from .cache import get_redis_client # Import Redis utility

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    logger.info("Backend API starting up...")

    # Initialize Database
    logger.info(f"Attempting to connect to database: {engine.url}")
    try:
        # This is a simple way to create tables for development.
        # For production, use Alembic migrations.
        create_db_and_tables()
        logger.info("Database tables checked/created.")
    except Exception as e:
        logger.error(f"Failed to connect to database or create tables: {e}")
        # Depending on the severity, you might want to prevent the app from starting.
        # For now, it will log the error and continue. Docker health checks might catch this.

    # Initialize Redis Client
    redis = get_redis_client()
    if redis:
        logger.info("Redis client initialized successfully for backend.")
        # You can perform a test set/get here if desired
        # from .cache import set_cache, get_cache
        # set_cache("backend_startup_test", "ok", ttl_seconds=60)
        # logger.info(f"Redis test get: {get_cache('backend_startup_test')}")
    else:
        logger.warning("Redis client failed to initialize for backend. Caching will be unavailable.")


    # Load other configurations if needed
    logger.info(f"SECRET_KEY loaded: {'Yes' if SECRET_KEY else 'No'}")
    logger.info(f"ACCESS_TOKEN_EXPIRE_MINUTES: {ACCESS_TOKEN_EXPIRE_MINUTES}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Backend API shutting down...")

# To run (from backend directory):
# uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# (Ensure .env file is present in backend/ or project root if variables are not set by Docker)
