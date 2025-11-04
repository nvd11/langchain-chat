import src.configs.config
import asyncio
import os
import json
from loguru import logger
from typing import List, Dict, Any
from langchain_core.tools import tool as langchain_tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from src.llm.gemini_tool_model import GeminiToolChatModel

# --- Tool Definition ---
async def list_user_repos(username: str) -> str:
    logger.info("--- EXECUTING REAL GITHUB API CALL (via curl) ---")
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token: return '{"status": "error", "message": "GITHUB_TOKEN not found"}'
    api_url = f"https://api.github.com/users/{username}/repos"
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
    proxy_arg = f"-x {proxy}" if proxy else ""
    command = (f"curl -s {proxy_arg} -H \"Accept: application/vnd.github.v3+json\" "
               f"-H \"Authorization: Bearer {github_token}\" {api_url}")
    proc = await asyncio.create_subprocess_shell(
        command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    if proc.returncode == 0:
        repos = json.loads(stdout.decode())
        repo_names = [repo.get("name") for repo in repos]
        return f"Found {len(repo_names)} repositories: {', '.join(repo_names)}"
    else:
        return f'{{"status": "error", "message": "API call failed: {stderr.decode()}"}}'

@langchain_tool
def list_user_repos_for_schema(username: str) -> str:
    """Lists all public repositories for a given GitHub user."""
    pass

# --- The "Black Box" AgentExecutor ---
class MyAgentExecutor:
    def __init__(self, llm: GeminiToolChatModel, tools: List):
        self.llm = llm
        self.tools = tools
        self.tool_map = {tool.name: tool for tool in tools}

    async def ainvoke(self, user_input: str) -> str:
        messages = [HumanMessage(content=user_input)]
        llm_with_tools = self.llm.bind(tools=self.tools)
        
        while True:
            logger.info("--- Agent thinking... ---")
            ai_response = await llm_with_tools.ainvoke(messages)
            messages.append(ai_response)

            if not ai_response.additional_kwargs.get("tool_calls"):
                logger.info("--- Agent decided no tool is needed. Finishing. ---")
                return ai_response.content

            tool_call = ai_response.additional_kwargs["tool_calls"][0]
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            logger.info(f"--- Agent decided to use tool: {tool_name} ---")
            
            # Find and execute the correct tool
            if tool_name in self.tool_map:
                # Note: the schema tool name is what's called, but we execute the real one
                tool_output = await list_user_repos(**tool_args)
                messages.append(ToolMessage(content=tool_output, name=tool_name, tool_call_id=tool_call["id"]))
            else:
                logger.warning(f"Tool '{tool_name}' not found!")
                break

# --- Main Function (Now a clean "Black Box" call) ---
async def main():
    logger.info("Starting final 'black box' agent example...")

    agent_executor = MyAgentExecutor(
        llm=GeminiToolChatModel(),
        tools=[list_user_repos_for_schema]
    )

    user_input = "Can you find all repos for the user nvd11?"
    
    final_answer = await agent_executor.ainvoke(user_input)

    print("\n--- Final Black Box Result ---")
    print(final_answer)
    print("------------------------------\n")

if __name__ == "__main__":
    asyncio.run(main())
