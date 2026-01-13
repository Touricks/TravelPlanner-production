"""
CRAG TravelPlanner State Definitions
=====================================
定义LangGraph工作流中使用的状态类型

设计模式：
- 继承 AgentState 基类（自动提供 messages: list[BaseMessage]）
- 使用 NotRequired 标记可选字段
- 不需要dict格式，直接使用LangChain的BaseMessage对象

更新记录：
- 2026-01-09: UserFeatures 从 TypedDict 改为 Pydantic BaseModel
  - 原因：支持 LLM structured_output，消除类型转换
"""

from typing import Literal, NotRequired

from langchain.agents import AgentState
from pydantic import BaseModel, ConfigDict, Field


class UserFeatures(BaseModel):
    """
    用户特征 - 从对话中提取的用户偏好

    使用 Pydantic BaseModel 而非 TypedDict，优势：
    - 支持 LLM with_structured_output() 原生调用
    - 运行时类型验证
    - 更好的序列化支持 (.model_dump())
    """

    model_config = ConfigDict(populate_by_name=True)

    # 必填字段
    destination: str | None = Field(default=None, description="目的地城市")
    interests: list[str] = Field(default_factory=list, description="兴趣标签")
    travel_days: int | None = Field(default=None, description="旅行天数")

    # 预算与消费
    budget_meal: int | None = Field(default=None, description="每餐预算（美元，如 30）")
    price_preference: str | None = Field(default=None, description="整体价格偏好")

    # 交通与节奏
    transportation: str | None = Field(default=None, description="交通方式")
    pois_per_day: int | None = Field(default=None, description="每天游览景点数量")

    # 可选偏好
    must_visit: list[str] = Field(default_factory=list, description="必去景点")
    dietary_options: list[str] = Field(default_factory=list, description="餐饮偏好")

    # === Java 集成新增字段 ===
    start_date: str | None = Field(default=None, description="开始日期 YYYY-MM-DD")
    end_date: str | None = Field(default=None, description="结束日期 YYYY-MM-DD")
    number_of_travelers: int | None = Field(default=None, description="出行人数")
    has_children: bool | None = Field(default=None, description="是否有儿童同行")
    has_elderly: bool | None = Field(default=None, description="是否有老人同行")


class POIResult(BaseModel):
    """POI搜索结果 - 单个景点/餐厅/酒店信息"""

    model_config = ConfigDict(frozen=False)

    id: str = Field(description="POI唯一标识")
    name: str = Field(description="POI名称")
    city: str | None = Field(default=None, description="所在城市")
    state: str | None = Field(default=None, description="所在州/省")

    # 地理位置
    latitude: float | None = Field(default=None, description="纬度")
    longitude: float | None = Field(default=None, description="经度")

    # 评分与评价
    rating: float | None = Field(default=None, description="评分")
    reviews_count: int | None = Field(default=None, description="评论数")

    # 分类与价格
    price_level: int | None = Field(
        default=None, description="价格等级 (1-4: low/medium/high/luxury)"
    )
    primary_category: str | None = Field(default=None, description="主分类")

    # 描述
    editorial_summary: str | None = Field(default=None, description="编辑摘要")

    # 搜索相关性
    score: float = Field(default=0.0, description="RRF融合分数")

    # === Java 集成新增字段 ===
    address: str = Field(default="", description="完整地址")
    image_url: str | None = Field(default=None, description="图片 URL")
    opening_hours: str | None = Field(default=None, description="营业时间")


class CRAGState(AgentState):
    """
    CRAG工作流状态 - LangGraph节点间传递的状态

    继承自 AgentState，自动包含以下字段：
    - messages: list[BaseMessage]  # LangChain消息对象列表（不是dict！）

    关键设计：
    - 所有自定义字段使用 NotRequired 标记（AgentState要求）
    - messages 字段直接使用 BaseMessage 对象，无需转换
    - 节点函数返回 dict 格式的更新（LangGraph自动合并到state）
    """

    # ===== RAG查询 =====
    last_rag_query: NotRequired[str]  # 最近一次RAG查询文本

    # ===== 用户特征 =====
    user_features: NotRequired[UserFeatures]  # 提取的用户偏好
    feature_complete: NotRequired[bool]  # 特征是否完整
    missing_features: NotRequired[list[str]]  # 缺失的必填特征

    # ===== 搜索结果 =====
    search_results: NotRequired[list[POIResult]]  # 检索到的POI列表
    result_quality: NotRequired[Literal["good", "poor", "irrelevant"]]  # 结果质量评估

    # ===== 错误处理与重试 =====
    error_type: NotRequired[
        Literal["too_few", "irrelevant", "semantic_drift", "not_found", "missing_must_visit"] | None
    ]
    refined_query: NotRequired[str | None]  # LLM修正后的查询
    retry_count: NotRequired[int]  # 当前重试次数
    tried_queries: NotRequired[list[str]]  # 已尝试的查询列表

    # ===== 最终输出 =====
    fallback_triggered: NotRequired[bool]  # 是否触发降级策略
    final_response: NotRequired[str]  # 最终生成的回复

    # ===== 用户交互 =====
    optional_asked: NotRequired[bool]  # 是否已询问过可选字段（避免重复询问）

    # ===== Java 集成新增 =====
    recommended_pois: NotRequired[list[POIResult]]  # 推荐的 POI 列表
    suggested_plan: NotRequired[dict]  # 结构化行程安排
    plan_ready: NotRequired[bool]  # 计划是否可保存


# ===== 常量定义 =====
MAX_RETRY_COUNT = 3  # 最大重试次数
MIN_RESULTS_THRESHOLD = 8  # 结果数量下限
QUALITY_SCORE_THRESHOLD = 0.5  # 质量分数阈值
