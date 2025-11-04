import src.configs.config
import asyncio

import os
import json
from loguru import logger
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from src.llm.gemini_tool_model import GeminiToolChatModel

class ListUserReposSchema(BaseModel):
    username: str = Field(description="The GitHub username to query for repositories.")

@tool(args_schema=ListUserReposSchema)
async def list_user_repos(username: str) -> str:
    """Lists all public repositories for a given GitHub user by calling the GitHub REST API."""
    logger.info("--- PREPARING FOR GITHUB REST API CALL ---")
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

    logger.info(f"Executing command to call GitHub API...")

    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    if proc.returncode == 0:
        logger.info("GitHub API call successful.")
        # The output is a JSON array of repo objects. We can return it directly.
        return stdout.decode()
    else:
        logger.error(f"GitHub API call failed: {stderr.decode()}")
        return f'{{"status": "error", "message": "Failed to call GitHub API: {stderr.decode()}"}}'

async def main():
    logger.info("Starting Agent with REAL GitHub API call...")

    llm = GeminiToolChatModel()
    tools = [list_user_repos]
    llm_with_tools = llm.bind(tools=tools)

    user_input = "Can you find all repos for the user nvd11?"
    messages = [HumanMessage(content=user_input)]
    
    logger.info("--- Agent Step 1: Calling model to get tool call ---")
    ai_response_1 = await llm_with_tools.ainvoke(messages)
    messages.append(ai_response_1)
    
    if ai_response_1.additional_kwargs.get("tool_calls"):
        tool_call = ai_response_1.additional_kwargs["tool_calls"][0]
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        
        logger.info(f"✅ Model decided to use tool: {tool_name} with args: {tool_args}")
        
        if tool_name == "list_user_repos":
            tool_output = await list_user_repos.ainvoke(tool_args)
            
            # To avoid overwhelming the model, let's just pass the repo names
            try:
                repos = json.loads(tool_output)
                repo_names = [repo.get("name") for repo in repos]
                tool_result_for_model = f"Found {len(repo_names)} repositories: {', '.join(repo_names)}"
            except json.JSONDecodeError:
                tool_result_for_model = tool_output

            messages.append(ToolMessage(content=tool_result_for_model, name=tool_name, tool_call_id=tool_name))
            
            logger.info("--- Agent Step 2: Calling model with tool result for final answer ---")
            ai_response_2 = await llm.ainvoke(messages)
            
            print("\n--- Final Agent Result ---")
            print(ai_response_2.content)
            print("--------------------------\n")
    else:
        print("\n--- Final Agent Result ---")
        print(ai_response_1.content)
        print("--------------------------\n")

if __name__ == "__main__":
    asyncio.run(main())
