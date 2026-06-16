import asyncio
import time
from typing import List, Dict
# Import other components...

DEFAULT_COST_PER_1K_TOKENS = {
    "gpt-4o-mini": 0.00075,
    "unknown": 0.00100,
}

class BenchmarkRunner:
    def __init__(self, agent, evaluator, judge, cost_per_1k_tokens=None):
        self.agent = agent
        self.evaluator = evaluator
        self.judge = judge
        self.cost_per_1k_tokens = cost_per_1k_tokens or DEFAULT_COST_PER_1K_TOKENS

    def _extract_usage(self, response: Dict) -> Dict:
        metadata = response.get("metadata", {})
        total_tokens = int(metadata.get("tokens_used", metadata.get("total_tokens", 0)) or 0)
        prompt_tokens = int(metadata.get("prompt_tokens", 0) or 0)
        completion_tokens = int(metadata.get("completion_tokens", 0) or 0)

        if total_tokens == 0:
            total_tokens = prompt_tokens + completion_tokens

        model = metadata.get("model", "unknown")
        unit_cost = self.cost_per_1k_tokens.get(model, self.cost_per_1k_tokens["unknown"])
        estimated_cost_usd = (total_tokens / 1000) * unit_cost

        return {
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": round(estimated_cost_usd, 8),
            "cost_per_1k_tokens_usd": unit_cost,
        }

    async def run_single_test(self, test_case: Dict) -> Dict:
        start_time = time.perf_counter()
        
        # 1. Gọi Agent
        response = await self.agent.query(test_case["question"])
        latency = time.perf_counter() - start_time
        
        # 2. Chạy RAGAS metrics
        ragas_scores = await self.evaluator.score(test_case, response)
        
        # 3. Chạy Multi-Judge
        judge_result = await self.judge.evaluate_multi_judge(
            test_case["question"], 
            response["answer"], 
            test_case["expected_answer"]
        )

        usage = self._extract_usage(response)
        
        return {
            "case_id": test_case.get("id") or test_case.get("case_id"),
            "test_case": test_case["question"],
            "expected_answer": test_case.get("expected_answer"),
            "agent_response": response["answer"],
            "latency_seconds": round(latency, 4),
            "token_usage": usage,
            "ragas": ragas_scores,
            "judge": judge_result,
            "status": "fail" if judge_result["final_score"] < 3 else "pass"
        }

    async def run_all(self, dataset: List[Dict], batch_size: int = 5) -> List[Dict]:
        """
        Chạy song song bằng asyncio.gather với giới hạn batch_size để không bị Rate Limit.
        """
        results = []
        for i in range(0, len(dataset), batch_size):
            batch = dataset[i:i + batch_size]
            tasks = [self.run_single_test(case) for case in batch]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
        return results
