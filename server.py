from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import os

# Import the chat router
from src.routers import chat_router

# Get root_path from an environment variable. Defaults to "/chat-api-svc" if not set.
root_path = os.getenv("ROOT_PATH", "/chat-api-svc")

# Initialize the FastAPI app
app = FastAPI(
    title="ChatGPT-style Streaming API",
    description="A simple API to demonstrate streaming chat responses.",
    version="1.0.0",
    root_path=root_path,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include the chat router
app.include_router(chat_router.router)

@app.get("/")
def read_root():
    """A simple root endpoint to confirm the server is running."""
    logger.info("Root endpoint was hit.")
    return {"message": "Welcome to the Streaming API. See /docs for details."}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
