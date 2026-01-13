"""直接测试通义千问Embedding API"""

import os

import requests
from dotenv import load_dotenv

load_dotenv()


def test_qwen_embedding():
    """直接调用通义千问Embedding API"""
    print("🔍 测试通义千问Embedding API (直接调用)...")

    api_key = os.getenv("EMBEDDING_API_KEY")
    model = os.getenv("EMBEDDING_MODEL", "text-embedding-v4")

    url = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # 通义千问Embedding API格式
    payload = {"model": model, "input": {"texts": ["测试文本"]}}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)

        if response.status_code == 200:
            result = response.json()
            embeddings = result["output"]["embeddings"]
            vector = embeddings[0]["embedding"]

            print("✅ Embedding API连接成功！")
            print(f"📊 向量维度: {len(vector)}")
            print(f"📊 向量示例（前5维）: {vector[:5]}")
            print(f"📊 请求ID: {result['request_id']}")
            return True
        else:
            print(f"❌ API返回错误: {response.status_code}")
            print(f"   {response.text}")
            return False

    except Exception as e:
        print(f"❌ 请求失败: {type(e).__name__}")
        print(f"   {str(e)}")
        return False


if __name__ == "__main__":
    success = test_qwen_embedding()
    exit(0 if success else 1)
