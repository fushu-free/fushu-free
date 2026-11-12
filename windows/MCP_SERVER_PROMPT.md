# 🐾 Pet Hospital MCP Server 开发提示词

> **目标**: 使用 Python + MCP Python SDK v2，为宠物医院 REST API 开发符合 `2026-07-28` 规范的 MCP 服务器。**MVP 阶段仅实现 `pets.list` 工具**，支持按各种参数筛选宠物。

---

## 一、项目背景

### 源服务：宠物医院 REST API

- **地址**: `http://127.0.0.1:8080`（默认端口）
- **协议**: 明文 HTTP，无鉴权，仅本地/内网
- **数据文件**: `data/pet.db`（单文件嵌入式数据库，含约 1008 条模拟数据）
- **技术栈**: Go 标准库，单文件可执行程序，零第三方依赖

### 现有 REST API（MVP 只用到的）

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/pets` | 列表：过滤 + 排序 + 分页 |
| `GET` | `/health` | 健康检查 |
| `GET` | `/api/v1/endpoints` | 接口清单（JSON） |

### 数据模型

主档 `Pet` 包含：`name`, `species`, `breed`, `gender`, `ageMonths`, `color`, `chipId`, `ownerName`, `ownerPhone`, `address`, `doctor`, `disease`, `status`, `allergyHistory`, `records[]`, `charges[]`

派生字段（只读）：`totalCost` = `charges[].amount` 之和，`visitCount` = `records` 条数

### 现有 REST API 查询参数（`/api/v1/pets`）

支持：`q` `name` `ownerName` `ownerPhone` `species` `doctor` `disease` `status` `min` `max` `sortBy` `order` `page` `pageSize`

示例：`curl -s 'http://127.0.0.1:8080/api/v1/pets?species=犬&min=1000&sortBy=totalCost&order=desc&page=1&pageSize=10'`

---

## 二、MCP 协议规范要求（2026-07-28）

### 核心变更

1. **无状态协议**：不再有 `initialize`/`initialized` 握手，不再有 `Mcp-Session-Id`
2. **每个请求自描述**：所有请求在 `_meta` 中携带：
   - `io.modelcontextprotocol/protocolVersion`（必需，值为 `"2026-07-28"`）
   - `io.modelcontextprotocol/clientCapabilities`（必需）
   - `io.modelcontextprotocol/clientInfo`（建议携带）
3. **`server/discover` RPC**：服务器 **MUST** 实现，宣告支持的协议版本、能力和身份
4. **Streamable HTTP 传输**：请求必须包含 `Mcp-Method` 和 `Mcp-Name` HTTP 头，且与 body 一致
5. **`resultType` 字段**：所有结果必须包含 `resultType`，值为 `"complete"` 或 `"input_required"`
6. **JSON-RPC 2.0 格式**：所有消息遵循 JSON-RPC 2.0
7. **缓存提示**：`tools/list` 返回 `ttlMs` 和 `cacheScope`
8. **废弃特性**：不要使用 Roots、Sampling、Logging、HTTP+SSE、DCR

### 关键错误码

| 码 | 名称 | 说明 |
|----|------|------|
| `-32602` | Invalid params | 参数无效 |
| `-32020` | HeaderMismatch | HTTP 头与 body 不一致 |
| `-32022` | UnsupportedProtocolVersion | 协议版本不支持 |

---

## 三、技术栈

### Python 依赖

```bash
pip install "mcp[cli]" uvicorn starlette httpx
```

或使用 `uv`：

```bash
uv add "mcp[cli]" uvicorn httpx
```

### 推荐库

| 库 | 用途 |
|----|------|
| `mcp` | MCP Python SDK v2，提供 `FastMCP` 类 |
| `httpx` | 异步 HTTP 客户端，调用现有 REST API |
| `uvicorn` | ASGI 服务器运行（如果需要） |

### Python 版本

**Python 3.10+**

---

## 四、MCP 服务器设计

### 4.1 传输层

- **传输**: Streamable HTTP（通过 `mcp.run(transport="streamable-http")`）
- **端口**: `8081`（或通过 `-mcp-port` 参数配置）
- **无状态模式**: `stateless_http=True`
- **端点**: `/mcp`（默认）
- **绑定地址**: `127.0.0.1`

### 4.2 服务器配置

```python
mcp = FastMCP(
    "pet-hospital-mcp",
    stateless_http=True,
    json_response=True,
)
```

### 4.3 MVP 工具：`pets.list`

这是唯一需要实现的工具。它将调用现有 REST API 的 `GET /api/v1/pets`，并将结果返回给 MCP Client。

**工具签名**：

```python
@mcp.tool()
async def pets_list(
    q: str | None = None,
    name: str | None = None,
    owner_name: str | None = None,
    owner_phone: str | None = None,
    species: str | None = None,
    doctor: str | None = None,
    disease: str | None = None,
    status: str | None = None,
    min_cost: float | None = None,
    max_cost: float | None = None,
    sort_by: str | None = None,
    order: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> dict:
    """
    查询宠物档案列表，支持多种筛选条件。
    
    调用宠物医院 REST API 的 GET /api/v1/pets 接口。
    """
```

**参数说明**：

| 参数 | 类型 | 说明 | 对应 REST 参数 |
|------|------|------|---------------|
| `q` | `str` | 全文检索关键词，空格分词AND | `q` |
| `name` | `str` | 宠物姓名 | `name` |
| `owner_name` | `str` | 主人姓名 | `ownerName` |
| `owner_phone` | `str` | 主人电话 | `ownerPhone` |
| `species` | `str` | 种类 | `species` |
| `doctor` | `str` | 主治医生 | `doctor` |
| `disease` | `str` | 疾病 | `disease` |
| `status` | `str` | 就诊状态 | `status` |
| `min_cost` | `float` | 最低总花费 | `min` |
| `max_cost` | `float` | 最高总花费 | `max` |
| `sort_by` | `str` | 排序字段 | `sortBy` |博士 | `order` | 排序方向（`asc`/`desc`） | `order` |
| `page` | `int` | 页码（从1开始） | `page` |
| `page_size` | `int` | 每页条数（默认10，最大100） | `pageSize` |

**注意**：Python 类型提示会自动生成 JSON Schema。MCP SDK 会自动处理工具发现、参数校验等协议细节。

---

## 五、完整代码框架

### 5.1 `pyproject.toml`

```toml
[project]
name = "pet-hospital-mcp"
version = "1.0.0"
requires-python = ">=3.10"
dependencies = [
    "mcp[cli]>=2.0.0rc1",
    "httpx>=0.27",
    "uvicorn>=0.31",
    "starlette>=0.27",
]
```

### 5.2 `server.py` — 完整实现

```python
import httpx
from mcp.server.fastmcp import FastMCP

# ── 配置 ──────────────────────────────────────────
REST_API_BASE = "http://127.0.0.1:8080"

# ── MCP 服务器 ────────────────────────────────────
mcp = FastMCP(
    "pet-hospital-mcp",
    stateless_http=True,
    json_response=True,
)

# ── HTTP 客户端 ───────────────────────────────────
_async_client: httpx.AsyncClient | None = None

def get_client() -> httpx.AsyncClient:
    global _async_client
    if _async_client is None:
        _async_client = httpx.AsyncClient(base_url=REST_API_BASE, timeout=30.0)
    return _async_client


# ── 工具定义 ──────────────────────────────────────
@mcp.tool()
async def pets_list(
    q: str | None = None,
    name: str | None = None,
    owner_name: str | None = None,
    owner_phone: str | None = None,
    species: str | None = None,
    doctor: str | None = None,
    disease: str | None = None,
    status: str | None = None,
    min_cost: float | None = None,
    max_cost: float | None = None,
    sort_by: str | None = None,
    order: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> dict:
    """
    查询宠物档案列表，支持多种筛选条件。

    调用宠物医院 REST API 的 GET /api/v1/pets 接口。

    Args:
        q: 全文检索关键词，空格分词AND
        name: 宠物姓名
        owner_name: 主人姓名
        owner_phone: 主人电话
        species: 种类（如 犬、猫）
        doctor: 主治医生
        disease: 疾病
        status: 就诊状态
        min_cost: 最低总花费
        max_cost: 最高总花费
        sort_by: 排序字段
        order: 排序方向 asc/desc
        page: 页码（从1开始）
        page_size: 每页条数（默认10，最大100）
    """
    client = get_client()
    params: dict = {"page": page, "pageSize": page_size}

    if q is not None:
        params["q"] = q
    if name is not None:
        params["name"] = name
    if owner_name is not None:
        params["ownerName"] = owner_name
    if owner_phone is not None:
        params["ownerPhone"] = owner_phone
    if species is not None:
        params["species"] = species
    if doctor is not None:
        params["doctor"] = doctor
    if disease is not None:
        params["disease"] = disease
    if status is not None:
        params["status"] = status
    if min_cost is not None:
        params["min"] = min_cost
    if max_cost is not None:
        params["max"] = max_cost
    if sort_by is not None:
        params["sortBy"] = sort_by
    if order is not None:
        params["order"] = order

    response = await client.get("/api/v1/pets", params=params)
    response.raise_for_status()
    return response.json()


# ── 启动 ──────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Pet Hospital MCP Server")
    parser.add_argument("-mcp-port", type=int, default=8081, help="MCP 服务器端口")
    parser.add_argument("-addr", type=str, default="http://127.0.0.1:8080", help="REST API 地址")
    parser.add_argument("-seed", action="store_true", help="启动时写入模拟数据")
    args = parser.parse_args()

    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=args.mcp_port,
        stateless_http=True,
    )
```

### 5.3 `test_client.py` — 测试客户端

```python
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def main():
    url = "http://127.0.0.1:8081/mcp"
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            # 1. server/discover
            result = await session.call_tool("server/discover", {})
            print("Discover:", result)

            # 2. tools/list
            tools = await session.list_tools()
            print("Tools:", [t.name for t in tools.tools])

            # 3. 调用 pets.list
            result = await session.call_tool("pets_list", {
                "species": "犬",
                "page": 1,
                "pageSize": 5,
            })
            print("pets_list result:", result)

            # 4. 调用 pets.list 带筛选
            result = await session.call_tool("pets_list", {
                "q": "肠胃炎",
                "minCost": 500,
                "sortBy": "totalCost",
                "order": "desc",
            })
            print("Filtered result:", result)

asyncio.run(main())
```

---

## 六、运行与验证

### 启动

```bash
# 确保宠物医院 REST API 已运行（pethospital.exe 或 go run .）
python server.py
# 或指定端口
python server.py -mcp-port 9090 -addr http://127.0.0.1:8080
# 或带模拟数据
python server.py -seed
```

### 使用 MCP Inspector 验证

```bash
python -m mcp dev server.py
```

或使用 curl 直接测试：

```bash
curl -s -X POST http://127.0.0.1:8081/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Method: tools/call" \
  -H "Mcp-Name: pets_list" \
  -H "MCP-Protocol-Version: 2026-07-28" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "pets_list",
      "arguments": {
        "species": "犬",
        "page": 1,
        "pageSize": 3
      }
    },
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientCapabilities": {},
      "io.modelcontextprotocol/clientInfo": {"name": "test-client", "version": "1.0.0"}
    }
  }'
```

### 预期响应

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "resultType": "complete",
    "content": [
      {
        "type": "text",
        "text": "{\"code\":200,\"data\":{\"list\":[...],\"total\":308,...}}"
      }
    ]
  },
  "_meta": {
    "io.modelcontextprotocol/serverInfo": {"name": "pet-hospital-mcp", "version": "1.0.0"}
  }
}
```

---

## 七、关键实现要点

1. **不要手动实现 `initialize` 握手**：MCP Python SDK v2 自动处理
2. **不要手动实现 `server/discover`**：SDK 自动实现
3. **不要手动构建 JSON-RPC 消息**：SDK 处理所有协议细节
4. **不要使用 session**：`stateless_http=True` 确保无状态
5. **不要使用 HTTP+SSE 传输**：只用 Streamable HTTP
6. **类型提示即 Schema**：Python 函数签名自动生成 JSON Schema
7. **异步函数**：`async def`，使用 `httpx.AsyncClient` 调用 REST API
8. **错误处理**：REST API 返回错误时 `raise_for_status()`，SDK 自动映射为 MCP 错误码
9. **缓存提示**：SDK 自动为 `tools/list` 添加 `ttlMs` 和 `cacheScope`
10. **`_meta` 由 SDK 自动处理**：无需手动构造

---

## 八、后续规划（不在 MVP 范围内）

MVP 完成后，后续可逐步添加：

| 阶段 | 功能 |
|------|------|
| Phase 2 | `pets.create`, `pets.get`, `pets.update`, `pets.delete` |
| Phase 3 | `pets.search`, `pets.byDoctor`, `pets.bySpecies` 等高级查询 |
| Phase 4 | `records.list`, `records.add`, `charges.list`, `charges.add` |
| Phase 5 | `data.export`, `admin.compact`, `admin.seed` |
| Phase 6 | Resources（种类/医生/状态列表）和 Prompts（摘要/报告模板） |

---

## 九、参考链接

- MCP Python SDK v2 仓库: https://github.com/modelcontextprotocol/python-sdk
- Python SDK 文档: https://modelcontextprotocol.io/
- MCP 2026-07-28 规范: https://modelcontextprotocol.io/specification/2026-07-28
- FastMCP 示例: https://github.com/modelcontextprotocol/python-sdk/tree/main/examples
- MCP Inspector 使用: `python -m mcp dev server.py`
