#!/usr/bin/env python3
"""
测试脚本：验证 Collector Prompt 修复效果
=========================================
测试用例：用户只提供目的地和天数，验证 LLM 不会脑补其他字段

运行方式：
    python tests/test_collector_fix.py
"""

import logging
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ruff: noqa: E402
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

# 加载环境变量
load_dotenv()

# 配置日志 - 显示 INFO 级别
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# 设置 seekdb_agent 模块的日志级别
logging.getLogger("seekdb_agent").setLevel(logging.INFO)


def test_tampa_itinerary():
    """测试用例：Recommend an 5-days itinerary for Tampa, FL"""
    from seekdb_agent.nodes.collector import collector_node
    from seekdb_agent.nodes.validator import validator_node

    print("\n" + "=" * 60)
    print("测试用例: Recommend an 5-days itinerary for Tampa, FL")
    print("=" * 60)

    # 构造输入状态
    state = {"messages": [HumanMessage(content="Recommend an 5-days itinerary for Tampa, FL")]}

    # 1. 执行 Collector
    print("\n--- Collector 执行 ---")
    collector_result = collector_node(state)
    user_features_raw = collector_result.get("user_features")
    # 转换为 dict（兼容 Pydantic BaseModel）
    if hasattr(user_features_raw, "model_dump"):
        user_features = user_features_raw.model_dump()
    else:
        user_features = dict(user_features_raw) if user_features_raw else {}

    print("\n提取的特征:")
    for key, value in dict(user_features).items():
        print(f"  {key}: {value}")

    # 2. 执行 Validator
    print("\n--- Validator 执行 ---")
    state_with_features = {**state, "user_features": user_features}
    validator_result = validator_node(state_with_features)

    print("\n验证结果:")
    print(f"  feature_complete: {validator_result.get('feature_complete')}")
    print(f"  missing_features: {validator_result.get('missing_features')}")

    # 3. 验证预期结果
    print("\n--- 验证预期 ---")

    # 预期：只有 destination 和 travel_days 有值
    expected_filled = ["destination", "travel_days"]
    expected_empty = ["interests", "budget_meal", "transportation", "pois_per_day"]

    success = True

    # 检查应该有值的字段
    for field in expected_filled:
        value = user_features.get(field)
        if value is None or value == "" or value == 0:
            print(f"  ❌ {field} 应该有值，但是: {value}")
            success = False
        else:
            print(f"  ✅ {field} = {value}")

    # 检查应该为空的字段
    for field in expected_empty:
        value = user_features.get(field)
        is_empty = (
            value is None
            or value == ""
            or value == 0
            or (isinstance(value, list) and len(value) == 0)
        )
        if not is_empty:
            print(f"  ❌ {field} 应该为空，但是: {value} (LLM 脑补了!)")
            success = False
        else:
            print(f"  ✅ {field} = {value} (正确为空)")

    # 检查 feature_complete 应该为 False
    if validator_result.get("feature_complete"):
        print("  ❌ feature_complete 应该为 False，但是: True")
        success = False
    else:
        print("  ✅ feature_complete = False (正确)")

    print("\n" + "=" * 60)
    if success:
        print("✅ 测试通过！LLM 没有脑补缺失字段")
    else:
        print("❌ 测试失败！LLM 仍在脑补缺失字段")
    print("=" * 60)

    return success


def test_beijing_history():
    """测试用例：我想去北京，对历史感兴趣"""
    from seekdb_agent.nodes.collector import collector_node
    from seekdb_agent.nodes.validator import validator_node

    print("\n" + "=" * 60)
    print("测试用例: 我想去北京，对历史感兴趣")
    print("=" * 60)

    state = {"messages": [HumanMessage(content="我想去北京，对历史感兴趣")]}

    # 执行 Collector
    print("\n--- Collector 执行 ---")
    collector_result = collector_node(state)
    user_features_raw = collector_result.get("user_features")
    # 转换为 dict（兼容 Pydantic BaseModel）
    if hasattr(user_features_raw, "model_dump"):
        user_features = user_features_raw.model_dump()
    else:
        user_features = dict(user_features_raw) if user_features_raw else {}

    print("\n提取的特征:")
    for key, value in dict(user_features).items():
        print(f"  {key}: {value}")

    # 执行 Validator
    print("\n--- Validator 执行 ---")
    state_with_features = {**state, "user_features": user_features}
    validator_result = validator_node(state_with_features)

    print("\n验证结果:")
    print(f"  feature_complete: {validator_result.get('feature_complete')}")
    print(f"  missing_features: {validator_result.get('missing_features')}")

    # 验证预期
    print("\n--- 验证预期 ---")

    success = True

    # destination 应该有值
    if not user_features.get("destination"):
        print("  ❌ destination 应该有值")
        success = False
    else:
        print(f"  ✅ destination = {user_features.get('destination')}")

    # interests 应该包含历史相关
    interests = user_features.get("interests", [])
    if not interests:
        print("  ❌ interests 应该有值")
        success = False
    else:
        print(f"  ✅ interests = {interests}")

    # travel_days 应该为空
    if user_features.get("travel_days"):
        print(f"  ❌ travel_days 应该为空，但是: {user_features.get('travel_days')}")
        success = False
    else:
        print("  ✅ travel_days = None (正确为空)")

    # budget_meal 应该为空
    if user_features.get("budget_meal"):
        print(f"  ❌ budget_meal 应该为空，但是: {user_features.get('budget_meal')}")
        success = False
    else:
        print("  ✅ budget_meal = None (正确为空)")

    print("\n" + "=" * 60)
    if success:
        print("✅ 测试通过！")
    else:
        print("❌ 测试失败！")
    print("=" * 60)

    return success


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Collector Prompt 修复验证测试")
    print("=" * 60)

    results = []

    # 运行测试
    results.append(("Tampa 5-day itinerary", test_tampa_itinerary()))
    results.append(("北京历史", test_beijing_history()))

    # 汇总结果
    print("\n\n" + "=" * 60)
    print("测试汇总")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("所有测试通过！")
        sys.exit(0)
    else:
        print("部分测试失败！")
        sys.exit(1)
