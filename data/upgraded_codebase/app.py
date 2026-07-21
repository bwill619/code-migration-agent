import asyncio
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def index() -> str:
    await asyncio.sleep(2)
    return "Hello Legacy Flask Code!"


@app.get("/process")
async def process_data() -> str:
    await asyncio.sleep(2)
    return "Data Processed Successfully"