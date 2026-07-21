import asyncio
import httpx
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


# ---------------------------------------------------------------------------
# Pydantic response models
# ---------------------------------------------------------------------------

class UserResponse(BaseModel):
    """Structured response model for a single user."""
    model_config = {"extra": "allow"}


class PostsResponse(BaseModel):
    """Structured response model for a user's posts list."""
    model_config = {"extra": "allow"}


class SlowOperationResponse(BaseModel):
    """Structured response model for the slow operation endpoint."""
    status: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/users/{user_id}", response_model=dict)
async def fetch_user(user_id: int) -> dict:
    """
    Fetch a single user by ID from the upstream API.

    Replaces:
        - synchronous `requests.get()` → `await httpx.AsyncClient().get()`
        - Flask `jsonify()` → plain dict return (FastAPI serialises automatically)
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/users/{user_id}")
        response.raise_for_status()
        return response.json()


@app.get("/users/{user_id}/posts", response_model=list)
async def fetch_posts(user_id: int) -> list:
    """
    Fetch all posts belonging to a user by ID from the upstream API.

    Replaces:
        - synchronous `requests.get()` → `await httpx.AsyncClient().get()`
        - Flask `jsonify()` → plain dict/list return (FastAPI serialises automatically)
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.example.com/users/{user_id}/posts"
        )
        response.raise_for_status()
        return response.json()


@app.get("/slow/{duration}", response_model=SlowOperationResponse)
async def slow_operation(duration: int) -> SlowOperationResponse:
    """
    Simulate a slow operation without blocking the event loop.

    Replaces:
        - blocking `time.sleep(duration)` → `await asyncio.sleep(duration)`
    """
    await asyncio.sleep(duration)
    return SlowOperationResponse(status="done")