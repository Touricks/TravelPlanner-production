"""
Database Connection Layer
=========================
OceanBase数据库连接和VectorStore初始化
"""

import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain_core.embeddings import Embeddings
from langchain_oceanbase.vectorstores import OceanbaseVectorStore
from openai import OpenAI

load_dotenv()

# Embedding模型配置（DashScope）
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v4")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1024"))


class DashScopeEmbeddings(Embeddings):
    """阿里云DashScope Embedding"""

    def __init__(self, model: str = EMBEDDING_MODEL):
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


def get_oceanbase_connection_args() -> dict:
    """获取OceanBase连接参数"""
    return {
        "host": os.getenv("DATABASE_HOST", "127.0.0.1"),
        "port": int(os.getenv("DATABASE_PORT", "2881")),
        "user": os.getenv("DATABASE_USER", "root@test"),
        "password": os.getenv("DATABASE_PASSWORD", ""),
        "db_name": os.getenv("DATABASE_NAME", "crag_travelplanner"),
    }


@lru_cache(maxsize=1)
def get_embeddings() -> DashScopeEmbeddings:
    """获取Embedding模型实例（单例）"""
    return DashScopeEmbeddings(model=EMBEDDING_MODEL)


_vector_store_instance: OceanbaseVectorStore | None = None


def get_vector_store(table_name: str = "pois") -> OceanbaseVectorStore:
    """
    获取OceanBase VectorStore实例

    Args:
        table_name: 表名，默认为pois

    Returns:
        OceanbaseVectorStore实例
    """
    global _vector_store_instance

    if _vector_store_instance is None:
        connection_args = get_oceanbase_connection_args()
        embeddings = get_embeddings()

        _vector_store_instance = OceanbaseVectorStore(
            connection_args=connection_args,
            table_name=table_name,
            embedding_function=embeddings,
            embedding_dim=EMBEDDING_DIM,
        )

    return _vector_store_instance


def reset_vector_store() -> None:
    """重置VectorStore实例（用于测试）"""
    global _vector_store_instance
    global _hybrid_store_instance
    _vector_store_instance = None
    _hybrid_store_instance = None


_hybrid_store_instance: OceanbaseVectorStore | None = None


def get_hybrid_store(table_name: str = "pois") -> OceanbaseVectorStore:
    """
    获取OceanBase Hybrid Search VectorStore实例
    支持 Vector + Sparse + Fulltext 混合搜索

    Args:
        table_name: 表名，默认为pois

    Returns:
        OceanbaseVectorStore实例（启用hybrid search）
    """
    global _hybrid_store_instance

    if _hybrid_store_instance is None:
        connection_args = get_oceanbase_connection_args()
        embeddings = get_embeddings()

        _hybrid_store_instance = OceanbaseVectorStore(
            connection_args=connection_args,
            table_name=table_name,
            embedding_function=embeddings,
            embedding_dim=EMBEDDING_DIM,
            include_sparse=True,
            include_fulltext=True,
            drop_old=False,  # 不删除已有表
        )

    return _hybrid_store_instance
