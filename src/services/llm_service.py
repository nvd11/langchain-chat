import src.configs.config
from langchain_core.language_models import BaseChatModel
from loguru import logger

class LLMService:
    def __init__(self, llm: BaseChatModel):
        logger.info("Initializing LLMService...")
        self.llm = llm
        logger.info("LLMService initialized.")

    async def ainvoke(self, prompt: str):
        logger.info(f"LLMService ainvoking with prompt: {prompt}")
        response = await self.llm.ainvoke(prompt)
        logger.info("LLMService ainvocation complete.")
        return response
