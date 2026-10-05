import httpx
from mcp.server.mcpserver import MCPServer

REST_API_BASE = "http://127.0.0.1:8080"

mcp = MCPServer(
    "pet-hospital-mcp",
    version="1.0.0",
)

_async_client: httpx.AsyncClient | None = None

def get_client() -> httpx.AsyncClient:
    global _async_client
    if _async_client is None:
        _async_client = httpx.AsyncClient(base_url=REST_API_BASE, timeout=30.0)
    return _async_client


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
    ownerName: str | None = None,
    ownerPhone: str | None = None,
    minCost: float | None = None,
    maxCost: float | None = None,
    sortBy: str | None = None,
    pageSize: int | None = None,
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
    if ownerName is not None:
        params["ownerName"] = ownerName
    if ownerPhone is not None:
        params["ownerPhone"] = ownerPhone
    if minCost is not None:
        params["min"] = minCost
    if maxCost is not None:
        params["max"] = maxCost
    if sortBy is not None:
        params["sortBy"] = sortBy
    if pageSize is not None:
        params["pageSize"] = pageSize

    response = await client.get("/api/v1/pets", params=params)
    response.raise_for_status()
    return response.json()


@mcp.tool()
async def pets_create(
    name: str,
    species: str,
    breed: str | None = None,
    gender: str | None = None,
    age_months: int | None = None,
    color: str | None = None,
    chip_no: str | None = None,
    owner_name: str | None = None,
    owner_phone: str | None = None,
    owner_addr: str | None = None,
    doctor: str | None = None,
    disease: str | None = None,
    status: str | None = None,
    allergy: str | None = None,
    note: str | None = None,
) -> dict:
    """
    新增/写入宠物档案。

    调用宠物医院 REST API 的 POST /api/v1/pets 接口，创建一条新的宠物档案。

    Args:
        name: 宠物姓名（必填）
        species: 种类（必填，取值：犬/猫/兔/鸟/仓鼠/爬宠/其他）
        breed: 品种
        gender: 性别（公/母）
        age_months: 年龄（月）
        color: 毛色
        chip_no: 芯片号
        owner_name: 主人姓名
        owner_phone: 主人电话
        owner_addr: 主人住址
        doctor: 主治医生
        disease: 疾病/主诉
        status: 就诊状态（如 已康复、住院中）
        allergy: 过敏史
        note: 备注
    """
    client = get_client()
    payload: dict = {"name": name, "species": species}

    if breed is not None:
        payload["breed"] = breed
    if gender is not None:
        payload["gender"] = gender
    if age_months is not None:
        payload["ageMonths"] = age_months
    if color is not None:
        payload["color"] = color
    if chip_no is not None:
        payload["chipNo"] = chip_no
    if owner_name is not None:
        payload["ownerName"] = owner_name
    if owner_phone is not None:
        payload["ownerPhone"] = owner_phone
    if owner_addr is not None:
        payload["ownerAddr"] = owner_addr
    if doctor is not None:
        payload["doctor"] = doctor
    if disease is not None:
        payload["disease"] = disease
    if status is not None:
        payload["status"] = status
    if allergy is not None:
        payload["allergy"] = allergy
    if note is not None:
        payload["note"] = note

    response = await client.post("/api/v1/pets", json=payload)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Pet Hospital MCP Server")
    parser.add_argument("-mcp-port", type=int, default=8081, help="MCP 服务器端口")
    parser.add_argument("-addr", type=str, default="http://127.0.0.1:8080", help="REST API 地址")
    parser.add_argument("-seed", action="store_true", help="启动时写入模拟数据")
    args = parser.parse_args()

    REST_API_BASE = args.addr

    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=args.mcp_port,
        stateless_http=True,
        json_response=True,
    )
