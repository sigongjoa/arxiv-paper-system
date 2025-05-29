import sys
import os

# Add root directory to path
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from api.routes import router

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="arXiv Paper Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    print("DEBUG: FastAPI server starting up...")

@app.get("/")
async def root():
    return {"message": "arXiv Paper Management API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
