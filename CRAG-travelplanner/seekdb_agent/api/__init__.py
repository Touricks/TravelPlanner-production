"""
CRAG TravelPlanner API
======================
FastAPI 接口层

Endpoints:
- GET /health - 健康检查
- POST /api/v1/chat - 对话接口
- POST /api/v1/search - 搜索接口
"""

from seekdb_agent.api.main import app

__all__ = ["app"]
