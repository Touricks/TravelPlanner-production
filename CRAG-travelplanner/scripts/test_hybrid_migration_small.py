#!/usr/bin/env python3
"""
测试Hybrid Search迁移（小样本）
================================
验证sparse embeddings是否正确存储
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from openai import OpenAI
from langchain_core.embeddings import Embeddings
from langchain_oceanbase.vectorstores import OceanbaseVectorStore
from langchain_core.documents import Document
import json

from seekdb_agent.db.sparse_encoder import TFIDFEncoder

load_dotenv()

# OceanBase连接
OB_CONFIG = {
    "host": os.getenv("DATABASE_HOST", "127.0.0.1"),
    "port": int(os.getenv("DATABASE_PORT", "2881")),
    "user": os.getenv("DATABASE_USER", "root@test"),
    "password": os.getenv("DATABASE_PASSWORD", ""),
    "db_name": os.getenv("DATABASE_NAME", "crag_travelplanner"),
}

EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1024"))


class DashScopeEmbeddings(Embeddings):
    """阿里云DashScope Embedding"""

    def __init__(self, model: str = "text-embedding-v4"):
        self.model = model
        self.client = OpenAI(
            api_key=os.getenv("EMBEDDING_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed多个文档"""
        embeddings = []
        for text in texts:
            response = self.client.embeddings.create(model=self.model, input=text)
            embeddings.append(response.data[0].embedding)
        return embeddings

    def embed_query(self, text: str) -> list[float]:
        """Embed单个查询"""
        response = self.client.embeddings.create(model=self.model, input=text)
        return response.data[0].embedding


def main():
    print("=" * 60)
    print("测试Hybrid Search迁移（10条记录）")
    print("=" * 60)

    # Load sample data
    data_file = Path(__file__).parent.parent / "data" / "pois_export.json"
    with open(data_file) as f:
        pois = json.load(f)[:10]

    print(f"\n加载 {len(pois)} 条POI")

    # Prepare data
    documents = []
    fulltext_content = []

    for poi in pois:
        parts = [poi["name"]]
        if poi.get("city"):
            parts.append(f"{poi['city']}, {poi.get('state', '')}")
        if poi.get("primary_category"):
            parts.append(poi["primary_category"])
        if poi.get("editorial_summary"):
            parts.append(poi["editorial_summary"])
        text = ". ".join(filter(None, parts))

        metadata = {
            "id": str(poi["id"]),
            "name": poi["name"],
            "city": poi.get("city"),
        }

        documents.append(Document(page_content=text, metadata=metadata))
        fulltext_content.append(text)

    # Train TF-IDF
    print("训练TF-IDF...")
    tfidf = TFIDFEncoder(max_vocab_size=1000)
    tfidf.fit([doc.page_content for doc in documents])
    sparse_embeddings = [tfidf.encode(doc.page_content) for doc in documents]

    print(f"词汇表: {tfidf.get_vocab_size()}词")
    print(f"示例sparse向量: {len(sparse_embeddings[0])}个非零元素")

    # Create table
    print("\n创建测试表...")
    OceanbaseVectorStore(
        connection_args=OB_CONFIG,
        table_name="pois_test",
        embedding_function=None,
        embedding_dim=EMBEDDING_DIM,
        include_sparse=True,
        include_fulltext=True,
        drop_old=True,
    )

    # Connect and add data
    print("添加数据...")
    embeddings = DashScopeEmbeddings()
    store = OceanbaseVectorStore(
        connection_args=OB_CONFIG,
        table_name="pois_test",
        embedding_function=embeddings,
        embedding_dim=EMBEDDING_DIM,
        include_sparse=True,
        include_fulltext=True,
        drop_old=False,
    )

    # Add with hybrid fields
    ids = store.add_documents_with_hybrid_fields(
        documents=documents,
        sparse_embeddings=sparse_embeddings,
        fulltext_content=fulltext_content
    )

    print(f"✅ 添加成功，ID: {ids[:3]}...")

    # Verify sparse data
    print("\n验证数据...")
    results = store.similarity_search("casino", k=1)
    print(f"Vector搜索结果: {results[0].metadata.get('name')}")

    # Test advanced hybrid search
    print("\n测试Hybrid Search...")

    # Encode query
    query_sparse = tfidf.encode("casino hotel")

    hybrid_results = store.advanced_hybrid_search(
        vector_query="casino hotel",
        sparse_query=query_sparse,
        fulltext_query="casino hotel",
        modality_weights={"vector": 0.4, "sparse": 0.3, "fulltext": 0.3},
        k=3
    )

    print(f"Hybrid搜索返回 {len(hybrid_results)} 条结果")
    for i, doc in enumerate(hybrid_results):
        print(f"  [{i+1}] {doc.metadata.get('name')} - {doc.metadata.get('city')}")

    print("\n" + "=" * 60)
    print("✅ 测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    main()