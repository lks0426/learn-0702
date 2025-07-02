import redis # type: ignore
import os
import logging
import json # For serializing/deserializing complex data if needed
from typing import Optional, Any

logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None) # Default to None if not set

# Global Redis client instance
redis_client = None

def get_redis_client():
    global redis_client
    if redis_client is None:
        try:
            logger.info(f"Attempting to connect to Redis at {REDIS_HOST}:{REDIS_PORT}")
            # Create Redis client without AUTH for no-password setup
            if REDIS_PASSWORD:
                client_params = {
                    "host": REDIS_HOST,
                    "port": REDIS_PORT,
                    "decode_responses": True,
                    "password": REDIS_PASSWORD
                }
            else:
                client_params = {
                    "host": REDIS_HOST,
                    "port": REDIS_PORT,
                    "decode_responses": True
                    # No username/password for Redis without auth
                }

            redis_client = redis.Redis(**client_params) # type: ignore
            # Test connection without AUTH if no password is set
            redis_client.ping() # Check connection
            logger.info("Successfully connected to Redis.")
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Could not connect to Redis: {e}")
            # Depending on how critical Redis is, you might raise an error
            # or allow the app to run in a degraded mode.
            # For now, we'll let it be None, and operations will fail gracefully.
            redis_client = None # Explicitly set to None on failure
    return redis_client

# Example cache functions (can be expanded)
def set_cache(key: str, value: Any, ttl_seconds: int = 3600):
    """
    Set a value in cache. Value will be JSON serialized if it's a dict or list.
    """
    client = get_redis_client()
    if client:
        try:
            if isinstance(value, (dict, list)):
                value_to_set = json.dumps(value)
            else:
                value_to_set = value # type: ignore
            client.setex(name=key, time=ttl_seconds, value=value_to_set) # type: ignore
            logger.debug(f"Set cache for key '{key}' with TTL {ttl_seconds}s.")
        except Exception as e:
            logger.error(f"Failed to set cache for key '{key}': {e}")

def get_cache(key: str) -> Optional[Any]:
    """
    Get a value from cache. Attempts to JSON deserialize if value looks like JSON.
    """
    client = get_redis_client()
    if client:
        try:
            cached_value = client.get(key)
            if cached_value is not None:
                logger.debug(f"Cache hit for key '{key}'.")
                try:
                    # Attempt to parse if it looks like a JSON object or array
                    if cached_value.startswith('{') and cached_value.endswith('}'):
                        return json.loads(cached_value)
                    if cached_value.startswith('[') and cached_value.endswith(']'):
                        return json.loads(cached_value)
                except json.JSONDecodeError:
                    # Not a JSON string, return as is
                    pass
                return cached_value
            else:
                logger.debug(f"Cache miss for key '{key}'.")
                return None
        except Exception as e:
            logger.error(f"Failed to get cache for key '{key}': {e}")
            return None
    return None

def delete_cache(key: str):
    client = get_redis_client()
    if client:
        try:
            client.delete(key)
            logger.debug(f"Deleted cache for key '{key}'.")
        except Exception as e:
            logger.error(f"Failed to delete cache for key '{key}': {e}")

# Initialize on module load (optional, get_redis_client handles lazy init)
# get_redis_client()

# Example of how to use it in main.py:
# from .cache import get_redis_client, set_cache, get_cache
#
# @app.on_event("startup")
# async def startup_event():
#     # ... other startup code ...
#     redis = get_redis_client()
#     if redis:
#         logger.info("Redis client initialized for backend.")
#     else:
#         logger.warning("Redis client failed to initialize for backend.")
#
# @app.get("/some_cached_data/{item_id}")
# async def get_some_data(item_id: str, db: Session = Depends(get_db)):
#     cache_key = f"item:{item_id}"
#     cached_data = get_cache(cache_key)
#     if cached_data:
#         return {"source": "cache", "data": cached_data}
#
#     # data = fetch_from_db(db, item_id) # Your actual data fetching
#     data = {"id": item_id, "value": "some complex data from db"}
#     if data:
#         set_cache(cache_key, data, ttl_seconds=600)
#         return {"source": "database", "data": data}
#     raise HTTPException(status_code=404, detail="Item not found")
