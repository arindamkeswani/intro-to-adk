from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
import os
from dotenv import load_dotenv
load_dotenv()

root_agent = LlmAgent(
    model='gemini-2.0-flash',
    name='search_agent',
    instruction='Help the user search for various topics on the internet. Perform a web search by default.',
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command='npx',
                args=[
                    "-y",  # Argument for npx to auto-confirm install
                    "@modelcontextprotocol/server-brave-search",
                ],
                env = {
                    "BRAVE_API_KEY": os.getenv("BRAVE_API_KEY"),
                }
            ),
        ),
    ],
)