from langchain_deepseek import ChatDeepSeek
from src.configs.config import yaml_configs

def get_deepseek_llm():
    """
    Initializes and returns a ChatDeepSeek instance.
    """
    api_key = yaml_configs["deepseek"]["api-key"]
    base_url = yaml_configs["deepseek"]["base-url"]
    
    llm = ChatDeepSeek(
        model="deepseek-chat",
        temperature=0.2,
        max_tokens=None,
        api_key=api_key,
        base_url=base_url,
    )
    return llm
