import src.configs.config
import asyncio
from loguru import logger
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.llm.gemini_web_async import GeminiWebAsyncChatModel

async def main():
    logger.info("Starting LangChain LCEL example...")

    # 1. Create the custom Gemini Web Async Chat Model instance
    gemini_model = GeminiWebAsyncChatModel(model_name="gemini-2.5-pro")

    # 2. Define the prompt template
    prompt = ChatPromptTemplate.from_template(
        "你是一个专业的命名大师。请为一个生产{product}的公司想一个好名字。"
    )

    # 3. Create the chain using LangChain Expression Language (LCEL)
    # This is the modern replacement for LLMChain
    chain = prompt | gemini_model | StrOutputParser()

    # 4. Run the chain asynchronously
    product_name = "彩色袜子"
    logger.info(f"Running chain for product: {product_name}")
    
    # Use `ainvoke` for async execution with LCEL
    result = await chain.ainvoke({"product": product_name})

    logger.info("Chain execution finished.")
    print("\n--- Chain Result ---")
    print(result)
    print("--------------------\n")

if __name__ == "__main__":
    asyncio.run(main())
