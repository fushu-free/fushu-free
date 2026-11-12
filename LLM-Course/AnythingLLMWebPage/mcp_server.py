from config import SERVER_NAME, SERVER_VERSION, PROTOCOL_VERSION
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import TextContent, Tool, ListToolsResult, CallToolResult


async def list_tools_handler(context, params):
    return ListToolsResult(
        tools=[
            Tool(
                name="chat_with_workspace",
                description="从唯一工作区提取文档信息，基于文档内容回答用户问题。适用于查询工作区中文档相关的任何问题。",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "用户需要基于工作区文档回答的问题",
                        }
                    },
                    "required": ["question"],
                    "additionalProperties": False,
                },
            )
        ],
        resultType="complete",
    )


async def call_tool_handler(context, params):
    name = params.name
    arguments = params.arguments or {}
    if name != "chat_with_workspace":
        raise ValueError(f"Unknown tool: {name}")
    question = arguments.get("question")
    if not question or not isinstance(question, str):
        raise ValueError("Missing or invalid 'question' parameter")
    answer = f"Received question: {question}. This is a test response."
    return CallToolResult(content=[TextContent(type="text", text=answer)], result_type="complete")


server = Server(
    name=SERVER_NAME,
    version=SERVER_VERSION,
    instructions="AnytimeLLM workspace MCP server. Provides AI-powered answers based on your workspace documents.",
    on_list_tools=list_tools_handler,
    on_call_tool=call_tool_handler,
)


def get_initialization_options():
    from mcp.server.lowlevel.server import NotificationOptions
    return InitializationOptions(
        server_name=SERVER_NAME,
        server_version=SERVER_VERSION,
        protocol_version=PROTOCOL_VERSION,
        capabilities=server.get_capabilities(notification_options=NotificationOptions(tools_changed=True)),
    )