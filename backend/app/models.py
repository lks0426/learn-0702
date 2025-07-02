from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func # For default timestamps
from .database import Base # Import Base from database.py

# For pgvector, we'll need this later in the AI Agent part, but good to be aware.
# from pgvector.sqlalchemy import Vector # This would be used if models.py also defined vector tables

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    disabled = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=True, default="New Conversation")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.timestamp")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    sender = Column(String, nullable=False)  # "user" or "ai"
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Placeholder for future pgvector integration if message embeddings are stored directly here
    # or in a related table. For now, we'll keep it simple.
    # embedding = Column(Vector(1536)) # Example if using OpenAI's ada-002 embeddings

    conversation = relationship("Conversation", back_populates="messages")

# Note on pgvector:
# If we were to integrate pgvector directly into these models (e.g. storing message embeddings),
# we would:
# 1. Ensure the pgvector extension is enabled in PostgreSQL.
# 2. Add `from pgvector.sqlalchemy import Vector`
# 3. Add a `Column(Vector(DIMENSION))` to the relevant model.
# For this project, the AI Agent service will manage its own tables for embeddings,
# possibly linking back to these message IDs if needed, or the backend will manage them
# if the AI agent calls back to the backend to store embeddings.
# Let's plan for the AI Agent service to manage its own vector data for now,
# or a separate table managed by the backend.
# For simplicity of the current step, these models are purely relational.
# We will create a new table for embeddings later.
