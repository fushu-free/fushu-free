import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

async def main():
    url = "http://127.0.0.1:8081/mcp"
    async with streamable_http_client(url) as (read, write):
        async with ClientSession(read, write) as session:
            tools = await session.list_tools()
            print("Tools:", [t.name for t in tools.tools])

            result = await session.call_tool("pets_list", {
                "species": "犬",
                "page": 1,
                "pageSize": 3,
            })
            print("pets_list result:", result)

            result = await session.call_tool("pets_list", {
                "q": "肠胃炎",
                "minCost": 500,
                "sortBy": "totalCost",
                "order": "desc",
            })
            print("Filtered result:", result)

asyncio.run(main())
