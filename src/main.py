"""
TRIZ IFR Agent - FastAPI 主入口

基于经典 TRIZ 倒推思维的漏斗收敛模型 Agent。
"""
import os
import httpx
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from src.config import get_settings
from src.api.v1.router import router as api_router


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时注册到控制面
    await register_agent()
    yield
    # 关闭时清理资源
    pass


app = FastAPI(
    title="TRIZ IFR Agent",
    description="TRIZ IFR 通用逆向收敛专家 - 基于倒推思维的漏斗收敛模型",
    version=settings.AGENT_VERSION,
    lifespan=lifespan
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok"}


@app.get("/metrics")
async def metrics():
    """Prometheus 监控指标端点"""
    return PlainTextResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get("/mcp/tools")
async def list_mcp_tools():
    """MCP 工具列表端点"""
    return {
        "tools": [
            {
                "name": "triz_solve",
                "description": "TRIZ IFR 逆向收敛求解",
                "parameters": {
                    "problem": {
                        "type": "string",
                        "description": "问题描述",
                        "required": True
                    },
                    "context": {
                        "type": "string",
                        "description": "额外上下文",
                        "required": False
                    },
                    "industry": {
                        "type": "string",
                        "description": "所属行业",
                        "required": False
                    }
                }
            },
            {
                "name": "resource_scan",
                "description": "扫描外部生态资源",
                "parameters": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词",
                        "required": True
                    },
                    "sources": {
                        "type": "array",
                        "description": "指定资源来源",
                        "required": False
                    }
                }
            },
            {
                "name": "contradiction_analysis",
                "description": "物理矛盾分析",
                "parameters": {
                    "problem": {
                        "type": "string",
                        "description": "问题描述",
                        "required": True
                    },
                    "factors": {
                        "type": "array",
                        "description": "已知有害因素",
                        "required": False
                    }
                }
            }
        ]
    }


@app.post("/mcp/tools/{tool_name}")
async def execute_mcp_tool(tool_name: str, request: dict):
    """MCP 工具执行端点"""
    if tool_name == "triz_solve":
        from src.api.v1.endpoints import solve_triz_ifr
        from src.models.schemas import SolveRequest

        solve_request = SolveRequest(
            problem=request.get("problem", ""),
            context=request.get("context"),
            industry=request.get("industry"),
            constraints=request.get("constraints", [])
        )
        return await solve_triz_ifr(solve_request, settings)

    elif tool_name == "resource_scan":
        return {
            "result": "资源扫描结果",
            "resources": [
                {"name": "GitHub", "url": "https://github.com/search?q=" + request.get("query", "")},
                {"name": "arXiv", "url": "https://arxiv.org/search/?query=" + request.get("query", "")}
            ]
        }

    elif tool_name == "contradiction_analysis":
        return {
            "result": "矛盾分析结果",
            "contradictions": [
                {
                    "parameter": "待分析参数",
                    "requirement_a": "条件 A",
                    "requirement_not_a": "条件非 A"
                }
            ]
        }

    else:
        return JSONResponse(
            status_code=404,
            content={"code": 404, "message": f"未知工具: {tool_name}", "data": {}}
        )


async def register_agent():
    """向控制面注册 Agent"""
    cp_api_key = settings.CP_API_KEY
    cp_base_url = settings.CP_BASE_URL
    agent_slug = settings.AGENT_NAME

    if not cp_api_key or not cp_base_url:
        print("[WARN] 控制面配置不完整，跳过注册")
        return

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{cp_base_url}/api/agents/register",
                headers={"Authorization": f"Bearer {cp_api_key}"},
                json={
                    "slug": agent_slug,
                    "endpoint": f"http://{agent_slug}_app:80",
                    "name": settings.AGENT_DESCRIPTION,
                    "version": settings.AGENT_VERSION
                },
                timeout=10.0
            )
            if response.status_code == 200:
                print(f"[INFO] Agent 已注册到控制面: {cp_base_url}")
            else:
                print(f"[WARN] Agent 注册失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[WARN] Agent 注册异常: {str(e)}")


# 挂载前端静态文件
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="static-assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """SPA fallback: 所有非 API 路径返回 index.html"""
        if full_path.startswith("api/") or full_path.startswith("health") or full_path.startswith("metrics") or full_path.startswith("mcp/"):
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        file_path = os.path.join(STATIC_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": f"服务器内部错误: {str(exc)}",
            "data": {}
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)
