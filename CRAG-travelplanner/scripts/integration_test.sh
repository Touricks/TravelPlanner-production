#!/bin/bash
# ============================================================================
# CRAG -> Java 端到端集成测试脚本
# ============================================================================
# 日期: 2026-01-09
# 描述: 测试 CRAG 对话 -> plan_ready -> save -> Java 持久化 的完整流程
#
# 前置条件:
# - PostgreSQL 运行在 5434
# - Java 后端运行在 8080
# - CRAG 服务运行在 8000
# ============================================================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
JAVA_API="${JAVA_API:-http://localhost:8080}"
CRAG_API="${CRAG_API:-http://localhost:8000}"
TEST_EMAIL="${TEST_EMAIL:-integration-test@example.com}"
TEST_PASSWORD="${TEST_PASSWORD:-TestPassword123!}"

echo "=============================================="
echo "CRAG -> Java 集成测试"
echo "=============================================="
echo "Java API: $JAVA_API"
echo "CRAG API: $CRAG_API"
echo "Test User: $TEST_EMAIL"
echo ""

# 函数: 打印步骤
step() {
    echo ""
    echo -e "${YELLOW}=== $1 ===${NC}"
}

# 函数: 成功消息
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# 函数: 失败消息
fail() {
    echo -e "${RED}✗ $1${NC}"
    exit 1
}

# ============================================================================
# Step 0: 健康检查
# ============================================================================
step "0. 服务健康检查"

# CRAG 健康检查
CRAG_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$CRAG_API/health" || echo "000")
if [ "$CRAG_HEALTH" = "200" ]; then
    success "CRAG 服务正常 ($CRAG_API)"
else
    fail "CRAG 服务不可用 (HTTP $CRAG_HEALTH)"
fi

# Java 健康检查
JAVA_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$JAVA_API/actuator/health" || echo "000")
if [ "$JAVA_HEALTH" = "200" ]; then
    success "Java 服务正常 ($JAVA_API)"
else
    echo -e "${YELLOW}⚠ Java 健康检查返回 $JAVA_HEALTH (可能是路径不同)${NC}"
fi

# ============================================================================
# Step 1: 注册测试用户
# ============================================================================
step "1. 注册测试用户"

REGISTER_RESPONSE=$(curl -s -X POST "$JAVA_API/api/auth/register" \
    -H "Content-Type: application/json" \
    -d "{
        \"email\": \"$TEST_EMAIL\",
        \"password\": \"$TEST_PASSWORD\",
        \"role\": \"USER\"
    }" 2>&1)

# 检查是否已存在或成功注册
if echo "$REGISTER_RESPONSE" | grep -q "already exists\|success\|token\|201"; then
    success "用户注册完成 (可能已存在)"
    echo "Response: $REGISTER_RESPONSE" | head -c 200
else
    echo "Response: $REGISTER_RESPONSE"
    echo -e "${YELLOW}⚠ 注册响应: 继续尝试登录...${NC}"
fi

# ============================================================================
# Step 2: 登录获取 JWT Token
# ============================================================================
step "2. 登录获取 JWT Token"

LOGIN_RESPONSE=$(curl -s -X POST "$JAVA_API/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{
        \"email\": \"$TEST_EMAIL\",
        \"password\": \"$TEST_PASSWORD\"
    }" 2>&1)

# 提取 token (支持多种格式)
TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
if [ -z "$TOKEN" ]; then
    TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"accessToken":"[^"]*"' | cut -d'"' -f4)
fi

if [ -z "$TOKEN" ]; then
    echo "Login Response: $LOGIN_RESPONSE"
    fail "无法获取 JWT Token"
fi

success "JWT Token 获取成功"
echo "Token: ${TOKEN:0:50}..."

# ============================================================================
# Step 3: CRAG 冷启动对话
# ============================================================================
step "3. CRAG 冷启动对话"

COLD_START=$(curl -s -X POST "$CRAG_API/api/v1/chat" \
    -H "Content-Type: application/json" \
    -d '{"message": ""}')

SESSION_ID=$(echo "$COLD_START" | grep -o '"session_id":"[^"]*"' | cut -d'"' -f4)
if [ -z "$SESSION_ID" ]; then
    echo "Response: $COLD_START"
    fail "无法创建会话"
fi

success "会话创建成功: $SESSION_ID"
GREETING=$(echo "$COLD_START" | grep -o '"message":"[^"]*"' | cut -d'"' -f4 | head -c 100)
echo "AI 问候: $GREETING..."

# ============================================================================
# Step 4: 提供旅行需求
# ============================================================================
step "4. 提供旅行需求"

CHAT_1=$(curl -s -X POST "$CRAG_API/api/v1/chat" \
    -H "Content-Type: application/json" \
    -d "{
        \"session_id\": \"$SESSION_ID\",
        \"message\": \"I want to visit New York City for exactly 3 days. I love museums and history. My meal budget is around \$50 per meal, I prefer walking as transportation, and I want to see about 5 attractions per day.\"
    }")

FEATURE_COMPLETE_1=$(echo "$CHAT_1" | grep -o '"feature_complete":[^,}]*' | cut -d':' -f2)
PLAN_READY_1=$(echo "$CHAT_1" | grep -o '"plan_ready":[^,}]*' | cut -d':' -f2)

success "对话轮次 1 完成"
echo "feature_complete: $FEATURE_COMPLETE_1"
echo "plan_ready: $PLAN_READY_1"

# ============================================================================
# Step 5: 检查是否需要更多信息
# ============================================================================
step "5. 补充更多信息 (如需要)"

if [ "$FEATURE_COMPLETE_1" != "true" ] && [ "$PLAN_READY_1" != "true" ]; then
    CHAT_2=$(curl -s -X POST "$CRAG_API/api/v1/chat" \
        -H "Content-Type: application/json" \
        -d "{
            \"session_id\": \"$SESSION_ID\",
            \"message\": \"Yes, my budget is \$40-60 per meal. I will be walking everywhere. I want to visit exactly 5 places each day.\"
        }")

    FEATURE_COMPLETE_2=$(echo "$CHAT_2" | grep -o '"feature_complete":[^,}]*' | cut -d':' -f2)
    PLAN_READY_2=$(echo "$CHAT_2" | grep -o '"plan_ready":[^,}]*' | cut -d':' -f2)

    success "对话轮次 2 完成"
    echo "feature_complete: $FEATURE_COMPLETE_2"
    echo "plan_ready: $PLAN_READY_2"

    # 第三轮：如果仍不完整，再补充信息
    if [ "$FEATURE_COMPLETE_2" != "true" ] && [ "$PLAN_READY_2" != "true" ]; then
        CHAT_3=$(curl -s -X POST "$CRAG_API/api/v1/chat" \
            -H "Content-Type: application/json" \
            -d "{
                \"session_id\": \"$SESSION_ID\",
                \"message\": \"I confirm: destination is New York, 3 days, interested in museums and history, meal budget is high (\$50+), walking transportation, 5 POIs per day.\"
            }")

        FEATURE_COMPLETE_3=$(echo "$CHAT_3" | grep -o '"feature_complete":[^,}]*' | cut -d':' -f2)
        PLAN_READY_3=$(echo "$CHAT_3" | grep -o '"plan_ready":[^,}]*' | cut -d':' -f2)

        success "对话轮次 3 完成"
        echo "feature_complete: $FEATURE_COMPLETE_3"
        echo "plan_ready: $PLAN_READY_3"
    fi
fi

# ============================================================================
# Step 6: 触发 search_agent -> generator 流程
# ============================================================================
step "6. 触发计划生成 (确认可选字段)"

# 发送消息以触发 search_agent 流程
# 这里需要用户再次输入，因为 optional_asked 已经设置
FINAL_CHAT=$(curl -s -X POST "$CRAG_API/api/v1/chat" \
    -H "Content-Type: application/json" \
    -d "{
        \"session_id\": \"$SESSION_ID\",
        \"message\": \"Yes, I don't have any must-visit places besides MET. No dietary restrictions. Please generate my travel plan now.\"
    }")

FINAL_PLAN_READY=$(echo "$FINAL_CHAT" | grep -o '"plan_ready":[^,}]*' | cut -d':' -f2)
POIS_COUNT=$(echo "$FINAL_CHAT" | grep -o '"recommended_pois":\[' | wc -l)
HAS_PLAN=$(echo "$FINAL_CHAT" | grep -o '"suggested_plan":{' | wc -l)

echo "plan_ready: $FINAL_PLAN_READY"
echo "has_pois: $POIS_COUNT"
echo "has_plan: $HAS_PLAN"

if [ "$FINAL_PLAN_READY" = "true" ]; then
    success "计划已就绪，可以保存"
else
    echo -e "${YELLOW}⚠ plan_ready 不为 true，但继续测试 save 接口...${NC}"
fi

# ============================================================================
# Step 7: 保存计划到 Java 后端
# ============================================================================
step "7. 保存计划到 Java 后端"

SAVE_RESPONSE=$(curl -s -X POST "$CRAG_API/api/v1/session/$SESSION_ID/save" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json")

SAVE_STATUS=$(echo "$SAVE_RESPONSE" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
ITINERARY_ID=$(echo "$SAVE_RESPONSE" | grep -o '"itinerary_id":"[^"]*"' | cut -d'"' -f4)

echo "Save Response: $SAVE_RESPONSE"

if [ "$SAVE_STATUS" = "success" ]; then
    success "计划保存成功!"
    echo "Itinerary ID: $ITINERARY_ID"
else
    echo -e "${RED}保存失败: $SAVE_RESPONSE${NC}"
fi

# ============================================================================
# Step 8: 验证数据库 (如果有 docker)
# ============================================================================
step "8. 验证数据库记录"

if command -v docker &> /dev/null; then
    echo "尝试查询 PostgreSQL..."

    DB_RESULT=$(docker exec aitripplanner-db-1 psql -U postgres -d TravelPlanner \
        -c "SELECT id, destination_city, created_at FROM itineraries ORDER BY created_at DESC LIMIT 1;" 2>&1 || echo "查询失败")

    echo "$DB_RESULT"

    if echo "$DB_RESULT" | grep -q "row"; then
        success "数据库记录验证完成"
    else
        echo -e "${YELLOW}⚠ 无法验证数据库记录${NC}"
    fi
else
    echo "Docker 未安装，跳过数据库验证"
fi

# ============================================================================
# 测试总结
# ============================================================================
step "测试总结"

echo ""
echo "=============================================="
echo "测试结果"
echo "=============================================="
echo "Session ID: $SESSION_ID"
echo "Plan Ready: $FINAL_PLAN_READY"
echo "Save Status: $SAVE_STATUS"
echo "Itinerary ID: $ITINERARY_ID"
echo ""

if [ "$SAVE_STATUS" = "success" ]; then
    echo -e "${GREEN}=============================================="
    echo "集成测试通过!"
    echo "==============================================${NC}"
    exit 0
else
    echo -e "${YELLOW}=============================================="
    echo "集成测试部分完成 (请检查上述输出)"
    echo "==============================================${NC}"
    exit 1
fi
