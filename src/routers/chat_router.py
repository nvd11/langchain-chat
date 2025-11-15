import asyncio
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from starlette.responses import StreamingResponse
from loguru import logger

from src.llm.deepseek_chat_model import get_deepseek_llm
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
        deepseek_model = get_deepseek_llm()
        return LLMService(llm=deepseek_model)
    except Exception as e:
        logger.error(f"Failed to initialize LLM service for dependency: {e}")
        return None

# --- Request and Response Models ---
class ChatRequest(BaseModel):
    message: str

# --- Stream Generator ---
async def stream_generator(prompt: str, llm_service: LLMService):
    """Async generator that yields response chunks from the LLM stream."""
    if not llm_service:
        error_message = "LLM Service is not available."
        logger.error(error_message)
        yield f"data: {error_message}\n\n"
        return

    logger.info(f"Initiating true stream for prompt: '{prompt}'")
    try:
        # Call the astream method on the service
        llm_stream = llm_service.astream(prompt)
        
        # Iterate over the stream and yield each chunk to the client
        async for chunk in llm_stream:
            logger.debug(f"Received chunk of type {type(chunk)}: {chunk}")
            if hasattr(chunk, 'content') and chunk.content:
                # The chunk is an AIMessageChunk object, we send its content directly
                yield f"data: {chunk.content}\n\n"
        
        logger.info("Streaming finished.")
    except Exception as e:
        error_message = f"An error occurred during streaming: {e}"
        logger.exception(error_message)  # Use logger.exception to include stack trace
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
