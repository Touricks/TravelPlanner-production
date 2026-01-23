"""
端到端集成测试 - LLM 辅助验证
==============================
测试真实 API 场景下 LLM 验证的行为

测试场景：
1. 用户发送初始请求
2. AI 询问 pois_per_day
3. 用户以简短数字回复 "3-4"
4. 验证 feature_complete 正确设置为 True

运行方式：
    # 需要先启动服务
    make start

    # 运行测试
    python tests/test_llm_validation_e2e.py

    # 或使用 pytest
    pytest tests/test_llm_validation_e2e.py -v -s

日期: 2026-01-22
"""

import json
import os
import sys
import time

import requests

# API 配置
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
CHAT_ENDPOINT = f"{API_BASE_URL}/api/v1/chat"


def log(msg: str) -> None:
    """打印带时间戳的日志"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")


def send_chat(session_id: str | None, message: str) -> dict:
    """
    发送聊天请求

    Args:
        session_id: 会话 ID，None 表示新会话
        message: 用户消息

    Returns:
        API 响应 dict
    """
    payload = {"message": message}
    if session_id:
        payload["session_id"] = session_id

    log(f">>> 发送: {message[:50]}..." if len(message) > 50 else f">>> 发送: {message}")

    response = requests.post(
        CHAT_ENDPOINT,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=180,  # 增加超时时间，搜索 POI 可能需要较长时间
    )

    if response.status_code != 200:
        log(f"!!! 错误: HTTP {response.status_code}")
        log(f"    响应: {response.text}")
        raise Exception(f"API error: {response.status_code}")

    data = response.json()
    log(f"<<< AI: {data['message'][:100]}..." if len(data["message"]) > 100 else f"<<< AI: {data['message']}")
    log(f"    feature_complete: {data.get('feature_complete')}")
    log(f"    user_features: {json.dumps(data.get('user_features'), ensure_ascii=False)[:200]}")

    return data


def test_short_reply_scenario():
    """
    测试场景：用户以简短数字回复确认 pois_per_day

    预期行为：
    - 用户说 "I want to visit Atlanta for 3 days"
    - AI 询问更多信息（interests, budget, etc.）
    - 用户回复 "history; mid-range about 30; car-rental;"
    - AI 询问 pois_per_day
    - 用户回复 "3-4" (简短数字)
    - feature_complete 应该为 True
    """
    log("=" * 60)
    log("测试场景: 简短数字回复确认 pois_per_day")
    log("=" * 60)

    # Step 1: 初始请求
    log("\n--- Step 1: 初始请求 ---")
    resp1 = send_chat(None, "I want to visit Atlanta for 3 days")
    session_id = resp1["session_id"]
    log(f"    新会话 ID: {session_id}")

    # feature_complete 应该是 False（缺少字段）
    assert resp1["feature_complete"] is False, "Step 1: feature_complete should be False"
    log("    ✓ feature_complete = False (预期)")

    # Step 2: 补充基本信息
    log("\n--- Step 2: 补充基本信息 ---")
    resp2 = send_chat(session_id, "history and food; mid-range about 30; car-rental;")

    # feature_complete 可能仍为 False（缺少 pois_per_day）
    log(f"    ✓ feature_complete = {resp2['feature_complete']}")

    # Step 3: 简短数字回复
    log("\n--- Step 3: 简短数字回复 '3-4' ---")
    resp3 = send_chat(session_id, "3-4; No must-see;")

    # 关键检查：feature_complete 应该为 True
    user_features = resp3.get("user_features", {})
    pois_per_day = user_features.get("pois_per_day") if user_features else None

    log(f"    pois_per_day: {pois_per_day}")
    log(f"    feature_complete: {resp3['feature_complete']}")

    # 验证结果
    if resp3["feature_complete"] is True:
        log("\n✅ 测试通过: 简短回复 '3-4' 正确识别为 pois_per_day 确认")
        return True
    else:
        log("\n❌ 测试失败: feature_complete 应该为 True")
        log(f"    missing_features 可能原因: pois_per_day={pois_per_day}")
        return False


def test_explicit_pois_mention():
    """
    测试场景：用户明确提到 POIs 数量

    预期行为：正则直接匹配，不需要 LLM 验证
    """
    log("=" * 60)
    log("测试场景: 明确提到 POIs 数量")
    log("=" * 60)

    # Step 1: 一次性提供所有信息
    log("\n--- Step 1: 提供完整信息（含明确 POIs 数量）---")
    resp = send_chat(
        None,
        "I want to visit Atlanta for 3 days. "
        "I like history and food. "
        "Budget is about $30 per meal. "
        "I'll rent a car. "
        "I want to see 3-4 POIs per day."
    )
    session_id = resp["session_id"]
    log(f"    新会话 ID: {session_id}")

    user_features = resp.get("user_features", {})
    pois_per_day = user_features.get("pois_per_day") if user_features else None

    log(f"    pois_per_day: {pois_per_day}")
    log(f"    feature_complete: {resp['feature_complete']}")

    if resp["feature_complete"] is True:
        log("\n✅ 测试通过: 明确 POIs 数量正确识别")
        return True
    else:
        log("\n❌ 测试失败: feature_complete 应该为 True")
        return False


def test_yes_confirmation():
    """
    测试场景：用户用 "yes" 确认 AI 建议

    这个场景更依赖 LLM 验证
    """
    log("=" * 60)
    log("测试场景: 用 'yes' 确认 AI 建议")
    log("=" * 60)

    # Step 1: 初始请求
    log("\n--- Step 1: 初始请求 ---")
    resp1 = send_chat(None, "Plan a 5 day trip to Miami")
    session_id = resp1["session_id"]
    log(f"    新会话 ID: {session_id}")

    # Step 2: 补充信息
    log("\n--- Step 2: 补充基本信息 ---")
    resp2 = send_chat(session_id, "beach and nightlife; $40 budget; I'll drive")

    # Step 3: 确认 AI 建议
    log("\n--- Step 3: 确认 AI 建议 ---")
    resp3 = send_chat(session_id, "yes, 4 per day sounds good")

    user_features = resp3.get("user_features", {})
    pois_per_day = user_features.get("pois_per_day") if user_features else None

    log(f"    pois_per_day: {pois_per_day}")
    log(f"    feature_complete: {resp3['feature_complete']}")

    if resp3["feature_complete"] is True:
        log("\n✅ 测试通过: 'yes' 确认正确识别")
        return True
    else:
        log("\n⚠️ 测试结果: feature_complete = False")
        log("    这可能是因为 AI 没有建议具体数量，或 LLM 未能确认")
        return False


def run_all_tests():
    """运行所有测试"""
    log("=" * 60)
    log("LLM 辅助验证 - 端到端集成测试")
    log("=" * 60)
    log(f"API 端点: {CHAT_ENDPOINT}")
    log("")

    # 检查服务是否可用
    try:
        health_check = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if health_check.status_code != 200:
            log("❌ 服务不可用，请先运行 'make start'")
            return False
    except requests.exceptions.ConnectionError:
        log("❌ 无法连接到服务，请先运行 'make start'")
        return False

    log("✓ 服务可用\n")

    results = []

    # 测试 1: 简短数字回复
    try:
        results.append(("短数字回复", test_short_reply_scenario()))
    except Exception as e:
        log(f"❌ 测试异常: {e}")
        results.append(("短数字回复", False))

    print()

    # 测试 2: 明确 POIs 提及
    try:
        results.append(("明确POIs提及", test_explicit_pois_mention()))
    except Exception as e:
        log(f"❌ 测试异常: {e}")
        results.append(("明确POIs提及", False))

    print()

    # 测试 3: Yes 确认
    try:
        results.append(("Yes确认", test_yes_confirmation()))
    except Exception as e:
        log(f"❌ 测试异常: {e}")
        results.append(("Yes确认", False))

    # 汇总
    log("\n" + "=" * 60)
    log("测试汇总")
    log("=" * 60)
    passed = 0
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        log(f"  {name}: {status}")
        if result:
            passed += 1

    log(f"\n总计: {passed}/{len(results)} 通过")

    return passed == len(results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
