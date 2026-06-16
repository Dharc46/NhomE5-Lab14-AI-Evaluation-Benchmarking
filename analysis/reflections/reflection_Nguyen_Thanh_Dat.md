# Báo cáo cá nhân - [Nguyễn Thành Đạt]

- Họ và tên: Nguyễn Thành Đạt
- Mã sinh viên: 2A202600944
- Vai trò: Member 4 - Failure Analysis, Optimization, and Submission

## Đóng góp

Em phụ trách phần phân tích kết quả benchmark sau khi hệ thống chạy xong. Công việc chính của em là đọc các file `reports/summary.json` và `reports/benchmark_results.json`, xác định các case có điểm thấp nhất, gom nhóm lỗi theo nguyên nhân, và viết báo cáo `analysis/failure_analysis.md`.

Trong báo cáo failure analysis, em tổng hợp các chỉ số chính như pass rate, điểm trung bình của LLM judge, Hit Rate, MRR, Agreement Rate, latency, token usage và chi phí ước tính. Dù kết quả benchmark hiện tại không có case fail theo ngưỡng `final_score < 3`, em vẫn phân tích các case có điểm thấp nhất để tìm rủi ro tiềm ẩn trong pipeline.

## Phân tích lỗi

Em chia lỗi thành các nhóm chính:

- **Incomplete Answer:** Agent trả lời theo template nên chưa nêu đủ thông tin chi tiết từ tài liệu.
- **Retrieval Ranking Weakness:** Hit Rate đạt 100% nhưng MRR chỉ đạt 0.50, nghĩa là tài liệu đúng có xuất hiện nhưng thường chưa đứng đầu.
- **Evaluation Blind Spot:** Một số metric đang cố định hoặc mô phỏng, làm kết quả có thể đẹp hơn thực tế.
- **Regression Signal Weakness:** Agent V1 và V2 chưa khác biệt đủ rõ, nên release gate chưa chứng minh được cải tiến thực sự.
- **Judge Reliability Risk:** Agreement Rate đạt 100%, nhưng cần kiểm tra lại khi chạy bằng API key thật để tránh kết quả simulated.

Em cũng thực hiện phân tích 5 Whys cho ba nhóm case tiêu biểu: câu hỏi fact-check, câu hỏi reasoning và câu hỏi dạng list/completeness. Qua đó, em nhận thấy nguyên nhân gốc không chỉ nằm ở retrieval mà còn ở generation prompt, rubric đánh giá và cách thiết kế golden answer.

## Đề xuất tối ưu

Để giảm chi phí evaluation khoảng 30% mà vẫn giữ độ tin cậy, em đề xuất dùng chiến lược đánh giá nhiều tầng. Tất cả case có thể được chấm trước bằng judge rẻ hơn. Sau đó, hệ thống chỉ gọi judge mạnh hơn cho các case có điểm gần ngưỡng pass/fail, case hard/adversarial, hoặc case có xung đột giữa judge. Ngoài ra, nhóm nên cache kết quả judge cho các response không thay đổi và rút gọn prompt judge để giảm token.

## Bài học rút ra

Qua phần này, em hiểu rằng pass rate cao không có nghĩa hệ thống đã tốt hoàn toàn. Một benchmark đáng tin cậy cần nhìn vào nhiều tín hiệu cùng lúc: chất lượng câu trả lời, chất lượng retrieval, độ đồng thuận của judge, chi phí, latency và khả năng phát hiện regression. Đặc biệt, Hit Rate và MRR có ý nghĩa khác nhau: Hit Rate cho biết tài liệu đúng có được lấy ra hay không, còn MRR cho biết tài liệu đúng đứng ở vị trí cao đến mức nào.

Em cũng rút ra rằng failure analysis không nên chỉ liệt kê case sai, mà cần đi đến nguyên nhân gốc rễ bằng 5 Whys. Nếu không xác định đúng lỗi nằm ở retrieval, prompting, judging hay dataset, nhóm có thể tối ưu sai chỗ và làm benchmark trở nên kém tin cậy hơn.

## Việc cần cải thiện tiếp

- Thay agent mẫu bằng agent RAG thật để benchmark phản ánh chất lượng thực tế.
- Kết nối retrieval evaluation với `retrieved_ids` thật.
- Chạy judge bằng API key thật trước khi nộp chính thức.
- Tách rõ Agent V1 và Agent V2 để release gate có ý nghĩa hơn.
- Thêm nhiều hard cases, đặc biệt là out-of-context, ambiguous và prompt injection.
