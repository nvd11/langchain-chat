from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from langchain_core.messages import AIMessage, HumanMessage

from src.services.llm_service import LLMService
from src.schemas.chat import ChatRequest
from src.dao import message_dao
from src.schemas.message import MessageCreateSchema

async def stream_chat_response(
    request: ChatRequest, llm_service: LLMService, db: AsyncSession
):
    """
    Handles the logic of saving messages, retrieving history,
    streaming the LLM response, and saving the final response.
    """
    if not llm_service:
        error_message = "LLM Service is not available."
        logger.error(error_message)
        yield f"data: {error_message}\n\n"
        return

    # 1. Save user message
    user_message_to_save = MessageCreateSchema(
        conversation_id=request.conversation_id, role="user", content=request.message
    )
    await message_dao.create_message(db, message=user_message_to_save)

    # 2. Load conversation history
    history_from_db = await message_dao.get_messages_by_conversation(
        db, conversation_id=request.conversation_id
    )
    
    # Format history for the LLM
    chat_history = []
    for msg in history_from_db:
        if msg['role'] == 'user':
            chat_history.append(HumanMessage(content=msg['content']))
        elif msg['role'] == 'assistant':
            chat_history.append(AIMessage(content=msg['content']))

    logger.info(f"Initiating true stream for conversation {request.conversation_id} with {len(chat_history)} messages in history.")
    
    full_response_content = ""
    try:
        # 3. Call the astream method on the service with history
        llm_stream = llm_service.llm.astream(chat_history)
        
        # 4. Iterate over the stream and yield each chunk to the client
        async for chunk in llm_stream:
            logger.debug(f"Received chunk of type {type(chunk)}: {chunk}")
            if hasattr(chunk, 'content') and chunk.content:
                full_response_content += chunk.content
                yield f"data: {chunk.content}\n\n"
        
        logger.info("Streaming finished.")
        
        # 5. Save assistant's full response
        if full_response_content:
            assistant_message_to_save = MessageCreateSchema(
                conversation_id=request.conversation_id,
                role="assistant",
                content=full_response_content,
            )
            await message_dao.create_message(db, message=assistant_message_to_save)

    except Exception as e:
        error_message = f"An error occurred during streaming: {e}"
        logger.exception(error_message)
        yield f"data: {error_message}\n\n"
