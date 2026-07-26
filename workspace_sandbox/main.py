from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4
from starlette.responses import RedirectResponse
from starlette.requests import Request
import sqlite3
import json

app = FastAPI(
    title="URL Shortener REST API",
    description="A simple URL shortener API using FastAPI and SQLite",
    version="1.0.0"
)

# Define the request and response models
class URL(BaseModel):
    original_url: str
    short_url: Optional[str] = None

# Connect to the SQLite database
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Create the table if it doesn't exist
def create_table():
    conn = get_db_connection()
    conn.execute('CREATE TABLE IF NOT EXISTS urls (original_url TEXT, short_url TEXT PRIMARY KEY)')
    conn.close()

create_table()

# Generate a short URL
def generate_short_url():
    return str(uuid4())[:6]

# Get the original URL from the short URL
def get_original_url(short_url):
    conn = get_db_connection()
    original_url = conn.execute('SELECT original_url FROM urls WHERE short_url = ?', (short_url,)).fetchone()
    conn.close()
    return original_url['original_url'] if original_url else None

# Create a new short URL
@app.post('/shorten')
async def shorten_url(url: URL):
    short_url = generate_short_url()
    conn = get_db_connection()
    conn.execute('INSERT INTO urls (original_url, short_url) VALUES (?, ?)', (url.original_url, short_url))
    conn.commit()
    conn.close()
    return {'short_url': short_url}

# Redirect to the original URL
@app.get('/{short_url}')
async def redirect(short_url: str):
    original_url = get_original_url(short_url)
    if original_url:
        return RedirectResponse(url=original_url, status_code=301)
    else:
        raise HTTPException(status_code=404, detail='URL not found')

# Get the stats of the short URL
@app.get('/stats/{short_url}')
async def get_stats(short_url: str):
    original_url = get_original_url(short_url)
    if original_url:
        return {'original_url': original_url}
    else:
        raise HTTPException(status_code=404, detail='URL not found')