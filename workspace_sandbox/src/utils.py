from typing import Optional
import uuid
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

async def generate_url_id() -> str:
    return str(uuid.uuid4())[:6]

async def store_url(url_id: str, original_url: str) -> None:
    redis_client.set(url_id, original_url)

async def get_original_url(url_id: str) -> Optional[str]:
    original_url = redis_client.get(url_id)
    return original_url.decode('utf-8') if original_url else None