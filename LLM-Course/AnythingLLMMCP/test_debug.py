import sys
import os
sys.path.insert(0, r"D:\fix\windows\anythingllm-mcp-server")
os.chdir(r"D:\fix\windows\anythingllm-mcp-server")

from mcp_server import server
from config import MCP_HOST, MCP_PORT, MCP_ENDPOINT
from mcp.server._streamable_http_modern import handle_modern_request
from mcp.server.models import JSONRPCRequest
import asyncio
import traceback

async def test_call():
    payload = {
        'jsonrpc': '2.0',
        'id': 2,
        'method': 'tools/call',
        'params': {
            'name': 'chat_with_workspace',
            'arguments': {'question': 'test'},
            '_meta': {
                'io.modelcontextprotocol/protocolVersion': '2026-07-28',
                'io.modelcontextprotocol/clientCapabilities': {}
            }
        }
    }
    decoded = payload
    req = JSONRPCRequest.model_validate(decoded)
    print(f"req.params type: {type(req.params)}")
    print(f"req.params: {req.params}")

    # Now test handle_modern_request by calling serve_one directly
    from mcp.server._streamable_http_modern import serve_one
    from mcp.server import Connection
    from mcp.server.models import DispatchContext

    connection = Connection(
        protocol_version="2026-07-28",
        client_info={},
        server_info={},
        state=None,
    )

    dctx = DispatchContext(
        transport_context=...,
        connection=connection,
        request_id=req.id,
        request=req,
    )

    try:
        result = await serve_one(
            server, dctx, req.method, req.params,
            connection=connection, lifespan_state=None
        )
        print(f"Result: {result}")
    except Exception as e:
        print(f"Exception in serve_one: {type(e).__name__}: {e}")
        traceback.print_exc()

asyncio.run(test_call())
