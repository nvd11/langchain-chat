import src.configs.config
import os
from typing import Any, List, Optional, Iterator
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from loguru import logger

load_dotenv(override=True)

class GeminiChatModel(BaseChatModel):
    model_name: str = "gemini-1.5-pro-latest"
    google_api_key: Optional[str] = None
    _client: Any = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.info("Initializing GeminiChatModel...")
        self.google_api_key = self.google_api_key or os.getenv("GEMINI_API_KEY")
        if not self.google_api_key:
            logger.error("GEMINI_API_KEY not found.")
            raise ValueError("GEMINI_API_KEY not found in .env file or as a parameter")
        
        logger.info(f"Creating ChatGoogleGenerativeAI client with model: {self.model_name}")
        self._client = ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=self.google_api_key
        )
        logger.info("ChatGoogleGenerativeAI client created.")

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        logger.info("Invoking Gemini model...")
        response = self._client.invoke(messages, stop=stop, **kwargs)
        logger.info("Gemini model invocation complete.")
        return ChatResult(generations=[ChatGeneration(message=response)])

    @property
    def _llm_type(self) -> str:
        return "gemini-chat-model"
