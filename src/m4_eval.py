from __future__ import annotations

"""Module 4: RAGAS Evaluation — 4 metrics + failure analysis."""

import os, sys, json, math
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
from dataclasses import dataclass, asdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TEST_SET_PATH


@dataclass
class EvalResult:
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float


def load_test_set(path: str = TEST_SET_PATH) -> list[dict]:
    """Load test set from JSON. (Đã implement sẵn)"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def evaluate_ragas(questions: list[str], answers: list[str],
                   contexts: list[list[str]], ground_truths: list[str]) -> dict:
    """Evaluate with RAGAS; retain predictions and explicitly mark unavailable scores."""
    metrics = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
    if len({len(questions), len(answers), len(contexts), len(ground_truths)}) != 1:
        raise ValueError("Evaluation inputs must have equal lengths")
    records = [dict(question=q, answer=a, contexts=list(c), ground_truth=g)
               for q, a, c, g in zip(questions, answers, contexts, ground_truths)]
    try:
        from config import OPENAI_API_KEY
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY unavailable or LAB_OFFLINE=1")
        if not questions:
            raise ValueError("No questions to evaluate")
        from ragas import evaluate
        from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
        from ragas.run_config import RunConfig
        from datasets import Dataset
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings
        dataset = Dataset.from_dict({"question": questions, "answer": answers,
                                     "contexts": contexts, "ground_truth": ground_truths})
        result = evaluate(dataset, metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
                          llm=ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY,
                                         temperature=0, timeout=30, max_retries=0),
                          embeddings=OpenAIEmbeddings(model="text-embedding-3-small", api_key=OPENAI_API_KEY,
                                                       request_timeout=30, max_retries=0),
                          run_config=RunConfig(timeout=60, max_retries=1, max_workers=4))
        # Read only score columns from pandas: contexts may be numpy arrays.
        frame = result.to_pandas()
        per_question = []
        for record, (_, row) in zip(records, frame.iterrows()):
            scores = {metric: float(row[metric]) for metric in metrics}
            per_question.append(EvalResult(**record, **scores))
        aggregate = {metric: float(result[metric]) for metric in metrics}
        valid = all(math.isfinite(value) for value in aggregate.values())
        complete = valid and all(math.isfinite(getattr(r, m)) for r in per_question for m in metrics)
        evaluator_models = ["gpt-4o-mini", "text-embedding-3-small"]
        return {**aggregate, "per_question": per_question,
                "metadata": {"evaluator_models": evaluator_models},
                "evaluation_status": "completed" if complete else "partial",
                "evaluation_error": None if complete else "Some RAGAS metrics are unavailable"}
    except Exception as exc:
        reason = f"{type(exc).__name__}: {exc}"
        print(f"  RAGAS unavailable: {reason}")
        return {**dict.fromkeys(metrics, 0.0), "per_question": [],
                "metadata": {"evaluator_models": []},
                "predictions": records, "evaluation_status": "unavailable", "evaluation_error": reason}


def failure_analysis(eval_results: list[EvalResult], bottom_n: int = 10) -> list[dict]:
    """Analyze bottom-N worst questions using Diagnostic Tree."""
    diagnostic_tree = {
        "faithfulness": ("LLM hallucinating / ungrounded answer", "Tighten prompt, lower temperature, use strict system prompt"),
        "context_recall": ("Missing relevant chunks in retrieval", "Improve chunking strategy or add BM25 / hybrid search"),
        "context_precision": ("Too many irrelevant chunks retrieved", "Add reranking (CrossEncoder) or metadata filtering"),
        "answer_relevancy": ("Answer doesn't match question intent", "Improve prompt template, add query reformulation"),
    }

    if bottom_n <= 0:
        return []
    scored = []
    for er in eval_results:
        scores = {
            "faithfulness": er.faithfulness,
            "answer_relevancy": er.answer_relevancy,
            "context_precision": er.context_precision,
            "context_recall": er.context_recall,
        }
        if not all(math.isfinite(v) for v in scores.values()):
            continue
        avg_score = sum(scores.values()) / 4.0
        worst_metric = min(scores, key=scores.get)
        diag, fix = diagnostic_tree.get(worst_metric, ("Unknown issue", "Review pipeline"))
        scored.append({
            "question": er.question,
            "answer": er.answer,
            "ground_truth": er.ground_truth,
            "worst_metric": worst_metric,
            "score": float(scores[worst_metric]),
            "avg_score": float(avg_score),
            "diagnosis": diag,
            "suggested_fix": fix,
        })

    scored.sort(key=lambda x: (x["avg_score"], x["score"]))
    return scored[:bottom_n]


def save_report(results: dict, failures: list[dict], path: str = "reports/ragas_report.json"):
    """Save evaluation report to JSON. (Đã implement sẵn)"""
    parent_dir = os.path.dirname(path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)
    metrics = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
    available = results.get("evaluation_status", "completed") != "unavailable"
    records = [asdict(row) for row in results.get("per_question", [])] or results.get("predictions", [])
    report = {
        "aggregate": {m: results.get(m) if available else None for m in metrics},
        "num_questions": len(records),
        "evaluation_status": results.get("evaluation_status", "completed"),
        "evaluation_error": results.get("evaluation_error"),
        "per_question": records,
        "failures": failures,
    }
    def clean(value):
        if isinstance(value, float) and not math.isfinite(value):
            return None
        if isinstance(value, dict):
            return {k: clean(v) for k, v in value.items()}
        if isinstance(value, list):
            return [clean(v) for v in value]
        return value
    with open(path, "w", encoding="utf-8") as f:
        json.dump(clean(report), f, ensure_ascii=False, indent=2, allow_nan=False)
    print(f"Report saved to {path}")


if __name__ == "__main__":
    test_set = load_test_set()
    print(f"Loaded {len(test_set)} test questions")
    print("Run pipeline.py first to generate answers, then call evaluate_ragas().")
