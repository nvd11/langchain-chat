import asyncio
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from starlette.responses import StreamingResponse
from loguru import logger

from src.llm.gemini_web_async import GeminiWebAsyncChatModel
from src.services.llm_service import LLMService

# Create an API router
router = APIRouter(
    prefix="/api/v1",
    tags=["Chat"],
)

# --- Dependency Injection ---
def get_llm_service():
    """Dependency to get a singleton instance of LLMService."""
    try:
        gemini_model = GeminiWebAsyncChatModel()
        return LLMService(llm=gemini_model)
    except ValueError as e:
        logger.error(f"Failed to initialize LLM service for dependency: {e}")
        return None

# --- Request and Response Models ---
class ChatRequest(BaseModel):
    message: str

# --- Stream Generator ---
async def stream_generator(prompt: str, llm_service: LLMService):
    """Async generator to stream the model's response."""
    if not llm_service:
        error_message = "LLM Service is not available."
        logger.error(error_message)
        yield f"data: {error_message}\n\n"
        return

    logger.info(f"Streaming response for prompt: '{prompt}'")
    try:
        response = await llm_service.ainvoke(prompt)
        full_message = response.content

        # Stream the response word by word to simulate real chunks
        words = full_message.split(' ')
        for word in words:
            yield f"data: {word} \n\n"
            await asyncio.sleep(0.05)  # Control the streaming speed
            
        logger.info("Streaming finished.")
    except Exception as e:
        error_message = f"An error occurred during streaming: {e}"
        logger.error(error_message)
        yield f"data: {error_message}\n\n"

# --- API Endpoint ---
@router.post("/chat")
async def chat(
    request: ChatRequest,
    llm_service: LLMService = Depends(get_llm_service)
):
    """
    Receives a user message and returns the model's response as a stream
    of Server-Sent Events (SSE).
    """
    logger.info(f"Received chat request with message: '{request.message}'")
    
    async def stream_wrapper():
        # A wrapper is needed because the dependency is injected into the endpoint,
        # not the generator directly.
        async for chunk in stream_generator(request.message, llm_service):
            yield chunk

    return StreamingResponse(
        stream_wrapper(),
        media_type="text/event-stream"
    )
