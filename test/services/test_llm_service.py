import pytest
import os
from unittest.mock import patch, AsyncMock, MagicMock

from langchain_core.messages import AIMessage
from src.llm.gemini_web_async import GeminiWebAsyncChatModel
from src.services.llm_service import LLMService

@pytest.fixture
def set_api_key():
    """Fixture to set the GEMINI_API_KEY environment variable for tests."""
    original_key = os.environ.get("GEMINI_API_KEY")
    test_key = "test-api-key"
    os.environ["GEMINI_API_KEY"] = test_key
    yield
    if original_key is None:
        if "GEMINI_API_KEY" in os.environ:
            del os.environ["GEMINI_API_KEY"]
    else:
        os.environ["GEMINI_API_KEY"] = original_key

@patch('aiohttp.ClientSession.post')
async def test_llm_service_with_gemini_model_success(mock_post, set_api_key):
    """
    Test that LLMService can successfully use GeminiWebAsyncChatModel
    and return a valid response when the underlying API call is mocked.
    """
    # 1. Mock the response from the external API
    mock_response_data = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "This is a mocked Gemini response."}],
                    "role": "model"
                }
            }
        ]
    }
    
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value=mock_response_data)
    # Configure raise_for_status as a synchronous mock, not an async one
    mock_response.raise_for_status = MagicMock()
    
    async_context_manager = AsyncMock()
    async_context_manager.__aenter__.return_value = mock_response
    mock_post.return_value = async_context_manager

    # 2. Initialize the model and the service
    gemini_model = GeminiWebAsyncChatModel()
    llm_service = LLMService(llm=gemini_model)

    # 3. Call the service
    prompt = "Tell me a joke."
    response = await llm_service.ainvoke(prompt)

    # 4. Assertions
    assert isinstance(response, AIMessage)
    assert response.content == "This is a mocked Gemini response."
    
    # Verify that the post method was called correctly
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    # The prompt string is converted to a HumanMessage internally by langchain
    assert call_args.kwargs['json']['contents'][0]['parts'][0]['text'] == prompt
