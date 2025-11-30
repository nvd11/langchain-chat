import pytest

import src.configs.config
from loguru import logger


import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.llm.gemini_chat_model import get_gemini_llm
from src.services import chat_service
from src.schemas.chat import ChatRequest
from src.llm.deepseek_chat_model import get_deepseek_llm
from src.services.llm_service import LLMService
from src.configs.db import get_db_session
from src.dao import conversation_dao
from src.schemas.conversation import ConversationCreateSchema

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
async def llm_service():
    """Fixture to provide a real LLMService instance."""
    return LLMService(llm=get_gemini_llm())

@pytest.fixture
async def db_session():
    """Fixture to provide a real database session."""
    session_generator = get_db_session()
    session = await anext(session_generator)
    try:
        yield session
    finally:
        await session.close()

@pytest.fixture
async def new_conversation(db_session: AsyncSession):
    """Fixture to create a new conversation for the test."""
    conv_create = ConversationCreateSchema(user_id=1) # Assuming user_id 1 exists or is not required
    conversation = await conversation_dao.create_conversation(db_session, conv=conv_create)
    return conversation

async def test_stream_chat_response_e2e(llm_service: LLMService, db_session: AsyncSession, new_conversation):
    """
    End-to-end test for the stream_chat_response function.
    This test makes a real call to the DeepSeek LLM and interacts with the database.
    """
    # 1. Prepare the request
    request = ChatRequest(
        conversation_id=new_conversation['id'],
        message="Hello, DeepSeek! Tell me why the sky is blue."
    )

    # 2. Call the function and collect the streamed response
    full_response = ""
    stream_generator = chat_service.stream_chat_response(request, llm_service, db_session)
    
    print("\n--- Streaming Response ---")
    try:
        async for chunk in stream_generator:
            # SSE format is "data: content\n\n"
            if chunk.startswith("data: "):
                # Precisely extract content, removing prefix and suffix without stripping spaces
                content = chunk[len("data: "):-2]
                
                # Print each chunk as it arrives, preserving all spaces and newlines
                print(content, end="", flush=True)
                full_response += content
    except Exception as e:
        pytest.fail(f"Streaming failed with an exception: {e}")
    finally:
        # Print a newline at the end of the stream
        print("\n--------------------------")


    # 3. Assertions
    assert full_response, "The streamed response should not be empty."
    assert len(full_response) > 10, "The streamed response should have a reasonable length."

    # Optional: You can add assertions here to check if the user and assistant messages
    # were correctly saved to the database. This would require querying the DB.
