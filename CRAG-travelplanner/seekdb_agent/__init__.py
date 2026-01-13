"""
CRAG TravelPlanner Agent
========================
基于OceanBase SeekDB的旅行规划智能体

使用示例:
    from seekdb_agent import app
    from langchain_core.messages import HumanMessage

    result = app.invoke({"messages": [HumanMessage(content="我想去杭州玩3天")]})
    print(result["final_response"])
"""

from seekdb_agent.graph import app, create_crag_graph
from seekdb_agent.state import CRAGState, POIResult, UserFeatures

__all__ = [
    "app",
    "create_crag_graph",
    "CRAGState",
    "POIResult",
    "UserFeatures",
]
