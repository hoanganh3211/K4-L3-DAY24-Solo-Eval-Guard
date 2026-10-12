from __future__ import annotations

"""Module 3: Reranking — Cross-encoder top-20 → top-3 + latency benchmark."""

import os, sys, time
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RERANK_TOP_K


@dataclass
class RerankResult:
    text: str
    original_score: float
    rerank_score: float
    metadata: dict
    rank: int


_cached_cross_encoder = None


class CrossEncoderReranker:
    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
        self.model_name = model_name
        self._model = None

    def _load_model(self):
        global _cached_cross_encoder
        if self._model is None:
            if _cached_cross_encoder is not None and getattr(_cached_cross_encoder, "_model_name", None) == self.model_name:
                self._model = _cached_cross_encoder
            else:
                from sentence_transformers import CrossEncoder
                try:
                    self._model = CrossEncoder(self.model_name, local_files_only=True)
                except OSError:
                    self._model = CrossEncoder(self.model_name)
                self._model._model_name = self.model_name
                _cached_cross_encoder = self._model
        return self._model

    def rerank(self, query: str, documents: list[dict], top_k: int = RERANK_TOP_K) -> list[RerankResult]:
        """Rerank documents: top-20 → top-k."""
        if not documents or top_k <= 0:
            return []
        model = self._load_model()
        pairs = [(query, d.text if hasattr(d, "text") else d["text"]) for d in documents]
        scores = model.predict(pairs)
        if hasattr(scores, "tolist"):
            scores = scores.tolist()
        elif isinstance(scores, (int, float)):
            scores = [float(scores)]
        else:
            scores = [float(s) for s in scores]

        scored = []
        for s, doc in zip(scores, documents):
            text = doc.text if hasattr(doc, "text") else doc["text"]
            orig_score = getattr(doc, "score", None) if hasattr(doc, "score") else doc.get("score", 0.0)
            meta = getattr(doc, "metadata", None) if hasattr(doc, "metadata") else doc.get("metadata", {})
            scored.append((float(s), text, float(orig_score) if orig_score is not None else 0.0, meta))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            RerankResult(
                text=text,
                original_score=orig_score,
                rerank_score=score,
                metadata=meta,
                rank=i + 1
            )
            for i, (score, text, orig_score, meta) in enumerate(scored[:top_k])
        ]


class FlashrankReranker:
    """Lightweight alternative (<5ms). Optional."""
    def __init__(self):
        self._model = None

    def rerank(self, query: str, documents: list[dict], top_k: int = RERANK_TOP_K) -> list[RerankResult]:
        if not documents:
            return []
        from flashrank import Ranker, RerankRequest
        if self._model is None:
            self._model = Ranker()
        passages = [
            {"id": i, "text": d.text if hasattr(d, "text") else d["text"], "meta": getattr(d, "metadata", None) if hasattr(d, "metadata") else d.get("metadata", {})}
            for i, d in enumerate(documents)
        ]
        results = self._model.rerank(RerankRequest(query=query, passages=passages))
        return [
            RerankResult(
                text=r["text"],
                original_score=0.0,
                rerank_score=float(r["score"]),
                metadata=r.get("meta", {}),
                rank=i + 1
            )
            for i, r in enumerate(results[:top_k])
        ]


def benchmark_reranker(reranker, query: str, documents: list[dict], n_runs: int = 5) -> dict:
    """Benchmark latency over n_runs. (Đã implement sẵn)"""
    if n_runs <= 0:
        raise ValueError("n_runs must be positive")
    times = []
    for _ in range(n_runs):
        start = time.perf_counter()
        reranker.rerank(query, documents)
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    return {"avg_ms": sum(times) / len(times), "min_ms": min(times), "max_ms": max(times)}


if __name__ == "__main__":
    query = "Nhân viên được nghỉ phép bao nhiêu ngày?"
    docs = [
        {"text": "Nhân viên được nghỉ 12 ngày/năm.", "score": 0.8, "metadata": {}},
        {"text": "Mật khẩu thay đổi mỗi 90 ngày.", "score": 0.7, "metadata": {}},
        {"text": "Thời gian thử việc là 60 ngày.", "score": 0.75, "metadata": {}},
    ]
    reranker = CrossEncoderReranker()
    for r in reranker.rerank(query, docs):
        print(f"[{r.rank}] {r.rerank_score:.4f} | {r.text}")
