# Báo cáo Phân tích Thất bại (Failure Analysis Report)

## 1. Tổng quan Benchmark

- **Phiên bản đánh giá:** Agent_V2_Optimized
- **Tổng số cases:** 50
- **Pass/Fail:** 50/0
- **Pass rate:** 100%
- **Điểm LLM-Judge trung bình:** 4.16 / 5.0
- **Faithfulness trung bình:** 0.90
- **Relevancy trung bình:** 0.80
- **Hit Rate:** 100%
- **MRR:** 0.50
- **Agreement Rate giữa các judge:** 100%
- **Latency trung bình:** 0.512 giây/case
- **Token trung bình:** 150 tokens/case
- **Chi phí ước tính:** 0.005625 USD cho 50 cases
- **Release Gate:** Release

Kết quả hiện tại không có case bị đánh dấu `fail` theo ngưỡng `final_score < 3`. Tuy nhiên, phân tích lỗi vẫn cần thiết vì benchmark cho thấy một số dấu hiệu rủi ro: MRR chỉ đạt 0.50, câu trả lời agent còn dùng dạng mẫu, và judge trong lần chạy hiện tại có thể đang fallback sang chế độ simulated nếu không có `OPENAI_API_KEY`.

## 2. Phân nhóm lỗi (Failure Clustering)

| Nhóm lỗi | Số lượng ước tính | Dấu hiệu quan sát | Nguyên nhân dự kiến |
|----------|-------------------|-------------------|---------------------|
| Incomplete Answer | 8 | Một số case đạt 3.5/5 dù vẫn pass | Agent trả lời theo template, chưa trích xuất trực tiếp chi tiết trong tài liệu |
| Retrieval Ranking Weakness | 50 | Hit Rate 1.0 nhưng MRR chỉ 0.5 | Tài liệu đúng có xuất hiện, nhưng thường không đứng vị trí đầu tiên |
| Evaluation Blind Spot | 50 | Faithfulness và retrieval score đang gần như cố định | Evaluator hiện còn mock, chưa đo trực tiếp trên context thực tế |
| Regression Signal Weakness | 50 | V1 và V2 có điểm gần như giống nhau | Hai phiên bản agent chưa khác biệt đủ rõ để regression gate phản ánh cải tiến thật |
| Judge Reliability Risk | 50 | Agreement Rate 1.0 tuyệt đối | Có khả năng kết quả quá "đẹp" do simulated judge hoặc hai judge chưa độc lập thực sự |

Các case có điểm thấp nhất trong benchmark gồm:

- "Khi nào phải khóa máy tính?" - final score 3.5
- "Phép bệnh có giới hạn không?" - final score 3.5
- "Đánh giá hiệu suất được thực hiện bao nhiêu lần mỗi năm?" - final score 3.5
- "Những gì được bao gồm trong ngân sách đào tạo?" - final score 3.5
- "Ai phải phê duyệt các khóa học?" - final score 3.5
- "Có thể lựa chọn khách sạn nào?" - final score 3.5
- "Bảo hiểm sức khỏe bắt đầu khi nào?" - final score 3.5
- "Hành vi nào là không được chấp nhận?" - final score 3.5

## 3. Phân tích 5 Whys

### Case #1: "Khi nào phải khóa máy tính?"

1. **Symptom:** Agent pass nhưng chỉ đạt 3.5/5, câu trả lời chưa nêu trực tiếp rằng máy tính phải được khóa khi vắng mặt.
2. **Why 1:** Câu trả lời sinh ra theo template chung thay vì trả lời đúng ý từ context.
3. **Why 2:** Agent mẫu chưa có bước trích xuất evidence cụ thể từ document được retrieve.
4. **Why 3:** Pipeline hiện chỉ mô phỏng RAG, chưa dùng retrieved document để tạo câu trả lời có căn cứ.
5. **Why 4:** Benchmark runner nhận `contexts` nhưng chưa kiểm tra chặt chẽ câu trả lời có bám vào context hay không.
6. **Root Cause:** Prompting/generation stage chưa được triển khai thật; agent còn là mock nên chất lượng câu trả lời chưa phản ánh năng lực RAG thực tế.

### Case #2: "Có thể lựa chọn khách sạn nào?"

1. **Symptom:** Case dạng reasoning chỉ đạt 3.5/5, trong khi tài liệu yêu cầu khách sạn phải được phê duyệt trước.
2. **Why 1:** Agent không diễn giải được ràng buộc chính sách thành câu trả lời trực tiếp cho người dùng.
3. **Why 2:** Prompt chưa yêu cầu trả lời ngắn gọn kèm điều kiện bắt buộc và không được suy diễn ngoài tài liệu.
4. **Why 3:** Dataset có phân loại `hard/reasoning`, nhưng evaluator chưa áp dụng rubric riêng cho câu hỏi cần suy luận.
5. **Why 4:** Failure clustering chưa được tự động hóa theo loại câu hỏi, nên lỗi reasoning dễ bị che bởi pass rate cao.
6. **Root Cause:** Thiếu rubric và prompt chuyên biệt cho reasoning cases; agent mới dừng ở trả lời mẫu.

### Case #3: "Những gì được bao gồm trong ngân sách đào tạo?"

1. **Symptom:** Case yêu cầu liệt kê đạt 3.5/5, có nguy cơ thiếu các mục như sách, hội thảo, chứng chỉ.
2. **Why 1:** Agent không bắt buộc phải trả lời đủ danh sách các entity trong tài liệu.
3. **Why 2:** Judge chỉ chấm tổng quan accuracy/tone, chưa kiểm tra coverage từng ý quan trọng.
4. **Why 3:** Golden answer đang là toàn bộ đoạn document hoặc một câu ngắn, chưa tách thành checklist các facts bắt buộc.
5. **Why 4:** Evaluation chưa có metric cho completeness hoặc key-fact coverage.
6. **Root Cause:** Golden dataset và judge rubric chưa đủ chi tiết cho dạng câu hỏi list/completeness.

## 4. Kế hoạch cải tiến (Action Plan)

- [ ] Thay agent mẫu bằng agent RAG thật: retrieve document, lấy `retrieved_ids`, đưa context vào prompt, và trả lời trực tiếp dựa trên evidence.
- [ ] Cập nhật retrieval evaluation để tính Hit Rate/MRR từ `ground_truth_doc_id` và `retrieved_ids` thật thay vì dùng điểm cố định.
- [ ] Bổ sung rubric completeness cho câu hỏi dạng list và reasoning.
- [ ] Tách V1/V2 thành hai cấu hình thật: V1 dùng basic retrieval, V2 dùng reranking hoặc prompt tối ưu.
- [ ] Tự động xuất danh sách case điểm thấp nhất vào report để Member 4 phân tích nhanh hơn sau mỗi lần benchmark.
- [ ] Khi chạy chính thức, cấu hình `OPENAI_API_KEY` để judge không fallback sang simulated evaluation.

## 5. Đề xuất tối ưu chi phí khoảng 30%

Để giảm chi phí eval mà không làm giảm đáng kể độ tin cậy, nhóm có thể áp dụng chiến lược đánh giá nhiều tầng:

1. **Dùng judge rẻ cho toàn bộ cases:** Chạy `gpt-4o-mini` hoặc model nhỏ cho 100% test cases.
2. **Escalation có điều kiện:** Chỉ gọi judge mạnh hơn cho các case có điểm nằm gần ngưỡng pass/fail, có conflict, hoặc thuộc nhóm hard/adversarial.
3. **Cache kết quả judge:** Nếu question, expected answer và agent response không đổi, dùng lại điểm judge cũ.
4. **Giảm prompt judge:** Chỉ gửi context/evidence cần thiết thay vì gửi toàn bộ document.
5. **Chạy full multi-judge theo lịch:** Pull request nhỏ chỉ chạy smoke eval, còn full eval chạy trước release.

Với benchmark 50 cases, nếu chỉ khoảng 30-40% case cần gọi judge mạnh hơn thay vì gọi cả hai judge cho mọi case, chi phí judge có thể giảm trên 30% trong khi các case rủi ro vẫn được kiểm tra kỹ.

## 6. Kết luận

Release gate hiện cho quyết định `Release` vì tất cả chỉ số tổng hợp đều đạt ngưỡng. Tuy nhiên, kết quả này nên được xem là baseline kỹ thuật hơn là kết luận chất lượng cuối cùng, vì agent và evaluator vẫn còn một số phần mô phỏng. Bước cải tiến quan trọng nhất là thay mock agent/evaluator bằng pipeline RAG thật, sau đó chạy lại benchmark để failure analysis phản ánh lỗi hệ thống chính xác hơn.
