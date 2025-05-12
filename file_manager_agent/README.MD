## Prerequisites:

- Set up ADK: Follow the standard ADK [setup]() instructions in the quickstart.
- Install/update Python: MCP requires Python version of 3.9 or higher.
- Setup Node.js and npx: Many community MCP servers are distributed as Node.js packages
- Verify Installations: Confirm adk and npx are available within the activated virtual environment:
- Use Git Bash
- Check node version

# Both commands should print the path to the executables.
which adk
which npx

## MCPToolset

- Helps maintaining connection with with MCP servers, 
- Exposes them to our LLMAgent
- Helps our agent our agent with MCP Servers