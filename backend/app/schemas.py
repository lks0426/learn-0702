from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# --- User Schemas ---
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class User(UserBase): # Schema for returning user data (without password)
    id: int
    disabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True # For SQLAlchemy compatibility, allows mapping from ORM models

# Not directly used for responses, but useful for internal representation if needed
# class UserInDB(User):
#     hashed_password: str


# --- Message Schemas ---
class MessageBase(BaseModel):
    content: str
    sender: str # "user" or "ai"

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: int
    conversation_id: int
    timestamp: datetime

    class Config:
        orm_mode = True

# --- Conversation Schemas ---
class ConversationBase(BaseModel):
    title: Optional[str] = None

class ConversationCreate(ConversationBase):
    pass

class Conversation(ConversationBase): # Schema for returning a single conversation with its messages
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    messages: List[Message] = []

    class Config:
        orm_mode = True

class ConversationListing(ConversationBase): # Schema for listing conversations (without messages)
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    # messages: List[Message] = [] # Exclude messages for listings

    class Config:
        orm_mode = True

# --- Health Check Schema ---
class HealthCheck(BaseModel):
    name: str
    version: str
    status: str
