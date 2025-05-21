from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from dotenv import load_dotenv
load_dotenv()

# ABSOLUTE_FILE_PATH = "C:\\Users\\Asus\\Downloads\\test
ABSOLUTE_FILE_PATH = "/Users/arindamkeswani/Desktop/Projects/Practice/ai/intro-to-adk"


root_agent = LlmAgent(
    model='gemini-2.0-flash',
    name='filesystem_assistant_agent',
    instruction='Help the user manage their files. You can list files, read files, etc. You can also read files stored in Google Drive.',
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command='npx',
                args=[
                    "-y",  # Argument for npx to auto-confirm install
                    "@modelcontextprotocol/server-filesystem",
                    ABSOLUTE_FILE_PATH
                ],
            ),
            # Optional: Filter which tools from the MCP server are exposed
            # tool_filter=['list_directory', 'read_file']
        ),
    ],
)