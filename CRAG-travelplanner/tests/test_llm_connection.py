"""测试LLM API连接"""

import os
import sys

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# 加载.env文件
load_dotenv()


def test_qwen():
    """测试通义千问API"""
    print("🔍 正在测试通义千问API连接...")
    print(f"Model: {os.getenv('QWEN_MODEL')}")
    print(f"Base URL: {os.getenv('QWEN_BASE_URL')}")
    print("-" * 50)

    try:
        llm = ChatOpenAI(
            model=os.getenv("QWEN_MODEL", "qwen-plus"),
            api_key=os.getenv("QWEN_API_KEY"),
            base_url=os.getenv("QWEN_BASE_URL"),
            temperature=0,
        )

        # 测试简单调用
        response = llm.invoke("请回复'OK'")
        print("✅ 通义千问连接成功！")
        print(f"📝 响应: {response.content}\n")
        return True

    except Exception as e:
        print(f"❌ 通义千问连接失败: {type(e).__name__}")
        print(f"   {str(e)}")
        print("\n💡 解决方案:")
        print("   1. 访问 https://dashscope.aliyun.com/")
        print("   2. 注册/登录阿里云账号")
        print("   3. 在控制台创建API Key")
        print("   4. 将API Key填入.env文件的QWEN_API_KEY字段")
        return False


def test_embedding():
    """测试Embedding API"""
    print("🔍 正在测试Embedding API...")
    print(f"Model: {os.getenv('EMBEDDING_MODEL')}")
    print("-" * 50)

    try:
        from langchain_openai import OpenAIEmbeddings

        embeddings = OpenAIEmbeddings(
            model=os.getenv("EMBEDDING_MODEL", "text-embedding-v3"),
            api_key=os.getenv("EMBEDDING_API_KEY"),
            base_url=os.getenv("EMBEDDING_BASE_URL"),
        )

        # 测试向量生成
        test_text = "测试文本"
        vector = embeddings.embed_query(test_text)

        print("✅ Embedding API连接成功！")
        print(f"📊 向量维度: {len(vector)}")
        print(f"📊 向量示例（前5维）: {vector[:5]}\n")
        return True

    except Exception as e:
        print(f"❌ Embedding API连接失败: {type(e).__name__}")
        print(f"   {str(e)}")
        print("\n💡 通常Embedding API与通义千问使用相同的API Key")
        return False


if __name__ == "__main__":
    # 检查.env文件
    if not os.path.exists(".env"):
        print("⚠️  未找到.env文件！")
        print("请先复制.env.example并填写配置:")
        print("   cp .env.example .env")
        sys.exit(1)

    # 检查必要的环境变量
    required_vars = ["QWEN_API_KEY", "QWEN_BASE_URL", "EMBEDDING_API_KEY"]
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        print("❌ 缺少必要的环境变量:")
        for var in missing:
            print(f"   - {var}")
        print("\n请在.env文件中配置以上变量")
        sys.exit(1)

    # 执行测试
    qwen_ok = test_qwen()
    print("=" * 50)
    embedding_ok = test_embedding()

    print("=" * 50)
    if qwen_ok and embedding_ok:
        print("✅ 所有LLM测试通过！")
        sys.exit(0)
    else:
        print("❌ 部分测试失败，请检查配置")
        sys.exit(1)
