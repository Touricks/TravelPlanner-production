#!/usr/bin/env python3
"""
POI数据迁移: PostgreSQL → OceanBase (Hybrid Search)
===================================================
使用阿里云Embedding (text-embedding-v4, 1024维) + Sparse + Fulltext
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
import uuid
from tqdm import tqdm

from seekdb_agent.db.sparse_encoder import TFIDFEncoder

load_dotenv()

# 数据文件（已从PostgreSQL导出）
DATA_FILE = Path(__file__).parent.parent / "data" / "pois_export.json"

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
        # DashScope支持批量，但有长度限制，逐个处理更安全
        embeddings = []
        for text in texts:
            response = self.client.embeddings.create(model=self.model, input=text)
            embeddings.append(response.data[0].embedding)
        return embeddings

    def embed_query(self, text: str) -> list[float]:
        """Embed单个查询"""
        response = self.client.embeddings.create(model=self.model, input=text)
        return response.data[0].embedding


def get_embeddings():
    """获取阿里云Embedding"""
    return DashScopeEmbeddings(model=os.getenv("EMBEDDING_MODEL", "text-embedding-v4"))


def load_pois_from_json() -> list[dict]:
    """从JSON文件读取POI数据"""
    with open(DATA_FILE) as f:
        return json.load(f)


def uuid_from_bytes(b) -> str:
    """Convert UUID bytes to string."""
    if isinstance(b, list):
        return str(uuid.UUID(bytes=bytes(b)))
    if isinstance(b, (bytes, memoryview)):
        return str(uuid.UUID(bytes=bytes(b)))
    return str(b)


def prepare_data(pois: list[dict]) -> tuple[list[Document], list[str], list[dict[int, float]]]:
    """准备数据"""
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

        # Add descriptive attributes for better fulltext search
        if poi.get("rating"):
            rating = float(poi["rating"])
            rating_desc = "excellent rating" if rating >= 4.5 else "good rating" if rating >= 4.0 else ""
            if rating_desc:
                parts.append(rating_desc)

        if poi.get("reviews_count"):
            reviews = int(poi["reviews_count"])
            if reviews >= 10000:
                parts.append("very popular destination")
            elif reviews >= 1000:
                parts.append("popular destination")

        if poi.get("price_level"):
            price_level = int(poi["price_level"])
            price_desc = {
                1: "low price",
                2: "moderate price",
                3: "high price",
                4: "high price",
            }.get(price_level, "")
            if price_desc:
                parts.append(price_desc)

        text = ". ".join(filter(None, parts))

        metadata = {
            "id": uuid_from_bytes(poi["id"]),
            "name": poi["name"],
            "city": poi.get("city"),
            "state": poi.get("state"),
            "latitude": float(poi["latitude"]) if poi.get("latitude") else None,
            "longitude": float(poi["longitude"]) if poi.get("longitude") else None,
            "rating": float(poi["rating"]) if poi.get("rating") else None,
            "reviews_count": poi.get("reviews_count"),
            "price_level": poi.get("price_level"),
            "primary_category": poi.get("primary_category"),
        }

        documents.append(Document(page_content=text, metadata=metadata))
        fulltext_content.append(text)

    # Train TF-IDF and generate sparse embeddings
    print("      训练TF-IDF...")
    tfidf = TFIDFEncoder(max_vocab_size=100000)
    tfidf.fit([doc.page_content for doc in documents])

    print("      生成稀疏向量...")
    sparse_embeddings = [
        tfidf.encode(doc.page_content)
        for doc in tqdm(documents, desc="      Sparse编码", unit="doc")
    ]
    print(f"      词汇表: {tfidf.get_vocab_size()}词")

    return documents, fulltext_content, sparse_embeddings


def main():
    print("=" * 60)
    print("POI迁移: PostgreSQL → OceanBase (Hybrid Search)")
    print(f"Embedding: {os.getenv('EMBEDDING_MODEL')} ({EMBEDDING_DIM}维)")
    print("=" * 60)

    # 1. Load from JSON
    print("\n[1/4] 从JSON文件读取数据...")
    pois = load_pois_from_json()
    print(f"      读取 {len(pois)} 条POI")

    # 2. Prepare data
    print("\n[2/4] 准备数据...")
    documents, fulltext_content, sparse_embeddings = prepare_data(pois)

    # 3. Initialize OceanBase Hybrid VectorStore
    print("\n[3/4] 初始化OceanBase VectorStore...")

    # Step 1: 创建表结构
    print("      创建表结构...")
    OceanbaseVectorStore(
        connection_args=OB_CONFIG,
        table_name="pois",
        embedding_function=None,
        embedding_dim=EMBEDDING_DIM,
        include_sparse=True,
        include_fulltext=True,
        drop_old=True,
    )

    # Step 2: 连接并准备写入
    print("      连接VectorStore...")
    embeddings = get_embeddings()
    store = OceanbaseVectorStore(
        connection_args=OB_CONFIG,
        table_name="pois",
        embedding_function=embeddings,
        embedding_dim=EMBEDDING_DIM,
        include_sparse=True,
        include_fulltext=True,
        drop_old=False,
    )

    # 4. Migrate data
    print("\n[4/4] 迁移数据...")

    # Check existing records to resume from where we left off
    import pymysql
    conn = pymysql.connect(
        host=OB_CONFIG["host"],
        port=OB_CONFIG["port"],
        user=OB_CONFIG["user"],
        password=OB_CONFIG["password"],
        database=OB_CONFIG["db_name"]
    )
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM pois")
    existing_count = cursor.fetchone()[0]
    conn.close()

    print(f"      现有记录: {existing_count}条")

    batch_size = 10  # 更小批次避免超时
    total = len(documents)
    start_idx = existing_count if existing_count < total else 0

    import time

    with tqdm(total=total, desc="      迁移POI", unit="条", initial=start_idx) as pbar:
        for i in range(start_idx, total, batch_size):
            end = min(i + batch_size, total)
            batch_docs = documents[i:end]
            batch_fulltext = fulltext_content[i:end]
            batch_sparse = sparse_embeddings[i:end]

            # Use add_documents_with_hybrid_fields to add all fields at once
            store.add_documents_with_hybrid_fields(
                documents=batch_docs,
                sparse_embeddings=batch_sparse,
                fulltext_content=batch_fulltext
            )

            pbar.update(len(batch_docs))

            # Add delay to avoid timeout
            if end < total:
                time.sleep(0.5)

    print("\n" + "=" * 60)
    print("✅ 迁移完成！")
    print("=" * 60)
    print(f"   记录数: {len(documents)}")
    print(f"   Vector: {EMBEDDING_DIM}维")
    print(f"   Sparse + Fulltext: 已启用")

    # Test
    print("\n测试搜索...")
    results = store.similarity_search("beach vacation", k=3)
    for i, doc in enumerate(results):
        print(f"   [{i+1}] {doc.metadata.get('name')} - {doc.metadata.get('city')}")


if __name__ == "__main__":
    main()
