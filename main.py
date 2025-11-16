import sys
import subprocess
from fastapi import FastAPI
from routers import video_router

API_PREFIX = "/api/v1"

app = FastAPI(title="Video API")

app.include_router(video_router, prefix=API_PREFIX)

@app.get("/")
async def root():
    return {"message": "API v1"}

def main():
    subprocess.run([
        "uvicorn", "main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
    ])

if __name__ == "__main__":
    main()