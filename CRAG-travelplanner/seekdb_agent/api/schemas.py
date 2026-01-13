"""
API Request/Response Schemas
============================
Pydantic 模型定义
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

# ===== Chat API =====


class ChatRequest(BaseModel):
    """Chat 请求模型"""

    session_id: str | None = Field(default=None, description="会话ID，不提供则创建新会话")
    message: str = Field(default="", description="用户消息，空字符串触发冷启动问候")

    model_config = {"json_schema_extra": {"examples": [{"message": "我想去杭州玩3天"}]}}


class ChatResponse(BaseModel):
    """Chat 响应模型"""

    session_id: str = Field(description="会话ID")
    message: str = Field(description="AI 回复")
    user_features: dict[str, Any] | None = Field(default=None, description="提取的用户特征")
    feature_complete: bool | None = Field(default=None, description="特征是否完整")

    # === Java 集成新增字段 ===
    plan_ready: bool = Field(default=False, description="计划是否可保存")
    recommended_pois: list["POIForExport"] | None = Field(
        default=None, description="推荐的 POI 列表"
    )
    suggested_plan: "SuggestedPlan | None" = Field(default=None, description="AI 建议的行程安排")


# ===== Search API =====


class SearchRequest(BaseModel):
    """Search 请求模型"""

    query: str = Field(description="搜索查询")
    mode: Literal["balanced", "semantic", "keyword", "exact"] = Field(
        default="balanced", description="搜索模式"
    )
    top_k: int = Field(default=20, ge=1, le=100, description="返回结果数量")
    city: str | None = Field(default=None, description="城市过滤")

    model_config = {
        "json_schema_extra": {
            "examples": [{"query": "杭州历史文化景点", "mode": "balanced", "top_k": 20}]
        }
    }


class POIResultSchema(BaseModel):
    """POI 结果模型"""

    id: str = Field(description="POI ID")
    name: str = Field(description="POI 名称")
    city: str | None = Field(default=None, description="城市")
    state: str | None = Field(default=None, description="州/省")
    rating: float | None = Field(default=None, description="评分")
    reviews_count: int | None = Field(default=None, description="评论数")
    price_level: int | None = Field(default=None, description="价格等级")
    primary_category: str | None = Field(default=None, description="主分类")
    editorial_summary: str | None = Field(default=None, description="编辑摘要")
    score: float = Field(default=0.0, description="相关性分数")

    # === Java 集成新增字段 ===
    latitude: float | None = Field(default=None, description="纬度")
    longitude: float | None = Field(default=None, description="经度")
    address: str = Field(default="", description="完整地址")


class SearchResponse(BaseModel):
    """Search 响应模型"""

    results: list[POIResultSchema] = Field(description="搜索结果")
    total: int = Field(description="结果总数")
    query: str = Field(description="原始查询")
    mode: str = Field(description="搜索模式")


# ===== Health API =====


class HealthResponse(BaseModel):
    """Health 响应模型"""

    status: str = Field(default="healthy", description="服务状态")
    version: str = Field(default="1.0.0", description="API 版本")


# ===== Testing API =====


class TestCollectRequest(BaseModel):
    """特征提取测试请求"""

    message: str = Field(description="用户消息")

    model_config = {
        "json_schema_extra": {"examples": [{"message": "I want to visit NYC for 3 days"}]}
    }


class TestCollectResponse(BaseModel):
    """特征提取测试响应"""

    user_features: dict[str, Any] = Field(description="提取的用户特征")
    extraction_success: bool = Field(description="提取是否成功")


class TestValidateRequest(BaseModel):
    """特征验证测试请求"""

    user_features: dict[str, Any] = Field(description="用户特征")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_features": {
                        "destination": "NYC",
                        "travel_days": 3,
                        "interests": ["history"],
                    }
                }
            ]
        }
    }


class TestValidateResponse(BaseModel):
    """特征验证测试响应"""

    feature_complete: bool = Field(description="核心特征是否完整")
    missing_features: list[str] = Field(description="缺失的字段列表")
    core_fields_status: dict[str, bool] = Field(description="核心字段状态")


class TestSearchRawRequest(BaseModel):
    """纯搜索测试请求"""

    query: str = Field(description="搜索查询")
    mode: Literal["balanced", "semantic", "keyword", "exact"] = Field(
        default="balanced", description="搜索模式"
    )
    top_k: int = Field(default=10, ge=1, le=100, description="返回结果数量")
    city: str | None = Field(default=None, description="城市过滤")
    use_rerank: bool = Field(default=True, description="是否使用 rerank")

    model_config = {
        "json_schema_extra": {
            "examples": [{"query": "museums in NYC", "mode": "balanced", "top_k": 5}]
        }
    }


class TestSearchRawResponse(BaseModel):
    """纯搜索测试响应"""

    results: list[POIResultSchema] = Field(description="搜索结果")
    total: int = Field(description="结果总数")
    search_mode: str = Field(description="搜索模式")
    weights: dict[str, float] = Field(description="搜索权重")
    rerank_applied: bool = Field(description="是否应用了 rerank")


class TestEvaluateRequest(BaseModel):
    """质量评估测试请求"""

    query: str = Field(description="查询文本")
    document: str = Field(description="待评估的文档内容")

    model_config = {
        "json_schema_extra": {
            "examples": [{"query": "historical sites", "document": "The Met is a famous museum..."}]
        }
    }


class TestEvaluateResponse(BaseModel):
    """质量评估测试响应"""

    binary_score: str = Field(description="评估结果 (yes/no)")
    reasoning: str = Field(description="评估理由")
    is_relevant: bool = Field(description="是否相关")


class TestRefineRequest(BaseModel):
    """查询修正测试请求"""

    original_query: str = Field(description="原始查询")
    error_type: Literal["too_few", "semantic_drift", "irrelevant"] = Field(description="错误类型")
    interests: list[str] = Field(default=[], description="用户兴趣")
    destination: str = Field(default="", description="目的地")
    tried_queries: list[str] = Field(default=[], description="已尝试的查询")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"original_query": "good places", "error_type": "too_few", "destination": "NYC"}
            ]
        }
    }


class TestRefineResponse(BaseModel):
    """查询修正测试响应"""

    refined_query: str = Field(description="修正后的查询")
    modification_reason: str = Field(description="修正原因")


class TestSearchCRAGRequest(BaseModel):
    """CRAG 搜索测试请求"""

    query: str = Field(description="搜索查询")
    user_features: dict[str, Any] | None = Field(default=None, description="用户特征")
    include_grading: bool = Field(default=True, description="是否启用质量评估")
    include_refiner: bool = Field(default=True, description="是否启用查询修正")
    include_fallback: bool = Field(default=False, description="是否启用 Fallback")
    max_retry: int = Field(default=1, ge=0, le=5, description="最大重试次数")

    model_config = {
        "json_schema_extra": {"examples": [{"query": "NYC museums", "include_fallback": False}]}
    }


class TestSearchCRAGResponse(BaseModel):
    """CRAG 搜索测试响应"""

    results: list[POIResultSchema] = Field(description="搜索结果")
    result_quality: str | None = Field(default=None, description="结果质量")
    retry_count: int = Field(default=0, description="重试次数")
    fallback_triggered: bool = Field(default=False, description="是否触发 Fallback")
    refined_query: str | None = Field(default=None, description="修正后的查询")


# ===== Java 集成模型 =====


class POIForExport(BaseModel):
    """导出到 Java 后端的 POI 结构"""

    id: str = Field(description="POI 唯一标识")
    name: str = Field(description="POI 名称")
    city: str | None = Field(default=None, description="城市")

    # 地理位置 - Java PlaceEntity 必需
    latitude: float = Field(description="纬度")
    longitude: float = Field(description="经度")
    address: str = Field(default="", description="完整地址")

    # 可选字段
    description: str | None = Field(default=None, description="POI 描述")
    image_url: str | None = Field(default=None, description="图片 URL")
    rating: float | None = Field(default=None, description="评分")
    primary_category: str | None = Field(default=None, description="分类")
    opening_hours: str | None = Field(default=None, description="营业时间")


class SuggestedStop(BaseModel):
    """行程中的单个停靠点"""

    poi_id: str = Field(description="关联 POIForExport.id")
    poi_name: str = Field(description="POI 名称")
    arrival_time: str = Field(description="到达时间 HH:MM")
    departure_time: str = Field(description="离开时间 HH:MM")
    duration_minutes: int = Field(description="停留时长（分钟）")
    activity: str | None = Field(default=None, description="活动描述")


class SuggestedDay(BaseModel):
    """单天行程"""

    date: str = Field(description="日期 YYYY-MM-DD")
    day_number: int = Field(description="第几天 (1-based)")
    theme: str | None = Field(default=None, description="当天主题")
    stops: list[SuggestedStop] = Field(default_factory=list, description="停靠点列表")


class SuggestedPlan(BaseModel):
    """AI 建议的完整行程"""

    destination: str = Field(description="目的地")
    start_date: str | None = Field(default=None, description="开始日期 YYYY-MM-DD")
    end_date: str | None = Field(default=None, description="结束日期 YYYY-MM-DD")
    total_days: int = Field(description="总天数")
    days: list[SuggestedDay] = Field(default_factory=list, description="每日行程")
