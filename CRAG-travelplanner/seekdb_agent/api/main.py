"""
CRAG TravelPlanner API - FastAPI 入口
=====================================
提供 RESTful API 接口

Endpoints:
- GET /health - 健康检查
- POST /api/v1/chat - 对话接口（调用 LangGraph 工作流）
- POST /api/v1/search - 搜索接口（直接调用 Hybrid Search）

启动方式:
    uvicorn seekdb_agent.api.main:app --reload --port 8000
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from seekdb_agent.api.schemas import HealthResponse

# 项目根目录和静态文件目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
STATIC_DIR = PROJECT_ROOT / "tests"

# 加载环境变量
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    """应用生命周期管理"""
    # 启动时预加载组件
    print("CRAG TravelPlanner API starting...")

    # 预加载 TF-IDF 编码器（避免首次请求延迟和运行时错误）
    try:
        from seekdb_agent.db.search import get_tfidf_encoder

        encoder = get_tfidf_encoder()
        print(f"TF-IDF encoder loaded (vocab size: {encoder.get_vocab_size()})")
    except Exception as e:
        print(f"WARNING: Failed to preload TF-IDF encoder: {e}")
        # 不阻止启动，让运行时给出具体错误

    yield
    # 关闭时
    print("CRAG TravelPlanner API shutting down...")


# 创建 FastAPI 应用
app = FastAPI(
    title="CRAG TravelPlanner API",
    description="基于 CRAG (Corrective RAG) 的智能旅游规划 API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== Health Check =====


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    """
    健康检查接口

    Returns:
        服务状态和版本信息
    """
    return HealthResponse(status="healthy", version="1.0.0")


# ===== 注册路由 =====
# 延迟导入避免循环依赖


def register_routers() -> None:
    """注册 API 路由"""
    from seekdb_agent.api.routers import chat, save, search, test

    app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
    app.include_router(save.router, prefix="/api/v1", tags=["save"])
    app.include_router(search.router, prefix="/api/v1", tags=["search"])
    app.include_router(test.router, tags=["testing"])


# 注册路由
register_routers()


# ===== 静态文件服务 =====


@app.get("/", include_in_schema=False)
async def serve_frontend() -> FileResponse:
    """提供前端测试页面"""
    return FileResponse(STATIC_DIR / "chat_test.html")


# 挂载静态文件目录（用于其他静态资源）
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ===== 主入口 =====

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "seekdb_agent.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
