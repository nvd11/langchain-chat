from fastapi import APIRouter, Depends
from starlette.responses import StreamingResponse
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.llm.deepseek_chat_model import get_deepseek_llm
from src.services.llm_service import LLMService
from src.configs.db import get_db_session
from src.schemas.chat import ChatRequest, PureChatRequest
from src.services import chat_service

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

# --- API Endpoint ---
@router.post("/chat")
async def chat(
    request: ChatRequest,
    llm_service: LLMService = Depends(get_llm_service),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Receives a user message, saves it, retrieves conversation history,
    and returns the model's response as a stream of Server-Sent Events (SSE).
    The assistant's final response is also saved to the database.
    """
    logger.info(f"Received chat request for conversation {request.conversation_id} with message: '{request.message}'")
    
    return StreamingResponse(
        chat_service.stream_chat_response(request, llm_service, db),
        media_type="text/event-stream"
    )

@router.post("/purechat")
async def pure_chat(
    request: PureChatRequest,
    llm_service: LLMService = Depends(get_llm_service),
):
    """
    Receives a user message and directly returns the model's response as a 
    stream of Server-Sent Events (SSE) without any database interaction.
    """
    logger.info(f"Received pure chat request with message: '{request.message}'")
    
    return StreamingResponse(
        chat_service.stream_pure_chat_response(request, llm_service),
        media_type="text/event-stream"
    )
