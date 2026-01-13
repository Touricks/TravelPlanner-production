"""
Performance Benchmark Tests
===========================
Day 9 性能测试实现

测试指标:
- E2E延迟（无重试）: < 5s
- E2E延迟（含重试）: < 10s
- Recall@20: ≥ 0.75
- 质量检测准确率: ≥ 0.85
- 幻觉率: ≤ 10%
- Validator拦截率: ≥ 80%
- 误报率: ≤ 10%

运行方式:
    pytest tests/test_performance.py -v -m performance
"""

import json
import logging
import time
from pathlib import Path
from typing import Any

import pytest
from langchain_core.messages import HumanMessage
from tqdm import tqdm

from seekdb_agent.graph import create_crag_graph
from seekdb_agent.nodes import collector_node, validator_node

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# 测试数据
# ============================================================

TEST_QUERIES = [
    # 具体目的地 (5条)
    {
        "query": "I want to visit museums in Tampa",
        "city": "Tampa",
        "expected_categories": ["museum"],
    },
    {"query": "Best beaches near Miami", "city": "Miami", "expected_categories": ["beach", "park"]},
    {"query": "Parks in Tampa for family", "city": "Tampa", "expected_categories": ["park"]},
    {
        "query": "Entertainment in Tampa",
        "city": "Tampa",
        "expected_categories": ["casino", "entertainment"],
    },
    {
        "query": "Historical sites in Tampa",
        "city": "Tampa",
        "expected_categories": ["historical", "museum"],
    },
    # 模糊偏好 (3条)
    {
        "query": "Romantic getaway spots",
        "city": None,
        "expected_categories": ["park", "restaurant"],
    },
    {
        "query": "Family friendly attractions",
        "city": None,
        "expected_categories": ["park", "museum"],
    },
    {"query": "Outdoor activities", "city": None, "expected_categories": ["park", "outdoor"]},
    # 边界测试 (2条)
    {"query": "Tourist spots", "city": None, "expected_categories": []},
    {"query": "Things to do", "city": None, "expected_categories": []},
]

# 精简版测试用例 (5条) - 适应 Google API 60/min 限制
HALLUCINATION_TEST_CASES = [
    {
        "query": "I want to visit New York",
        "expected": {"destination": "New York"},
        "should_be_none": ["travel_days", "budget_meal", "transportation", "pois_per_day"],
        "description": "只提供目的地，其他字段应为空",
    },
    {
        "query": "Planning a trip to LA for 5 days",
        "expected": {"destination": "Los Angeles", "travel_days": 5},
        "should_be_none": ["budget_meal", "transportation", "pois_per_day"],
        "description": "只提供目的地和天数",
    },
    {
        "query": "I like museums and art galleries",
        "expected": {"interests": ["museums", "art galleries"]},
        "should_be_none": ["destination", "travel_days", "budget_meal", "transportation"],
        "description": "只提供兴趣，无目的地",
    },
    {
        "query": "travel",
        "expected": {},
        "should_be_none": [
            "destination",
            "travel_days",
            "budget_meal",
            "transportation",
            "pois_per_day",
        ],
        "description": "极简输入，不应提取任何具体信息",
    },
    {
        "query": "help me plan",
        "expected": {},
        "should_be_none": [
            "destination",
            "travel_days",
            "budget_meal",
            "transportation",
            "pois_per_day",
        ],
        "description": "无实质信息，全部应为空",
    },
]

# 精简版测试用例 (5条) - 适应 API 限制
GRADING_TEST_CASES = [
    (
        "museums in Tampa",
        "The Tampa Bay History Center is a museum dedicated to the history of Tampa Bay region.",
        True,
    ),
    (
        "beaches in Miami",
        "Historic Virginia Key Beach Park is a popular beach destination in Miami.",
        True,
    ),
    ("museums in Tampa", "Best pizza restaurants in Chicago with great reviews.", False),
    ("hiking trails", "Indoor shopping mall with many stores and entertainment.", False),
    (
        "parks in Tampa",
        "Lettuce Lake Park offers nature trails and wildlife viewing in Tampa.",
        True,
    ),
]


def _is_empty(value: Any) -> bool:
    """判断值是否为空"""
    if value is None:
        return True
    if value == "":
        return True
    if value == 0:
        return True
    if isinstance(value, list) and len(value) == 0:
        return True
    return False


def _get_features_dict(features: Any) -> dict[str, Any]:
    """将 UserFeatures 转换为字典"""
    if features is None:
        return {}
    if isinstance(features, dict):
        return features
    if hasattr(features, "model_dump"):
        return features.model_dump()
    return dict(features)


# ============================================================
# E2E 延迟测试
# ============================================================


class TestE2ELatency:
    """E2E 延迟测试"""

    @pytest.fixture
    def graph_no_retry(self):
        """无重试配置"""
        return create_crag_graph(
            include_grading=True,
            include_refiner=False,
            include_fallback=False,
            max_retry=0,
        )

    @pytest.fixture
    def graph_with_retry(self):
        """含重试配置"""
        return create_crag_graph(
            include_grading=True,
            include_refiner=True,
            include_fallback=True,
            max_retry=2,
        )

    @pytest.mark.performance
    def test_latency_no_retry(self, graph_no_retry):
        """无重试延迟 < 5s (测试3条查询)"""
        latencies = []

        for test_case in tqdm(TEST_QUERIES[:3], desc="E2E Latency (No Retry)"):
            state = {
                "messages": [HumanMessage(content=test_case["query"])],
                "user_features": None,
                "feature_complete": True,
                "missing_features": [],
            }

            start = time.perf_counter()
            try:
                graph_no_retry.invoke(state)
            except Exception as e:
                logger.warning(f"Graph invoke failed: {e}")
            elapsed = time.perf_counter() - start
            latencies.append(elapsed)
            tqdm.write(f"  {test_case['query'][:30]}... {elapsed:.2f}s")

        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        max_latency = max(latencies) if latencies else 0

        print("\n=== E2E Latency (No Retry) ===")
        print(f"Queries tested: {len(latencies)}")
        print(f"Average latency: {avg_latency:.2f}s")
        print(f"Max latency: {max_latency:.2f}s")
        print("Target: < 5.0s")

        assert avg_latency < 5.0, f"平均延迟 {avg_latency:.2f}s 超过 5s"

    @pytest.mark.performance
    def test_latency_with_retry(self, graph_with_retry):
        """含重试延迟 < 10s (测试2条查询)"""
        latencies = []

        for test_case in tqdm(TEST_QUERIES[:2], desc="E2E Latency (With Retry)"):
            state = {
                "messages": [HumanMessage(content=test_case["query"])],
                "user_features": None,
                "feature_complete": True,
                "missing_features": [],
            }

            start = time.perf_counter()
            try:
                graph_with_retry.invoke(state)
            except Exception as e:
                logger.warning(f"Graph invoke failed: {e}")
            elapsed = time.perf_counter() - start
            latencies.append(elapsed)
            tqdm.write(f"  {test_case['query'][:30]}... {elapsed:.2f}s")

        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        max_latency = max(latencies) if latencies else 0

        print("\n=== E2E Latency (With Retry) ===")
        print(f"Queries tested: {len(latencies)}")
        print(f"Average latency: {avg_latency:.2f}s")
        print(f"Max latency: {max_latency:.2f}s")
        print("Target: < 10.0s")

        assert avg_latency < 10.0, f"平均延迟 {avg_latency:.2f}s 超过 10s"


# ============================================================
# 搜索召回率测试
# ============================================================


class TestSearchRecall:
    """搜索召回率测试"""

    @pytest.fixture
    def ground_truth(self):
        """加载标注数据"""
        gt_path = Path(__file__).parent.parent / "data" / "test_ground_truth.json"
        if not gt_path.exists():
            pytest.skip("Ground truth file not found")
        with open(gt_path) as f:
            return json.load(f)

    @pytest.mark.performance
    def test_recall_at_20(self, ground_truth):
        """Recall@20 >= 0.75"""
        from seekdb_agent.db.connection import get_hybrid_store
        from seekdb_agent.db.search import hybrid_search

        try:
            store = get_hybrid_store()
        except Exception as e:
            pytest.skip(f"Database connection failed: {e}")

        recalls = []
        details = []

        for case in tqdm(ground_truth, desc="Recall@20"):
            query = case["query"]
            relevant_ids = set(case["relevant_poi_ids"])

            try:
                results = hybrid_search(
                    store=store,
                    query=query,
                    top_k=20,
                    search_mode="balanced",
                )
                retrieved_ids = {poi.id for poi in results}
                hits = len(retrieved_ids & relevant_ids)
                recall = hits / len(relevant_ids) if relevant_ids else 0
                recalls.append(recall)
                details.append(
                    {
                        "query": query,
                        "relevant": len(relevant_ids),
                        "retrieved": len(retrieved_ids),
                        "hits": hits,
                        "recall": recall,
                    }
                )
            except Exception as e:
                logger.warning(f"Search failed for '{query}': {e}")
                recalls.append(0)

        avg_recall = sum(recalls) / len(recalls) if recalls else 0

        print("\n=== Search Recall@20 ===")
        print(f"Queries tested: {len(recalls)}")
        for d in details:
            print(f"  {d['query'][:30]}: {d['hits']}/{d['relevant']} = {d['recall']:.2f}")
        print(f"Average Recall@20: {avg_recall:.2f}")
        print("Target: >= 0.75")

        assert avg_recall >= 0.75, f"Recall@20 {avg_recall:.2f} 低于 0.75"


# ============================================================
# 质量检测准确率测试
# ============================================================


class TestGradingAccuracy:
    """质量检测准确率测试"""

    @pytest.mark.performance
    def test_grading_accuracy(self):
        """质量检测准确率 >= 0.85"""
        from seekdb_agent.llm import get_cached_llm
        from seekdb_agent.middleware.grading import create_grader

        try:
            llm = get_cached_llm(temperature=0.0)
            grader = create_grader(llm)
        except Exception as e:
            pytest.skip(f"LLM initialization failed: {e}")

        correct = 0
        total = len(GRADING_TEST_CASES)
        details = []

        for query, document, expected in tqdm(GRADING_TEST_CASES, desc="Grading Accuracy"):
            try:
                result = grader.invoke(
                    {
                        "question": query,
                        "document": document[:500],
                        "must_visit": "无",  # 测试场景无 must_visit 要求
                    }
                )

                if result is None or not hasattr(result, "binary_score"):
                    logger.warning(f"Grader returned None for '{query}'")
                    continue

                is_relevant = result.binary_score.lower() == "yes"
                is_correct = is_relevant == expected

                if is_correct:
                    correct += 1

                details.append(
                    {
                        "query": query[:30],
                        "expected": expected,
                        "predicted": is_relevant,
                        "correct": is_correct,
                    }
                )
            except Exception as e:
                logger.warning(f"Grading failed for '{query}': {e}")

        accuracy = correct / total if total > 0 else 0

        print("\n=== Grading Accuracy ===")
        print(f"Total cases: {total}")
        print(f"Correct: {correct}")
        for d in details:
            status = "✓" if d["correct"] else "✗"
            print(f"  {status} {d['query']}: expected={d['expected']}, predicted={d['predicted']}")
        print(f"Accuracy: {accuracy:.2%}")
        print("Target: >= 85%")

        assert accuracy >= 0.85, f"准确率 {accuracy:.2%} 低于 85%"


# ============================================================
# LLM 幻觉检测测试 (合并版 - 复用 collector 结果减少 API 调用)
# ============================================================


class TestHallucinationDetection:
    """LLM 幻觉检测测试 - 合并为单个测试减少 API 调用"""

    @pytest.mark.performance
    def test_hallucination_combined(self):
        """
        合并测试: 幻觉率 + Validator拦截率 + 误报率

        只调用一次 collector_node，复用结果计算所有指标。
        适应 Google API 60/min 限制。
        """
        # 统计变量
        total_fields_checked = 0
        hallucinated_fields = 0
        field_stats: dict[str, dict[str, int]] = {}
        caught_hallucinations = 0
        missed_hallucinations = 0
        false_positives = 0
        total_expected_fields = 0

        # 缓存 collector 结果
        cached_results: list[dict[str, Any]] = []

        # Step 1: 调用 collector_node (只调用一次)
        print("\n[1/3] 调用 Collector 提取特征...")
        for case in tqdm(HALLUCINATION_TEST_CASES, desc="Collector (Gemini)"):
            try:
                state = {"messages": [HumanMessage(content=case["query"])]}
                collector_result = collector_node(state)
                state.update(collector_result)

                # Validator 验证 (不调用 LLM)
                validator_result = validator_node(state)

                cached_results.append(
                    {
                        "case": case,
                        "features": state.get("user_features"),
                        "missing_features": validator_result.get("missing_features", []),
                    }
                )
            except Exception as e:
                logger.warning(f"Collector failed for '{case['query']}': {e}")
                cached_results.append({"case": case, "features": None, "missing_features": []})

        # Step 2: 分析幻觉率
        print("\n[2/3] 计算幻觉率...")
        for item in cached_results:
            case = item["case"]
            features = item["features"]
            features_dict = _get_features_dict(features)

            for field in case["should_be_none"]:
                total_fields_checked += 1
                value = features_dict.get(field)

                if field not in field_stats:
                    field_stats[field] = {"total": 0, "hallucinated": 0}
                field_stats[field]["total"] += 1

                if not _is_empty(value):
                    hallucinated_fields += 1
                    field_stats[field]["hallucinated"] += 1

        # Step 3: 分析 Validator 拦截率
        print("[3/3] 计算 Validator 拦截率和误报率...")
        for item in cached_results:
            case = item["case"]
            features = item["features"]
            features_dict = _get_features_dict(features)
            missing_features = item["missing_features"]

            # Validator 拦截率
            for field in case["should_be_none"]:
                value = features_dict.get(field)
                if not _is_empty(value):
                    if field in missing_features:
                        caught_hallucinations += 1
                    else:
                        missed_hallucinations += 1

            # 误报率
            if case["expected"]:
                for field in case["expected"].keys():
                    total_expected_fields += 1
                    if field in missing_features:
                        false_positives += 1

        # 计算指标
        hallucination_rate = (
            hallucinated_fields / total_fields_checked if total_fields_checked > 0 else 0
        )
        total_hall = caught_hallucinations + missed_hallucinations
        catch_rate = caught_hallucinations / total_hall if total_hall > 0 else 1.0
        fp_rate = false_positives / total_expected_fields if total_expected_fields > 0 else 0

        # 输出报告
        print("\n" + "=" * 50)
        print("=== Hallucination Detection (Combined) ===")
        print("=" * 50)

        print("\n[幻觉率]")
        print(f"  Total fields checked: {total_fields_checked}")
        print(f"  Hallucinated fields: {hallucinated_fields}")
        print(f"  Hallucination rate: {hallucination_rate:.2%}")
        print("  Target: <= 10%")
        print(f"  Status: {'PASS' if hallucination_rate <= 0.10 else 'FAIL'}")

        print("\n[字段级统计]")
        for field, stats in field_stats.items():
            rate = stats["hallucinated"] / stats["total"] if stats["total"] > 0 else 0
            print(f"  {field}: {stats['hallucinated']}/{stats['total']} ({rate:.2%})")

        print("\n[Validator 拦截率]")
        print(f"  Caught: {caught_hallucinations}")
        print(f"  Missed: {missed_hallucinations}")
        print(f"  Catch rate: {catch_rate:.2%}")
        print("  Target: >= 80%")
        print(f"  Status: {'PASS' if catch_rate >= 0.80 else 'FAIL'}")

        print("\n[误报率]")
        print(f"  Total expected fields: {total_expected_fields}")
        print(f"  False positives: {false_positives}")
        print(f"  FP rate: {fp_rate:.2%}")
        print("  Target: <= 10%")
        print(f"  Status: {'PASS' if fp_rate <= 0.10 else 'FAIL'}")

        print("=" * 50)

        # 断言
        assert hallucination_rate <= 0.10, f"幻觉率 {hallucination_rate:.2%} 高于 10%"
        assert catch_rate >= 0.80, f"Validator 拦截率 {catch_rate:.2%} 低于 80%"
        assert fp_rate <= 0.10, f"误报率 {fp_rate:.2%} 高于 10%"


# ============================================================
# 综合报告测试
# ============================================================


class TestBenchmarkReport:
    """综合报告生成"""

    @pytest.mark.performance
    def test_generate_report(self):
        """生成测试报告摘要"""
        print(f"\n{'='*60}")
        print("BENCHMARK REPORT - Day 9 Performance Tests")
        print(f"{'='*60}")
        print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nTest Configuration:")
        print(f"  - E2E Latency queries: {len(TEST_QUERIES)}")
        print(f"  - Hallucination cases: {len(HALLUCINATION_TEST_CASES)}")
        print(f"  - Grading cases: {len(GRADING_TEST_CASES)}")
        print("\nTargets:")
        print("  - E2E Latency (no retry): < 5s")
        print("  - E2E Latency (with retry): < 10s")
        print("  - Recall@20: >= 0.75")
        print("  - Grading Accuracy: >= 85%")
        print("  - Hallucination Rate: <= 10%")
        print("  - Validator Catch Rate: >= 80%")
        print("  - False Positive Rate: <= 10%")
        print(f"{'='*60}")

        # 这是一个报告测试，总是通过
        assert True
