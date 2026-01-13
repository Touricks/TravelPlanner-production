"""
TF-IDF Sparse Encoder
=====================
基于词汇表的TF-IDF编码器，用于Hybrid Search中的稀疏向量搜索
"""

import math
import re
from collections import Counter

# 英文停用词列表
STOPWORDS: set[str] = {
    # 冠词
    "a",
    "an",
    "the",
    # 介词
    "in",
    "on",
    "at",
    "for",
    "with",
    "to",
    "from",
    "of",
    "by",
    "as",
    "into",
    "through",
    "during",
    "before",
    "after",
    "above",
    "below",
    "between",
    "under",
    "over",
    "out",
    "off",
    "down",
    "up",
    # 连词
    "and",
    "or",
    "but",
    "nor",
    "so",
    "yet",
    "both",
    "either",
    "neither",
    # 代词
    "i",
    "me",
    "my",
    "myself",
    "we",
    "our",
    "ours",
    "ourselves",
    "you",
    "your",
    "yours",
    "yourself",
    "yourselves",
    "he",
    "him",
    "his",
    "himself",
    "she",
    "her",
    "hers",
    "herself",
    "it",
    "its",
    "itself",
    "they",
    "them",
    "their",
    "theirs",
    "themselves",
    "this",
    "that",
    "these",
    "those",
    "who",
    "whom",
    "which",
    "what",
    # 助动词/be动词
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "has",
    "have",
    "had",
    "having",
    "do",
    "does",
    "did",
    "doing",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "must",
    "can",
    # 其他常见词
    "not",
    "no",
    "yes",
    "all",
    "any",
    "some",
    "each",
    "every",
    "more",
    "most",
    "other",
    "another",
    "such",
    "own",
    "same",
    "than",
    "too",
    "very",
    "just",
    "also",
    "now",
    "here",
    "there",
    "when",
    "where",
    "why",
    "how",
    "if",
    "then",
    "else",
    "because",
    "about",
    "against",
    "while",
    "although",
    "though",
    "unless",
    "until",
    "only",
    "again",
    "further",
    "once",
    "already",
    "always",
    "never",
    # 旅游领域常见但无意义的词
    "place",
    "located",
    "offers",
    "features",
    "provides",
    "known",
}


class TFIDFEncoder:
    """基于词汇表的TF-IDF编码器，用于稀疏向量搜索"""

    def __init__(self, max_vocab_size: int = 100000):
        """
        初始化TF-IDF编码器

        Args:
            max_vocab_size: 最大词汇表大小（OceanBase限制500K维度）
        """
        self.max_vocab_size = max_vocab_size
        self.vocab: dict[str, int] = {}  # term -> index
        self.idf: dict[str, float] = {}  # term -> idf score
        self.doc_count: int = 0
        self._fitted: bool = False

    def tokenize(self, text: str) -> list[str]:
        """
        分词并过滤停用词

        Args:
            text: 输入文本

        Returns:
            过滤后的词列表
        """
        # 提取字母数字词（至少2个字符）
        words = re.findall(r"\b[a-zA-Z][a-zA-Z0-9]*\b", text.lower())
        # 过滤停用词和短词
        return [w for w in words if w not in STOPWORDS and len(w) >= 2]

    def fit(self, documents: list[str]) -> "TFIDFEncoder":
        """
        从文档集构建词汇表和IDF分数

        Args:
            documents: 文档列表

        Returns:
            self，支持链式调用
        """
        self.doc_count = len(documents)
        doc_freq: Counter[str] = Counter()

        # 统计每个词出现在多少文档中
        for doc in documents:
            unique_terms = set(self.tokenize(doc))
            for term in unique_terms:
                doc_freq[term] += 1

        # 选择文档频率最高的词构建词汇表
        top_terms = doc_freq.most_common(self.max_vocab_size)

        # 构建词汇表和计算IDF
        for idx, (term, df) in enumerate(top_terms):
            self.vocab[term] = idx
            # IDF = log(N / df) + 1 (平滑处理，避免除零)
            self.idf[term] = math.log(self.doc_count / df) + 1

        self._fitted = True
        return self

    def encode(self, text: str) -> dict[int, float]:
        """
        将文本编码为TF-IDF稀疏向量

        Args:
            text: 输入文本

        Returns:
            稀疏向量 {index: tfidf_score}
        """
        if not self._fitted:
            raise RuntimeError("TFIDFEncoder must be fitted before encoding")

        terms = self.tokenize(text)
        if not terms:
            return {}

        term_freq: Counter[str] = Counter(terms)
        max_tf = max(term_freq.values())

        sparse_vec: dict[int, float] = {}
        for term, tf in term_freq.items():
            if term in self.vocab:
                idx = self.vocab[term]
                # TF-IDF = (tf / max_tf) * idf
                tfidf = (tf / max_tf) * self.idf[term]
                sparse_vec[idx] = tfidf

        return sparse_vec

    def get_vocab_size(self) -> int:
        """获取词汇表大小"""
        return len(self.vocab)

    def get_top_terms(self, n: int = 10) -> list[tuple[str, float]]:
        """获取IDF最高的N个词（最具区分度）"""
        sorted_terms = sorted(self.idf.items(), key=lambda x: x[1], reverse=True)
        return sorted_terms[:n]
