from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables from .env file specifically for this module if needed,
# or rely on them being loaded at application startup or by Docker Compose.
# For local execution of scripts that might use this module directly (e.g. Alembic),
# loading here can be useful.
# load_dotenv(dotenv_path="../../.env") # If .env is in project root relative to this file's execution
# load_dotenv() # If .env is in the same directory or backend/

# The DATABASE_URL should be set in your environment (e.g., in .env file loaded by docker-compose)
# Default value is for docker-compose setup where 'db' is the service name for PostgreSQL.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/ai_agent_db")

if not SQLALCHEMY_DATABASE_URL:
    # This should ideally not happen if .env.example is followed and .env is configured.
    print("CRITICAL: DATABASE_URL environment variable is not set.")
    # Fallback to a default that might work in some local non-Docker setups if user has postgres running
    # SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost:5432/ai_agent_db"
    # Or raise an error:
    # raise ValueError("DATABASE_URL environment variable is not set.")


# The pool_pre_ping argument will help with dropped connections
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    connect_args={} # e.g. {"sslmode": "require"} for managed DBs like RDS often
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get DB session for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to create all tables (call this from main.py on startup or use Alembic)
# This is a simple way to create tables, not suitable for production migrations.
# Alembic is recommended for production.
def create_db_and_tables():
    # Import all models here before calling create_all
    # This ensures they are registered with Base.metadata
    from . import models # noqa
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully (if they didn't exist).")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        print(f"Attempted to connect to: {SQLALCHEMY_DATABASE_URL}")
        print("Ensure the database server is running and accessible, and credentials are correct.")

# If you want to use Alembic for migrations, you would typically initialize it
# in the `backend` directory:
# `alembic init alembic`
# Then configure `alembic.ini` and `env.py`.
# `env.py` would need access to `Base.metadata` and the `SQLALCHEMY_DATABASE_URL`.
# `target_metadata = Base.metadata` in `env.py`.
# And you'd run `alembic revision -m "create_initial_tables"` and `alembic upgrade head`.
# For this project, we'll start with `create_all` for simplicity and mention Alembic as a best practice.
