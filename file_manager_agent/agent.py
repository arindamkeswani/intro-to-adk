from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from dotenv import load_dotenv
load_dotenv()



ABSOLUTE_FILE_PATH = "C:\\Users\\Asus\\Downloads\\test"
# ABSOLUTE_FILE_PATH = "/Users/arindamkeswani/Desktop/Projects/Practice/ai/intro-to-adk"

async def create_agent():
  """Gets tools from MCP Server."""
  try:
    tools, exit_stack = await MCPToolset.from_server(
        connection_params=StdioServerParameters(
            command='npx',
            args=["-y", "@modelcontextprotocol/server-filesystem", ABSOLUTE_FILE_PATH],
        )
    )
    

    agent = LlmAgent(
        model='gemini-2.0-flash',
        name='enterprise_assistant',
        instruction=(
            'Help user accessing their file systems'
        ),
        tools=tools,
    )
    return agent, exit_stack
  except Exception as e:
    print("ERROR", e)


root_agent = create_agent()