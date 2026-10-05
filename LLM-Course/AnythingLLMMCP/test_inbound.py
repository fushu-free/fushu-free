from mcp.server._streamable_http_modern import classify_inbound_request

body = {
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

result = classify_inbound_request(body, headers={
    'mcp-protocol-version': '2026-07-28',
    'mcp-method': 'tools/call',
    'mcp-name': 'chat_with_workspace'
})
print('Result:', result)
print('Type:', type(result))
