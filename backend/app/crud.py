from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from . import models, schemas
from passlib.context import CryptContext # For password hashing if user creation is here

# Potentially move pwd_context here if user creation logic with hashing is centralized in CRUD
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# def get_password_hash(password):
#     return pwd_context.hash(password)

# --- User CRUD Operations ---
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate, hashed_password: str):
    db_user = models.User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password  # Hashing should be done before calling this
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- Conversation CRUD Operations ---
def create_conversation(db: Session, conversation: schemas.ConversationCreate, user_id: int):
    db_conversation = models.Conversation(
        title=conversation.title or "New Conversation", # Use default if title is empty
        user_id=user_id
    )
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation

def get_conversations_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 10):
    return db.query(models.Conversation)\
             .filter(models.Conversation.user_id == user_id)\
             .order_by(desc(models.Conversation.updated_at))\
             .offset(skip)\
             .limit(limit)\
             .all()

def get_conversation(db: Session, conversation_id: int, user_id: int):
    # Ensure the user owns the conversation
    return db.query(models.Conversation)\
             .filter(models.Conversation.id == conversation_id, models.Conversation.user_id == user_id)\
             .first()

def get_conversation_by_id_internal(db: Session, conversation_id: int):
    """
    Internal function to get conversation by ID without user check.
    Use with caution, ensure authorization is handled by the caller.
    """
    return db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()


# --- Message CRUD Operations ---
def create_message(db: Session, message: schemas.MessageCreate, conversation_id: int):
    db_message = models.Message(
        conversation_id=conversation_id,
        sender=message.sender,
        content=message.content
        # timestamp is server_default
    )
    db.add(db_message)

    # Update conversation's updated_at timestamp
    db_conversation = db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()
    if db_conversation:
        # The onupdate hook for updated_at should handle this automatically if the record is dirty.
        # Explicitly setting it ensures it happens, or just db.commit() might be enough if model is touched.
        # Forcing an update:
        db_conversation.title = db_conversation.title # Mark as dirty if not already
        # Or rely on SQLAlchemy's detection of changes on related objects, or simply commit.
        pass # The commit below should save the message and trigger conversation update if configured.

    db.commit()
    db.refresh(db_message)
    # db.refresh(db_conversation) # if db_conversation was modified and needs refresh

    return db_message

def get_messages_by_conversation(db: Session, conversation_id: int, skip: int = 0, limit: int = 100):
    # Assuming messages in Conversation model are ordered by timestamp
    # If not, add .order_by(asc(models.Message.timestamp))
    return db.query(models.Message)\
             .filter(models.Message.conversation_id == conversation_id)\
             .order_by(asc(models.Message.timestamp))\
             .offset(skip)\
             .limit(limit)\
             .all()
