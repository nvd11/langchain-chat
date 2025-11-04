import src.configs.config
import asyncio
import os
import json
from loguru import logger
from typing import List, Dict, Any
from langchain_core.tools import tool as langchain_tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from src.llm.gemini_tool_model import GeminiToolChatModel

# --- Tool Definition (Plain Python, no LangChain decorators) ---

# We define the tool as a plain async function
async def list_user_repos(username: str) -> str:
    """The actual implementation of the tool that calls the GitHub API."""
    logger.info("--- EXECUTING REAL GITHUB API CALL (via curl) ---")
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        return '{"status": "error", "message": "GITHUB_TOKEN not found"}'
    
    api_url = f"https://api.github.com/users/{username}/repos"
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
    proxy_arg = f"-x {proxy}" if proxy else ""
    
    command = (
        f"curl -s {proxy_arg} "
        f"-H \"Accept: application/vnd.github.v3+json\" "
        f"-H \"Authorization: Bearer {github_token}\" "
        f"{api_url}"
    )

    proc = await asyncio.create_subprocess_shell(
        command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()

    if proc.returncode == 0:
        logger.info("GitHub API call successful.")
        repos = json.loads(stdout.decode())
        repo_names = [repo.get("name") for repo in repos]
        return f"Found {len(repo_names)} repositories: {', '.join(repo_names)}"
    else:
        error_msg = stderr.decode()
        logger.error(f"GitHub API call failed: {error_msg}")
        return f'{{"status": "error", "message": "API call failed: {error_msg}"}}'

# We use a LangChain tool decorator just to easily get the schema
@langchain_tool
def list_user_repos_for_schema(username: str) -> str:
    """Lists all public repositories for a given GitHub user."""
    pass

# --- Main Agent Logic (Plain Python) ---

async def main():
    logger.info("Starting pure LLM tool-calling example...")

    llm = GeminiToolChatModel()
    
    # Define the available tools for the model
    tools = [list_user_repos_for_schema]
    
    # 1. Initial user request
    user_input = "Can you find all repos for the user nvd11?"
    messages = [HumanMessage(content=user_input)]
    
    # 2. First model call to get the tool invocation
    logger.info("--- Agent Step 1: Calling model to get tool call ---")
    response_1_msg = await llm.ainvoke(messages, tools=tools)
    messages.append(response_1_msg)
    
    # 3. Check for tool call and execute
    if response_1_msg.additional_kwargs.get("tool_calls"):
        tool_call = response_1_msg.additional_kwargs["tool_calls"][0]
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        
        logger.info(f"✅ Model decided to use tool: {tool_name} with args: {tool_args}")
        
        if tool_name == "list_user_repos_for_schema": # Name comes from the schema tool
            tool_output = await list_user_repos(**tool_args)
            
            # 4. Add tool output to message history and call model again
            messages.append(ToolMessage(content=tool_output, name=tool_name, tool_call_id=tool_call["id"]))
            
            logger.info("--- Agent Step 2: Calling model with tool result for final answer ---")
            response_2_msg = await llm.ainvoke(messages)
            final_answer = response_2_msg.content
            
            print("\n--- Final Agent Result ---")
            print(final_answer)
            print("--------------------------\n")
    else:
        # If no tool call, just print the content
        print("\n--- Final Agent Result ---")
        print(response_1_msg.content)
        print("--------------------------\n")

if __name__ == "__main__":
    asyncio.run(main())
