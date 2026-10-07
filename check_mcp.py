"""Step 21: connect to the TrustLens MCP server like an AI agent would,
list its tools, and call one of them."""

import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    params = StdioServerParameters(command=sys.executable, args=["-m", "app.mcp_server"])

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Tools the agent is allowed to use:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")

            print("\nCalling search_products('antivirus') through MCP:")
            result = await session.call_tool("search_products", {"query": "antivirus"})
            for block in result.content:
                text = getattr(block, "text", None)
                if text:
                    print(f"  {text[:300]}")


asyncio.run(main())