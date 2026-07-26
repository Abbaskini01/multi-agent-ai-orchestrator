import redis
import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse


app = FastAPI()

 
# Initialize Redis Connection
r = redis.Redis(host='localhost', port=6379, db=0)


 
# Request Body for Shorten API
class ShortenRequest(BaseModel):
    original_url: str


 
# Request Body for GetOriginalUrl API
class GetOriginalUrlRequest(BaseModel):
    short_url: str


 
# Shorten URL API
@app.post("/shorten")
def shorten_url(request: ShortenRequest):
    try:
        original_url = request.original_url
        short_url_id = str(uuid.uuid4())[:6]
        r.set(short_url_id, original_url)
        return {"short_url": f"http://localhost:8000/{short_url_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


 
# Original URL API
@app.get("/{short_url_id}")
def get_original_url(short_url_id: str):
    try:
        original_url = r.get(short_url_id)
        if original_url is None:
            raise HTTPException(status_code=404, detail="URL not found")
        return JSONResponse(content={"original_url": original_url.decode()}, status_code=301)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))