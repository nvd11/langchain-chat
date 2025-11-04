import src.configs.config
import asyncio
import os
from loguru import logger
from pydantic import BaseModel, Field
from langchain_core.tools import tool
# Attempting to import from the classic package
from langchain_classic.agents.agent import AgentExecutor
from langchain_classic.agents.tool_calling_agent.base import create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from src.llm.gemini_tool_model import GeminiToolChatModel

# Using the real (simulated) tool from the other example
def mcp_tool_simulation(server_name: str, tool_name: str, arguments: dict):
    logger.info(f"--- SIMULATING MCP TOOL CALL ---")
    logger.info(f"Server: {server_name}")
    logger.info(f"Tool: {tool_name}")
    logger.info(f"Arguments: {arguments}")
    logger.info(f"---------------------------------")
    issue_url = f"https://github.com/{arguments['owner']}/{arguments['repo']}/issues/123"
    return f"Successfully created issue at {issue_url}"

class CreateIssueSchema(BaseModel):
    owner: str = Field(description="The owner of the repository.")
    repo: str = Field(description="The name of the repository.")
    title: str = Field(description="The title of the issue.")
    body: str = Field(description="The body content of the issue.")

@tool(args_schema=CreateIssueSchema)
def create_github_issue(owner: str, repo: str, title: str, body: str) -> str:
    """Creates a new issue on a GitHub repository."""
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        return "Error: GITHUB_TOKEN not found in environment."
    arguments = {"owner": owner, "repo": repo, "title": title, "body": body, "token": github_token}
    return mcp_tool_simulation(
        server_name="https://mcpserverhub.com/servers/github",
        tool_name="create_issue",
        arguments=arguments
    )

async def main():
    logger.info("Starting MCP Agent example with AgentExecutor from langchain_classic...")

    llm = GeminiToolChatModel()
    tools = [create_github_issue]

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful assistant that can create GitHub issues."),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )

    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    user_input = "Please create an issue in the 'langchain-mcp' repo owned by 'nvd11'. The title should be 'New Feature Request' and the body should be 'Please add support for streaming responses.'"
    
    result = await agent_executor.ainvoke({"input": user_input})

    logger.info("Agent execution finished.")
    print("\n--- AgentExecutor Result ---")
    print(result.get("output"))
    print("----------------------------\n")

if __name__ == "__main__":
    asyncio.run(main())
