import src.configs.config
from src.llm.gemini_web_async import GeminiWebAsyncChatModel
from src.services.llm_service import LLMService
from loguru import logger
import asyncio

async def main():
    logger.info("Starting Gemini ASYNC example...")
    
    # 1. Create the custom Gemini Web Async Chat Model instance
    gemini_model = GeminiWebAsyncChatModel()

    # 2. Inject the model into the service
    llm_service = LLMService(llm=gemini_model)

    # 3. Use the service to invoke the model
    prompt = "你好，请你用中文介绍一下自己。"
    logger.info(f"Invoking LLM with prompt: '{prompt}'")
    
    response = await llm_service.ainvoke(prompt)

    logger.info("LLM Response received.")
    print("LLM Response:")
    print(response.content)
    logger.info("Gemini ASYNC example finished.")

if __name__ == "__main__":
    asyncio.run(main())
