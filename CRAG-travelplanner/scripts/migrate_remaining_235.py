#!/usr/bin/env python3
"""
补全剩余235条POI记录
===================
从索引5690到5924的POI数据迁移
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
import time
from tqdm import tqdm

from seekdb_agent.db.sparse_encoder import TFIDFEncoder

load_dotenv()

# 数据文件
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
        embeddings = []
        for text in texts:
            response = self.client.embeddings.create(model=self.model, input=text)
            embeddings.append(response.data[0].embedding)
        return embeddings

    def embed_query(self, text: str) -> list[float]:
        """Embed单个查询"""
        response = self.client.embeddings.create(model=self.model, input=text)
        return response.data[0].embedding


def prepare_data(pois: list[dict]) -> tuple[list[Document], list[str], list[dict[int, float]]]:
    """准备数据（与主脚本相同的逻辑）"""
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
            "id": str(poi["id"]),
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

    # 需要用全部数据训练TF-IDF以保持词汇表一致
    print("      加载完整数据集训练TF-IDF...")
    with open(DATA_FILE) as f:
        all_pois = json.load(f)

    all_texts = []
    for poi in all_pois:
        parts = [poi["name"]]
        if poi.get("city"):
            parts.append(f"{poi['city']}, {poi.get('state', '')}")
        if poi.get("primary_category"):
            parts.append(poi["primary_category"])
        if poi.get("editorial_summary"):
            parts.append(poi["editorial_summary"])
        all_texts.append(". ".join(filter(None, parts)))

    print("      训练TF-IDF...")
    tfidf = TFIDFEncoder(max_vocab_size=100000)
    tfidf.fit(all_texts)

    # 只为剩余235条生成sparse embeddings
    sparse_embeddings = [tfidf.encode(doc.page_content) for doc in documents]
    print(f"      词汇表: {tfidf.get_vocab_size()}词")

    return documents, fulltext_content, sparse_embeddings


def main():
    print("=" * 60)
    print("补全剩余235条POI")
    print("=" * 60)

    # 1. 加载最后235条记录
    print("\n[1/3] 加载剩余POI数据...")
    with open(DATA_FILE) as f:
        all_pois = json.load(f)

    remaining_pois = all_pois[5690:]  # 从索引5690开始
    print(f"      加载 {len(remaining_pois)} 条POI (索引5690-5924)")

    # 2. 准备数据
    print("\n[2/3] 准备数据...")
    documents, fulltext_content, sparse_embeddings = prepare_data(remaining_pois)

    # 3. 连接OceanBase并迁移
    print("\n[3/3] 迁移剩余数据...")

    embeddings = DashScopeEmbeddings(model=os.getenv("EMBEDDING_MODEL", "text-embedding-v4"))
    store = OceanbaseVectorStore(
        connection_args=OB_CONFIG,
        table_name="pois",
        embedding_function=embeddings,
        embedding_dim=EMBEDDING_DIM,
        include_sparse=True,
        include_fulltext=True,
        drop_old=False,  # 不删除已有数据
    )

    # 小批次插入，避免超时
    batch_size = 10
    total = len(documents)

    with tqdm(total=total, desc="      迁移POI", unit="条") as pbar:
        for i in range(0, total, batch_size):
            end = min(i + batch_size, total)
            batch_docs = documents[i:end]
            batch_fulltext = fulltext_content[i:end]
            batch_sparse = sparse_embeddings[i:end]

            store.add_documents_with_hybrid_fields(
                documents=batch_docs,
                sparse_embeddings=batch_sparse,
                fulltext_content=batch_fulltext
            )

            pbar.update(len(batch_docs))

            # 批次间延迟避免超时
            if end < total:
                time.sleep(0.5)

    print("\n" + "=" * 60)
    print("✅ 补全完成！")
    print("=" * 60)
    print(f"   新增记录数: {len(documents)}")
    print(f"   Vector: {EMBEDDING_DIM}维")
    print(f"   Sparse + Fulltext: 已启用")

    # 验证总数
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
    final_count = cursor.fetchone()[0]
    conn.close()

    print(f"\n📊 当前数据库总记录数: {final_count}/5925")
    if final_count == 5925:
        print("🎉 所有POI已成功迁移！")
    else:
        print(f"⚠️  还缺少 {5925 - final_count} 条记录")


if __name__ == "__main__":
    main()
