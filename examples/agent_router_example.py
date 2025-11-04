import src.configs.config
import asyncio
import os
import json
from loguru import logger
from typing import List, Dict, Any
from src.llm.gemini_tool_model import GeminiToolChatModel

# --- Tool Implementations ---

async def list_user_repos(username: str) -> str:
    """Calls the GitHub API to list user repositories."""
    logger.info(f"--- EXECUTING 'list_user_repos' tool for {username} ---")
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

async def create_github_issue(owner: str, repo: str, title: str, body: str) -> str:
    """Simulates creating a GitHub issue."""
    logger.info(f"--- SIMULATING 'create_github_issue' tool ---")
    logger.info(f"Owner: {owner}, Repo: {repo}, Title: {title}")
    return f"Successfully simulated creating issue '{title}' in {owner}/{repo}."

# --- Router and Agent Logic ---

class Tool:
    def __init__(self, name: str, description: str, coro, schema: Dict):
        self.name = name
        self.description = description
        self.coroutine = coro
        self.schema = schema

# Define our available tools
TOOLS = [
    Tool(
        name="list_user_repos",
        description="Useful for finding and listing all public repositories for a given GitHub user.",
        coro=list_user_repos,
        schema={"type": "object", "properties": {"username": {"type": "string"}}, "required": ["username"]}
    ),
    Tool(
        name="create_github_issue",
        description="Useful for creating a new issue in a GitHub repository. Requires owner, repo, title, and body.",
        coro=create_github_issue,
        schema={"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "title": {"type": "string"}, "body": {"type": "string"}}, "required": ["owner", "repo", "title", "body"]}
    )
]
TOOL_MAP = {tool.name: tool for tool in TOOLS}

async def router(user_input: str, llm: GeminiToolChatModel) -> Dict[str, Any]:
    """
    This is the 'Master Agent' or Router. It decides which tool to use.
    """
    logger.info("--- Router deciding which tool to use... ---")
    
    tool_descriptions = "\n".join([f"- {tool.name}: {tool.description}" for tool in TOOLS])
    
    prompt = f"""
    You are a smart router that chooses the best tool for a user's request.
    Based on the user's input, which of the following tools should you use?

    Available tools:
    {tool_descriptions}

    User input: "{user_input}"

    Respond with ONLY the name of the best tool to use.
    """
    
    response = await llm.ainvoke(prompt)
    chosen_tool_name = response.content.strip()
    logger.info(f"Router chose tool: {chosen_tool_name}")
    
    if chosen_tool_name not in TOOL_MAP:
        return {"error": f"Router chose an invalid tool: {chosen_tool_name}"}
        
    return {"next_tool": TOOL_MAP[chosen_tool_name]}

async def main():
    llm = GeminiToolChatModel()
    
    # --- First Use Case: Listing Repos ---
    user_input_1 = "Can you find all repos for the user nvd11?"
    logger.info(f"\n\n--- STARTING TASK 1: {user_input_1} ---")
    
    # 1. Ask the router which tool to use
    routing_decision = await router(user_input_1, llm)
    chosen_tool = routing_decision.get("next_tool")

    if chosen_tool:
        # 2. Use another LLM call to extract arguments for the chosen tool
        logger.info(f"--- Argument Extractor for '{chosen_tool.name}' deciding arguments... ---")
        arg_prompt = f"""
        You are an argument extractor. Based on the user's input, extract the JSON arguments for the '{chosen_tool.name}' tool.
        The tool's schema is: {json.dumps(chosen_tool.schema)}

        User input: "{user_input_1}"

        Respond with ONLY the JSON object of the arguments.
        """
        arg_response = await llm.ainvoke(arg_prompt)
        try:
            # Clean the string before parsing
            cleaned_json_str = arg_response.content.strip().replace("```json", "").replace("```", "").strip()
            tool_args = json.loads(cleaned_json_str)
            logger.info(f"Extractor found arguments: {tool_args}")
            
            # 3. Execute the tool
            tool_output = await chosen_tool.coroutine(**tool_args)
            
            # 4. Final LLM call to summarize the result
            logger.info("--- Summarizer generating final response... ---")
            summary_prompt = f"""
            You are a helpful assistant. You have just executed a tool and received a result.
            Original user input: "{user_input_1}"
            Tool result: "{tool_output}"
            Summarize the result for the user.
            """
            final_answer = (await llm.ainvoke(summary_prompt)).content
            
            print("\n--- Final Result for Task 1 ---")
            print(final_answer)
            print("---------------------------------\n")

        except json.JSONDecodeError:
            logger.error(f"Failed to decode arguments from LLM: {arg_response.content}")

if __name__ == "__main__":
    asyncio.run(main())
