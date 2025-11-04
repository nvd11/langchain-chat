import src.configs.config
import os
import aiohttp
import json
import ssl
import certifi
from typing import Any, List, Optional, Dict, Type
from loguru import logger
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv(override=True)

def _format_tool_to_gemini_tool(tool: BaseTool) -> Dict[str, Any]:
    if tool.args_schema:
        schema = tool.args_schema.schema()
        return {
            "name": tool.name,
            "description": tool.description,
            "parameters": {
                "type": "object",
                "properties": schema.get("properties", {}),
                "required": schema.get("required", []),
            },
        }
    else:
        return {"name": tool.name, "description": tool.description}

class GeminiToolChatModel(BaseChatModel):
    model_name: str = "gemini-2.5-pro"
    google_api_key: Optional[str] = None
    
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.google_api_key = self.google_api_key or os.getenv("GEMINI_API_KEY")
        if not self.google_api_key:
            raise ValueError("GEMINI_API_KEY not found")

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        tools: Optional[List[BaseTool]] = None,
        **kwargs: Any,
    ) -> ChatResult:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.google_api_key}"
        
        contents = self._format_messages(messages)
        gemini_tools = [{"function_declarations": [_format_tool_to_gemini_tool(tool) for tool in tools]}] if tools else None
        
        payload = {"contents": contents}
        if gemini_tools:
            payload["tools"] = gemini_tools

        proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
        
        try:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, proxy=proxy, ssl=ssl_context) as response:
                    response.raise_for_status()
                    data = await response.json()

            part = data["candidates"][0]["content"]["parts"][0]
            if "functionCall" in part:
                function_call = part["functionCall"]
                tool_call = {"name": function_call["name"], "args": function_call["args"], "id": function_call["name"]}
                message = AIMessage(content="", additional_kwargs={"tool_calls": [tool_call]})
            else:
                message = AIMessage(content=part.get("text", ""))
            
            return ChatResult(generations=[ChatGeneration(message=message)])
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=f"API Error: {e}"))])

    def _generate(self, *args, **kwargs):
        raise NotImplementedError("This model is async only.")

    def _format_messages(self, messages: List[BaseMessage]) -> List[Dict[str, Any]]:
        # This formatting is for the direct web request
        formatted = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                formatted.append({"role": "user", "parts": [{"text": msg.content}]})
            elif isinstance(msg, AIMessage):
                if msg.additional_kwargs.get("tool_calls"):
                    tool_calls = msg.additional_kwargs["tool_calls"]
                    parts = [{"functionCall": {"name": tc["name"], "args": tc["args"]}} for tc in tool_calls]
                    formatted.append({"role": "model", "parts": parts})
                else:
                    formatted.append({"role": "model", "parts": [{"text": msg.content}]})
            elif isinstance(msg, ToolMessage):
                formatted.append({
                    "role": "tool",
                    "parts": [{"functionResponse": {"name": msg.name, "response": {"content": msg.content}}}]
                })
        return formatted

    @property
    def _llm_type(self) -> str:
        return "gemini-tool-chat-model"
