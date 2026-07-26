from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import uuid
import redis

app = FastAPI()

# Redis connection settings
redis_client = redis.Redis(host='localhost', port=6379, db=0)

class URL(BaseModel):
    original_url: str
    url_id: Optional[str] = None

# POST /url - create a new shortened URL
@app.post("/url")
async def create_url(url: URL):
    if not url.url_id:
        url_id = str(uuid.uuid4())[:6]
    else:
        url_id = url.url_id
    redis_client.set(url_id, url.original_url)
    return {"url_id": url_id, "shortened_url": f"http://localhost:8000/{url_id}"}

# GET /{url_id} - redirect to the original URL
@app.get("/{url_id}")
async def redirect_to_original_url(url_id: str):
    original_url = redis_client.get(url_id)
    if not original_url:
        raise HTTPException(status_code=404, detail="URL not found")
    return JSONResponse(content={"original_url": original_url.decode("utf-8")}, status_code=302, headers={"Location": original_url.decode("utf-8")})
