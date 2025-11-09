from fastapi import FastAPI
from loguru import logger

# Import the chat router
from src.api import chat

# Initialize the FastAPI app
app = FastAPI(
    title="ChatGPT-style Streaming API",
    description="A simple API to demonstrate streaming chat responses.",
    version="1.0.0",
)

# Include the chat router
app.include_router(chat.router)

@app.get("/")
def read_root():
    """A simple root endpoint to confirm the server is running."""
    logger.info("Root endpoint was hit.")
    return {"message": "Welcome to the Streaming API. See /docs for details."}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
