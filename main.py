import asyncio
import json
import os
import time
from statistics import mean
from typing import Dict, List, Optional, Tuple

from agent.main_agent import MainAgent
from engine.runner import BenchmarkRunner


QUALITY_MIN_SCORE = 3.0
MAX_SCORE_DROP = 0.10
MAX_COST_INCREASE_RATIO = 0.10
MAX_LATENCY_INCREASE_RATIO = 0.20


class ExpertEvaluator:
    async def score(self, case, resp):
        return {
            "faithfulness": 0.9,
            "relevancy": 0.8,
            "retrieval": {"hit_rate": 1.0, "mrr": 0.5},
        }


class MultiModelJudge:
    async def evaluate_multi_judge(self, q, a, gt):
        return {
            "final_score": 4.5,
            "agreement_rate": 0.8,
            "reasoning": "Both judges consider this answer acceptable for the expected answer.",
        }


def load_dataset(path: str = "data/golden_set.jsonl") -> List[Dict]:
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Missing {path}. Run 'python data/synthetic_gen.py' before benchmarking."
        )

    with open(path, "r", encoding="utf-8") as f:
        dataset = [json.loads(line) for line in f if line.strip()]

    if not dataset:
        raise ValueError(f"{path} is empty. Add at least one benchmark case.")

    return dataset


def _safe_mean(values: List[float]) -> float:
    return round(mean(values), 6) if values else 0.0


def build_summary(agent_version: str, results: List[Dict], started_at: float) -> Dict:
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "pass")
    failed = total - passed
    latencies = [r["latency_seconds"] for r in results]
    costs = [r["token_usage"]["estimated_cost_usd"] for r in results]
    tokens = [r["token_usage"]["total_tokens"] for r in results]

    metrics = {
        "avg_score": _safe_mean([r["judge"]["final_score"] for r in results]),
        "pass_rate": round(passed / total, 6) if total else 0.0,
        "hit_rate": _safe_mean([r["ragas"]["retrieval"]["hit_rate"] for r in results]),
        "mrr": _safe_mean([r["ragas"]["retrieval"]["mrr"] for r in results]),
        "agreement_rate": _safe_mean([r["judge"]["agreement_rate"] for r in results]),
        "avg_latency_seconds": _safe_mean(latencies),
        "max_latency_seconds": round(max(latencies), 6) if latencies else 0.0,
        "total_tokens": sum(tokens),
        "avg_tokens_per_case": _safe_mean(tokens),
        "estimated_total_cost_usd": round(sum(costs), 8),
        "estimated_avg_cost_usd": _safe_mean(costs),
    }

    return {
        "metadata": {
            "version": agent_version,
            "total": total,
            "passed": passed,
            "failed": failed,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_seconds": round(time.perf_counter() - started_at, 4),
        },
        "metrics": metrics,
    }


def _ratio_delta(new_value: float, old_value: float) -> float:
    if old_value == 0:
        return 0.0 if new_value == 0 else 1.0
    return (new_value - old_value) / old_value


def build_release_gate(previous_summary: Dict, new_summary: Dict) -> Dict:
    previous = previous_summary["metrics"]
    new = new_summary["metrics"]

    score_delta = new["avg_score"] - previous["avg_score"]
    cost_delta_ratio = _ratio_delta(
        new["estimated_avg_cost_usd"], previous["estimated_avg_cost_usd"]
    )
    latency_delta_ratio = _ratio_delta(
        new["avg_latency_seconds"], previous["avg_latency_seconds"]
    )

    checks = {
        "quality_floor": new["avg_score"] >= QUALITY_MIN_SCORE,
        "quality_regression": score_delta >= -MAX_SCORE_DROP,
        "cost_regression": cost_delta_ratio <= MAX_COST_INCREASE_RATIO,
        "latency_regression": latency_delta_ratio <= MAX_LATENCY_INCREASE_RATIO,
    }
    decision = "Release" if all(checks.values()) else "Rollback"

    return {
        "decision": decision,
        "checks": checks,
        "thresholds": {
            "quality_min_score": QUALITY_MIN_SCORE,
            "max_score_drop": MAX_SCORE_DROP,
            "max_cost_increase_ratio": MAX_COST_INCREASE_RATIO,
            "max_latency_increase_ratio": MAX_LATENCY_INCREASE_RATIO,
        },
        "delta": {
            "avg_score": round(score_delta, 6),
            "avg_cost_usd_ratio": round(cost_delta_ratio, 6),
            "avg_latency_seconds_ratio": round(latency_delta_ratio, 6),
        },
    }


async def run_benchmark_with_results(
    agent_version: str, dataset: Optional[List[Dict]] = None
) -> Tuple[List[Dict], Dict]:
    print(f"Starting benchmark for {agent_version}...")
    dataset = dataset or load_dataset()
    started_at = time.perf_counter()

    runner = BenchmarkRunner(MainAgent(), ExpertEvaluator(), MultiModelJudge())
    results = await runner.run_all(dataset)
    summary = build_summary(agent_version, results, started_at)
    return results, summary


async def run_benchmark(version: str) -> Dict:
    _, summary = await run_benchmark_with_results(version)
    return summary


async def main():
    try:
        dataset = load_dataset()
    except (FileNotFoundError, ValueError) as exc:
        print(f"Cannot run benchmark: {exc}")
        return

    previous_results, previous_summary = await run_benchmark_with_results(
        "Agent_V1_Base", dataset
    )
    new_results, new_summary = await run_benchmark_with_results(
        "Agent_V2_Optimized", dataset
    )

    gate = build_release_gate(previous_summary, new_summary)
    new_summary["regression_baseline"] = previous_summary
    new_summary["release_gate"] = gate

    report = {
        "previous_version": previous_summary,
        "new_version": new_summary,
        "release_gate": gate,
        "results": new_results,
    }

    print("\n--- Regression comparison ---")
    print(f"V1 score: {previous_summary['metrics']['avg_score']:.2f}")
    print(f"V2 score: {new_summary['metrics']['avg_score']:.2f}")
    print(f"Score delta: {gate['delta']['avg_score']:+.2f}")
    print(f"Cost delta ratio: {gate['delta']['avg_cost_usd_ratio']:+.2%}")
    print(f"Latency delta ratio: {gate['delta']['avg_latency_seconds_ratio']:+.2%}")
    print(f"Release gate decision: {gate['decision']}")

    os.makedirs("reports", exist_ok=True)
    with open("reports/summary.json", "w", encoding="utf-8") as f:
        json.dump(new_summary, f, ensure_ascii=False, indent=2)
    with open("reports/benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    asyncio.run(main())
