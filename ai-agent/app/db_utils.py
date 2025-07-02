import os
from typing import Optional, List
from sqlalchemy import create_engine, text, Column, Integer, Index, func, Text, DateTime, String
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from pgvector.sqlalchemy import Vector # type: ignore
from dotenv import load_dotenv
import logging

# Load environment variables
# Assumes .env might be in project root or ai-agent/
# load_dotenv(dotenv_path="../../.env")
# load_dotenv()

logger = logging.getLogger(__name__)

# --- Database Configuration ---
# The DATABASE_URL should be the same as the one used by the backend,
# as the AI agent will connect to the same PostgreSQL instance.
# It should be defined in the root .env file and passed by docker-compose.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/ai_agent_db")
OPENAI_EMBEDDING_DIM = int(os.getenv("PINECONE_VECTOR_DIMENSION", 1536)) # Re-using this env var for dimension

if not SQLALCHEMY_DATABASE_URL:
    logger.error("DATABASE_URL not set for AI Agent Service.")
    # Fallback or raise error
    # SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost:5432/ai_agent_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Embedding Model Definition ---
class MessageEmbedding(Base):
    __tablename__ = "message_embeddings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # backend_message_id = Column(Integer, nullable=True, index=True) # Optional: Link to backend's message.id
    session_id = Column(String, nullable=False, index=True) # To scope embeddings by session/conversation
    sender = Column(String, nullable=False) # "user" or "ai"
    content_hash = Column(String, nullable=True, index=True) # Optional: MD5 hash of content to avoid re-embedding exact same text
    content_preview = Column(Text, nullable=True) # Store a preview of the text that was embedded
    embedding = Column(Vector(OPENAI_EMBEDDING_DIM), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Create an IVFFlat index for faster similarity search on the 'embedding' column.
    # The lists parameter (e.g., 100) should be chosen based on the dataset size.
    # For up to 1M vectors, lists = rows / 1000. For up to 10M vectors, lists = sqrt(rows).
    # This is a general guideline.
    # HNSW index is generally better for speed/accuracy but requires more setup.
    # We'll use a simple cosine index for now, or IVFFlat if preferred.
    # __table_args__ = (
    #     Index("idx_message_embeddings_embedding_ivfflat", embedding, postgresql_using="ivfflat", postgresql_with={"lists": 100}, postgresql_ops={"embedding": "vector_cosine_ops"}),
    # )
    # For basic cosine similarity:
    __table_args__ = (
        Index('idx_message_embeddings_embedding_cos', embedding, postgresql_using='hnsw', postgresql_with={'m': 16, 'ef_construction': 64}, postgresql_ops={'embedding': 'vector_cosine_ops'}),
    )


# --- Database Utility Functions ---
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_pgvector(db: Session):
    try:
        db.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        db.commit()
        logger.info("pgvector extension checked/created successfully.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error enabling pgvector extension: {e}")
        raise

def create_embeddings_table(db: Session):
    try:
        Base.metadata.create_all(bind=engine, tables=[MessageEmbedding.__table__], checkfirst=True)
        db.commit() # Ensure table creation is committed
        logger.info("MessageEmbeddings table checked/created successfully.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating MessageEmbeddings table: {e}")
        raise

# --- CRUD for Embeddings (to be expanded) ---

def store_message_embedding(
    db: Session,
    session_id: str,
    sender: str,
    content: str,
    embedding: List[float],
    content_hash: Optional[str] = None
):
    db_embedding = MessageEmbedding(
        session_id=session_id,
        sender=sender,
        content_preview=content[:255], # Store a preview
        embedding=embedding,
        content_hash=content_hash
    )
    db.add(db_embedding)
    db.commit()
    db.refresh(db_embedding)
    logger.info(f"Stored embedding for session {session_id}, sender {sender}")
    return db_embedding

def find_similar_message_contents(db: Session, session_id: str, query_embedding: List[float], top_k: int = 3, similarity_threshold: float = 0.75) -> List[str]:
    """
    Finds messages with embeddings similar to the query_embedding within the same session.
    Returns a list of their content previews.
    Uses cosine distance (1 - cosine_similarity). Lower distance is more similar.
    """
    # vector_cosine_ops gives cosine distance. We want high similarity (low distance).
    # L2 distance: embedding <-> query_embedding
    # Inner product: embedding <#> query_embedding (negative for similarity with normalized vectors)
    # Cosine distance: embedding <=> query_embedding

    # The operator <=> calculates cosine distance. A smaller value means more similar.
    # So, we order by distance ASC.
    # Cosine similarity = 1 - cosine_distance.
    # If threshold is for similarity, convert: distance_threshold = 1 - similarity_threshold
    distance_threshold = 1 - similarity_threshold

    similar_embeddings = db.query(MessageEmbedding)\
        .filter(MessageEmbedding.session_id == session_id)\
        .filter(MessageEmbedding.embedding.cosine_distance(query_embedding) < distance_threshold)\
        .order_by(MessageEmbedding.embedding.cosine_distance(query_embedding).asc())\
        .limit(top_k)\
        .all()

    # Return the content previews of the found messages
    # Filter out the very last message if it's identical to the query (avoid self-matching immediately)
    # This logic might need refinement based on how content_preview is used.
    # For now, just return all found.

    # To get similarity score: (1 - MessageEmbedding.embedding.cosine_distance(query_embedding))
    # results_with_similarity = db.query(
    #     MessageEmbedding.content_preview,
    #     (1 - MessageEmbedding.embedding.cosine_distance(query_embedding)).label('similarity')
    # ).filter(MessageEmbedding.session_id == session_id)\
    #  .order_by(MessageEmbedding.embedding.cosine_distance(query_embedding).asc())\
    #  .limit(top_k)\
    #  .all()
    # return [res.content_preview for res in results_with_similarity if res.similarity > similarity_threshold]

    return [emb.content_preview for emb in similar_embeddings if emb.content_preview]


# Example usage (for testing, not part of the service logic directly here)
if __name__ == "__main__":
    # This is for standalone testing of this module if needed.
    logger.info("Running db_utils.py standalone for testing.")

    # Create a new session
    test_db_session = next(get_db_session())

    logger.info("Initializing pgvector extension...")
    init_pgvector(test_db_session)

    logger.info("Creating message_embeddings table...")
    create_embeddings_table(test_db_session)

    logger.info("Standalone test: pgvector initialized and table created (if they didn't exist).")

    # Example: Store an embedding
    # sample_embedding = [0.1] * OPENAI_EMBEDDING_DIM # Replace with actual embedding
    # try:
    #     logger.info("Attempting to store a sample embedding...")
    #     stored = store_message_embedding(test_db_session, session_id="test_session_123", sender="user", content="Hello world", embedding=sample_embedding)
    #     logger.info(f"Stored sample embedding with ID: {stored.id}")

    #     logger.info("Attempting to find similar embeddings...")
    #     similar_docs = find_similar_message_contents(test_db_session, session_id="test_session_123", query_embedding=sample_embedding, top_k=1)
    #     logger.info(f"Found similar docs: {similar_docs}")

    # except Exception as e:
    #     logger.error(f"Error during standalone test: {e}")
    # finally:
    #     test_db_session.close()
    #     logger.info("Test session closed.")
