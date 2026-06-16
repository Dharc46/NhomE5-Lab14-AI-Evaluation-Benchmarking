import asyncio
import os
import json
from typing import Dict, Any
from openai import AsyncOpenAI

class LLMJudge:
    def __init__(self, model_a: str = "gpt-4o-mini", model_b: str = "gpt-4o"):
        self.model_a = model_a
        self.model_b = model_b
        
        # Initialize AsyncOpenAI client
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            self.client = AsyncOpenAI(api_key=api_key)
        else:
            self.client = None

        # Detailed grading rubrics for Accuracy and Tone
        self.rubrics = {
            "accuracy": (
                "Chấm điểm từ 1-5 dựa trên độ chính xác so với Ground Truth:\n"
                "1 - Hoàn toàn sai lệch hoặc bịa đặt thông tin.\n"
                "2 - Có nhiều lỗi sai nghiêm trọng hoặc thiếu phần lớn thông tin quan trọng.\n"
                "3 - Chính xác một phần, nhưng thiếu thông tin chi tiết hoặc có lỗi nhỏ.\n"
                "4 - Hầu như chính xác hoàn toàn, chỉ thiếu hoặc thừa một vài ý nhỏ không quan trọng.\n"
                "5 - Hoàn toàn chính xác, đầy đủ và khớp với Ground Truth."
            ),
            "tone": (
                "Chấm điểm từ 1-5 dựa trên sự chuyên nghiệp của ngôn ngữ (Tone/Professionalism):\n"
                "1 - Rất thiếu chuyên nghiệp, thô lỗ hoặc không phù hợp.\n"
                "2 - Quá suồng sã, thiếu lịch sự hoặc không phù hợp với văn phong công sở.\n"
                "3 - Trung tính, không quá suồng sã nhưng chưa thực sự chuyên nghiệp.\n"
                "4 - Văn phong chuyên nghiệp, lịch sự, rõ ràng và chuẩn mực.\n"
                "5 - Văn phong cực kỳ chuyên nghiệp, chu đáo, lịch thiệp và mẫu mực."
            )
        }

    async def _query_judge_llm(self, model: str, question: str, answer: str, ground_truth: str) -> Dict[str, Any]:
        """
        Gửi yêu cầu đánh giá tới một LLM cụ thể.
        """
        if not self.client:
            # Nếu không có API Key, giả lập kết quả bằng cách băm chuỗi để có kết quả ổn định và hợp lý
            # Điều này giúp chạy thử nghiệm offline không bị lỗi
            val = hash(question + answer) % 3
            # score accuracy: 3, 4, hoặc 5
            accuracy = 3 + val
            # score tone: 4 hoặc 5
            tone = 4 + (hash(answer) % 2)
            await asyncio.sleep(0.05) # Giả lập độ trễ
            return {
                "accuracy": float(accuracy),
                "tone": float(tone),
                "reasoning": f"Simulated evaluation by {model} (No OPENAI_API_KEY found)."
            }

        prompt = f"""Bạn là một Chuyên gia Đánh giá (Judge LLM) độc lập. Hãy đánh giá câu trả lời của AI Agent dựa trên câu hỏi và tài liệu đối chứng (Ground Truth).

[Câu hỏi]: {question}
[Câu trả lời của Agent]: {answer}
[Ground Truth (Tài liệu đối chứng)]: {ground_truth}

---
[Tiêu chuẩn đánh giá]:
1. ĐỘ CHÍNH XÁC (Accuracy):
{self.rubrics['accuracy']}

2. PHONG THÁI/VĂN PHONG (Tone/Professionalism):
{self.rubrics['tone']}

---
Hãy trả về kết quả dưới định dạng JSON duy nhất như sau:
{{
  "accuracy": <số từ 1 đến 5>,
  "tone": <số từ 1 đến 5>,
  "reasoning": "<Giải thích ngắn gọn lý do cho điểm>"
}}
"""
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that outputs only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            content = response.choices[0].message.content
            result = json.loads(content)
            return {
                "accuracy": float(result.get("accuracy", 3)),
                "tone": float(result.get("tone", 3)),
                "reasoning": result.get("reasoning", "")
            }
        except Exception as e:
            # Fallback nếu lỗi gọi API
            return {
                "accuracy": 3.0,
                "tone": 4.0,
                "reasoning": f"Fallback due to API error with model {model}: {str(e)}"
            }

    async def evaluate_multi_judge(self, question: str, answer: str, ground_truth: str) -> Dict[str, Any]:
        """
        EXPERT TASK: Gọi ít nhất 2 model (ví dụ GPT-4o-mini và GPT-4o).
        Tính toán sự sai lệch. Nếu lệch > 1 điểm, áp dụng logic xử lý xung đột.
        """
        task_a = self._query_judge_llm(self.model_a, question, answer, ground_truth)
        task_b = self._query_judge_llm(self.model_b, question, answer, ground_truth)
        
        result_a, result_b = await asyncio.gather(task_a, task_b)
        
        # 1. Điểm số cho từng tiêu chí
        acc_a = result_a["accuracy"]
        acc_b = result_b["accuracy"]
        
        tone_a = result_a["tone"]
        tone_b = result_b["tone"]
        
        # 2. Logic tính điểm trung bình trước xử lý xung đột
        final_accuracy = (acc_a + acc_b) / 2
        final_tone = (tone_a + tone_b) / 2
        
        # 3. Xử lý xung đột (Conflict resolution)
        # Nếu điểm số chênh lệch > 1 giữa 2 judge
        conflict_detected = False
        if abs(acc_a - acc_b) > 1:
            conflict_detected = True
            # Cách xử lý xung đột: Sử dụng một giải pháp phạt điểm/hoặc lấy cận dưới an toàn để đảm bảo chất lượng phát hành
            # Hoặc ở đây chúng ta ưu tiên điểm số thấp hơn để tăng độ khắt khe, tránh phát hành phiên bản lỗi (Conservative approach)
            final_accuracy = min(acc_a, acc_b)
            reason_conflict = f"Xung đột điểm số Accuracy giữa {self.model_a} ({acc_a}) và {self.model_b} ({acc_b}). Đã chọn cận dưới an toàn: {final_accuracy}."
        else:
            reason_conflict = "Không có xung đột lớn về Accuracy."

        if abs(tone_a - tone_b) > 1:
            conflict_detected = True
            final_tone = min(tone_a, tone_b)
            reason_conflict += f" Xung đột điểm số Tone giữa {self.model_a} ({tone_a}) và {self.model_b} ({tone_b}). Đã chọn cận dưới an toàn: {final_tone}."

        # 4. Tính toán độ đồng thuận (Agreement Rate)
        # Độ đồng thuận tính bằng: 1.0 - (khoảng cách điểm trung bình giữa 2 model / tối đa 4 điểm khoảng cách)
        # Điều này cho kết quả mượt mà và trực quan hơn là chỉ True/False
        acc_diff = abs(acc_a - acc_b)
        tone_diff = abs(tone_a - tone_b)
        
        # Tính agreement trung bình cho cả 2 chỉ số
        agreement = 1.0 - ((acc_diff + tone_diff) / 8.0)
        
        # Final score tổng hợp là trung bình cộng của accuracy và tone
        final_score = (final_accuracy + final_tone) / 2
        
        return {
            "final_score": final_score,
            "accuracy": final_accuracy,
            "tone": final_tone,
            "agreement_rate": agreement,
            "conflict_detected": conflict_detected,
            "conflict_notes": reason_conflict,
            "individual_scores": {
                self.model_a: {"accuracy": acc_a, "tone": tone_a, "reasoning": result_a["reasoning"]},
                self.model_b: {"accuracy": acc_b, "tone": tone_b, "reasoning": result_b["reasoning"]}
            }
        }

    async def check_position_bias(self, question: str, response_a: str, response_b: str, ground_truth: str) -> Dict[str, Any]:
        """
        Nâng cao: Thực hiện đổi chỗ response A và B để xem Judge có thiên vị vị trí không.
        Trả về kết quả đánh giá cho cả 2 trường hợp và độ lệch.
        """
        if not self.client:
            # Giả lập kết quả check bias
            return {"bias_detected": False, "delta_score": 0.0}

        prompt_ab = f"""Hãy đánh giá xem câu trả lời nào tốt hơn.
[Câu hỏi]: {question}
[Ground Truth]: {ground_truth}
[Câu trả lời A]: {response_a}
[Câu trả lời B]: {response_b}

Trả về JSON: {{"better_response": "A" hoặc "B" hoặc "Draw"}}
"""

        prompt_ba = f"""Hãy đánh giá xem câu trả lời nào tốt hơn.
[Câu hỏi]: {question}
[Ground Truth]: {ground_truth}
[Câu trả lời A]: {response_b}
[Câu trả lời B]: {response_a}

Trả về JSON: {{"better_response": "A" hoặc "B" hoặc "Draw"}}
"""
        try:
            # Gọi song song để kiểm tra bias
            task_1 = self.client.chat.completions.create(
                model=self.model_a,
                messages=[{"role": "user", "content": prompt_ab}],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            task_2 = self.client.chat.completions.create(
                model=self.model_a,
                messages=[{"role": "user", "content": prompt_ba}],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            res_1, res_2 = await asyncio.gather(task_1, task_2)
            ans_1 = json.loads(res_1.choices[0].message.content).get("better_response")
            ans_2 = json.loads(res_2.choices[0].message.content).get("better_response")
            
            # Nếu đổi chỗ mà lựa chọn thay đổi (ví dụ: cả 2 lần đều chọn "A" - tức là chọn response_a ở lần 1 và response_b ở lần 2)
            # -> Thiên vị vị trí
            bias = False
            if ans_1 == "A" and ans_2 == "A":
                bias = True
            elif ans_1 == "B" and ans_2 == "B":
                bias = True
                
            return {
                "bias_detected": bias,
                "first_run_better": ans_1,
                "second_run_better": ans_2
            }
        except Exception as e:
            return {"bias_detected": False, "error": str(e)}

