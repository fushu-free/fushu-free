from config import MCP_HOST, MCP_PORT, MCP_ENDPOINT
from mcp_server import server

app = server.streamable_http_app(
    streamable_http_path=MCP_ENDPOINT,
    json_response=True,
    stateless_http=True,
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=MCP_HOST, port=MCP_PORT)