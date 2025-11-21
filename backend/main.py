import subprocess
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routers import video_router
from pathlib import Path

API_PREFIX = "/api/v1"

app = FastAPI(title="Video API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(video_router, prefix=API_PREFIX)

samples_path = Path("samples")
if samples_path.exists():
    app.mount("/samples", StaticFiles(directory="samples"), name="samples")
else:
    print(f"Warning: samples directory not found at {samples_path.absolute()}")

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