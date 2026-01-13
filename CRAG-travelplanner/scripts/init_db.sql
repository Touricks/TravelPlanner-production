-- ==========================================
-- CRAG Travel Planner - 数据库初始化脚本
-- 创建时间: 2026-01-03
-- 数据库: OceanBase 4.x+
-- ==========================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS crag_travelplanner
DEFAULT CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE crag_travelplanner;

-- ==========================================
-- POI主表（景点/餐厅/酒店等）
-- ==========================================
CREATE TABLE IF NOT EXISTS pois (
    -- 基础信息
    id VARCHAR(64) PRIMARY KEY COMMENT 'POI唯一标识',
    name VARCHAR(256) NOT NULL COMMENT 'POI名称',
    city VARCHAR(128) COMMENT '城市',
    state VARCHAR(64) COMMENT '州/省份',
    country VARCHAR(64) DEFAULT 'USA' COMMENT '国家',

    -- 地理位置
    latitude DECIMAL(10, 7) COMMENT '纬度',
    longitude DECIMAL(10, 7) COMMENT '经度',
    address TEXT COMMENT '详细地址',

    -- 评分与热度
    rating DECIMAL(2, 1) COMMENT '评分 (0-5)',
    reviews_count INT DEFAULT 0 COMMENT '评论数',
    popularity_score DECIMAL(5, 2) COMMENT '热度分数',

    -- 分类与属性
    primary_category VARCHAR(128) COMMENT '主分类',
    google_types JSON COMMENT 'Google Place类型数组',
    price_level VARCHAR(32) COMMENT '价格等级 (low/medium/high/luxury)',

    -- 营业信息
    business_hours JSON COMMENT '营业时间（JSON格式）',
    website VARCHAR(512) COMMENT '官网',
    phone VARCHAR(32) COMMENT '电话',

    -- 内容描述
    editorial_summary TEXT COMMENT '编辑摘要（用于检索）',
    description TEXT COMMENT '详细描述',

    -- 向量嵌入（1024维，Qwen text-embedding-v3）
    embedding VECTOR(1024) COMMENT '文本向量嵌入',

    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    data_source VARCHAR(64) DEFAULT 'manual' COMMENT '数据来源',

    -- 约束
    CONSTRAINT check_rating CHECK (rating >= 0 AND rating <= 5),
    CONSTRAINT check_latitude CHECK (latitude >= -90 AND latitude <= 90),
    CONSTRAINT check_longitude CHECK (longitude >= -180 AND longitude <= 180)
) COMMENT='POI主表';

-- ==========================================
-- 索引配置
-- ==========================================

-- 1. 向量索引（由langchain-oceanbase自动创建）
-- 注意：OceanBase向量索引通过langchain_oceanbase包自动管理
-- 不需要手动创建向量索引

-- 2. 地理位置索引
CREATE INDEX idx_pois_location ON pois (city, state, country)
COMMENT '地理位置过滤索引';

CREATE INDEX idx_pois_coordinates ON pois (latitude, longitude)
COMMENT '经纬度范围查询索引';

-- 3. 分类索引
CREATE INDEX idx_pois_category ON pois (primary_category)
COMMENT '分类过滤索引';

-- 4. 评分索引
CREATE INDEX idx_pois_rating ON pois (rating DESC)
COMMENT '按评分排序索引';

-- 5. 热度索引
CREATE INDEX idx_pois_popularity ON pois (popularity_score DESC)
COMMENT '按热度排序索引';

-- 6. 复合索引（城市+分类+评分）
CREATE INDEX idx_pois_city_cat_rating ON pois (city, primary_category, rating DESC)
COMMENT '常用查询组合索引';

-- 7. 全文索引（名称和摘要）
-- 注意：OceanBase 4.3+支持，如版本不支持请注释掉
-- CREATE FULLTEXT INDEX idx_pois_fulltext ON pois (name, editorial_summary)
-- COMMENT '全文检索索引';

-- ==========================================
-- 用户会话表（可选，用于记录用户交互）
-- ==========================================
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id VARCHAR(64) PRIMARY KEY COMMENT '会话ID',
    user_id VARCHAR(64) COMMENT '用户ID（可选）',

    -- 用户特征
    user_features JSON COMMENT '用户偏好特征（UserFeatures）',

    -- 会话状态
    state JSON COMMENT 'CRAGState快照',
    search_history JSON COMMENT '搜索历史',

    -- 统计信息
    total_queries INT DEFAULT 0 COMMENT '总查询次数',
    retry_count INT DEFAULT 0 COMMENT '重试次数',
    fallback_triggered BOOLEAN DEFAULT FALSE COMMENT '是否触发fallback',

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    expires_at TIMESTAMP COMMENT '过期时间（24小时后）',

    INDEX idx_user_id (user_id),
    INDEX idx_expires (expires_at)
) COMMENT='用户会话表';

-- ==========================================
-- 查询日志表（可选，用于分析和优化）
-- ==========================================
CREATE TABLE IF NOT EXISTS query_logs (
    log_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(64) COMMENT '关联会话',

    -- 查询信息
    query_text TEXT COMMENT '原始查询',
    refined_query TEXT COMMENT '修正后查询',
    search_mode VARCHAR(32) COMMENT '搜索模式',

    -- 结果评估
    result_quality VARCHAR(32) COMMENT 'good/poor/irrelevant',
    result_count INT COMMENT '返回结果数',
    error_type VARCHAR(32) COMMENT '错误类型（如有）',

    -- 性能指标
    latency_ms INT COMMENT '响应延迟（毫秒）',
    token_usage INT COMMENT 'Token消耗',

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_session (session_id),
    INDEX idx_quality (result_quality),
    INDEX idx_created (created_at)
) COMMENT='查询日志表';

-- ==========================================
-- 初始化完成提示
-- ==========================================
SELECT 'Database schema initialized successfully!' AS status;
SELECT COUNT(*) AS poi_count FROM pois;
SELECT TABLE_NAME, TABLE_ROWS, TABLE_COMMENT
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'crag_travelplanner';
