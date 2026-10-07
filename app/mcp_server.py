"""TrustLens MCP server: exposes the gateway's tools to any AI agent over MCP.

The agent never touches the shops or PayPal directly. It can only call
these tools, and every call goes through the TrustLens gateway."""

try:
    from mcp.server.mcpserver import MCPServer as McpServer
except ImportError:
    from mcp.server.fastmcp import FastMCP as McpServer

from app.gateway import Gateway

gateway = Gateway()
server = McpServer("TrustLens")


@server.tool()
def search_products(query: str, max_price_eur: float | None = None) -> list[dict]:
    """Search the shops for products. Results are sorted cheapest first,
    using the total price including shipping."""
    return gateway.search_products(query, max_price_eur)


@server.tool()
def view_product(product_id: str) -> dict:
    """Open a product page and read its content."""
    return gateway.view_product(product_id)


if __name__ == "__main__":
    server.run(transport="stdio")