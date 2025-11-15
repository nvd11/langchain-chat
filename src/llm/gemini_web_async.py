import src.configs.config
import os
import aiohttp
import asyncio
import ssl
import certifi
from typing import Any, List, Optional
from loguru import logger
from langchain_core.callbacks.manager import AsyncCallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_core.outputs import ChatResult, ChatGeneration, GenerationChunk
from langchain_core.messages import AIMessageChunk
from dotenv import load_dotenv
import json
import io

class GeminiWebAsyncChatModel(BaseChatModel):
    model_name: str = "gemini-2.5-pro"
    google_api_key: Optional[str] = None
    
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        logger.info("Initializing GeminiWebAsyncChatModel...")
        self.google_api_key = self.google_api_key or os.getenv("GEMINI_API_KEY")
        if not self.google_api_key:
            logger.error("GEMINI_API_KEY not found.")
            raise ValueError("GEMINI_API_KEY not found in .env file or as a parameter")

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        logger.info("Generating chat completion using Gemini Web API (async)...")
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.google_api_key}"
        
        contents = [{"role": "user", "parts": [{"text": msg.content}]} for msg in messages if isinstance(msg, HumanMessage)]
        payload = {"contents": contents}
        
        proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
        
        logger.info(f"Sending request to {url} with proxy: {proxy}")
        
        try:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, proxy=proxy, ssl=ssl_context) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
            logger.info("Received response from Gemini Web API (async).")
            content = data['candidates'][0]['content']['parts'][0]['text']
            
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])

        except Exception as e:
            logger.error(f"Error calling Gemini Web API (async): {e}")
            error_content = f"Failed to call Gemini API (async): {e}"
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=error_content))])

    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ):
        """Streaming implementation for the Gemini Web API."""
        logger.info("Streaming chat completion using Gemini Web API (async)...")
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:streamGenerateContent?key={self.google_api_key}"
        
        contents = [{"role": "user" if isinstance(msg, HumanMessage) else "model", "parts": [{"text": msg.content}]} for msg in messages]
        payload = {"contents": contents}
        
        proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
        
        logger.info(f"Sending stream request to {url} with proxy: {proxy}")
        
        try:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, proxy=proxy, ssl=ssl_context) as response:
                    response.raise_for_status()
                    
                    # Manually process the stream line by line
                    async for line in response.content:
                        if line:
                            try:
                                # The API returns a list of chunks, often just one
                                data = json.loads(line.decode('utf-8'))
                                for candidate in data.get('candidates', []):
                                    for part in candidate.get('content', {}).get('parts', []):
                                        if 'text' in part:
                                            for word in part['text'].split(' '):
                                                yield AIMessageChunk(content=word + ' ')
                            except json.JSONDecodeError:
                                # Ignore lines that are not valid JSON
                                continue

        except Exception as e:
            logger.exception(f"Error during Gemini Web API stream: {e}")
            yield AIMessageChunk(content=f"Failed to stream from Gemini API: {e}")

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        raise NotImplementedError(
            "This model does not support synchronous generation. Please use 'ainvoke' or 'astream' instead."
        )

    @property
    def _llm_type(self) -> str:
        return "gemini-web-async-chat-model"
