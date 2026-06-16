# Báo cáo cá nhân - Nguyễn Tài Khoa

- Họ và tên: Nguyễn Tài Khoa
- Mã sinh viên: 2A202600682
- Vai trò: Member 1 - Data & Retrieval Evaluation

## Đóng góp

Em phụ trách phần thiết kế Golden Dataset và script sinh dữ liệu tổng hợp (SDG) trong `data/synthetic_gen.py`. Đây là nền tảng của toàn bộ hệ thống đánh giá, vì mọi chỉ số benchmark ở các giai đoạn sau đều dựa trên chất lượng của bộ dữ liệu này.

Em đã xây dựng 50 test case chất lượng cao, được tạo từ 10 tài liệu chính sách công ty (mật khẩu, làm việc từ xa, quản lý phép, đánh giá hiệu suất, ngân sách đào tạo, hoàn chi phí, bảo hiểm sức khỏe, quy tắc ứng xử, sắp xếp công việc linh hoạt và quy trình ứng phó khẩn cấp). Mỗi test case bao gồm: câu hỏi, câu trả lời kỳ vọng, context, `ground_truth_doc_id`, tiêu đề tài liệu và metadata.

Điểm quan trọng nhất là em đã gắn `ground_truth_doc_id` cho từng case. Đây là dữ liệu bắt buộc để các bạn khác trong nhóm tính được Hit Rate và MRR ở bước đánh giá Retrieval, thay vì chỉ đánh giá câu trả lời cuối cùng.

## Thiết kế Golden Dataset

Em chia bộ dữ liệu theo nhiều cấp độ khó để benchmark phản ánh được nhiều khía cạnh của agent:

- **Easy (17 case):** Câu hỏi fact-check trực tiếp, trả lời được ngay từ một câu trong tài liệu.
- **Medium (19 case):** Câu hỏi dạng liệt kê (list) hoặc cần tổng hợp một vài chi tiết.
- **Hard (6 case):** Câu hỏi cần suy luận (reasoning), dễ gây hiểu nhầm nếu retrieval lấy sai context.
- **Adversarial (8 case):** Câu hỏi "lừa" được diễn đạt lại theo cách khác để kiểm tra xem agent có bám vào tài liệu thật hay không, nhằm phát hiện rủi ro hallucination.

Em cũng phân loại câu hỏi theo `type` (fact-check, list, reasoning) trong metadata, giúp các bạn ở giai đoạn phân tích lỗi có thể gom nhóm và truy vết nguyên nhân gốc rễ chính xác hơn.

## Bài học rút ra

Qua phần này, em hiểu rằng một hệ thống đánh giá chỉ tốt khi dữ liệu nền tảng đủ tốt. Nếu Golden Dataset toàn câu dễ, pass rate sẽ luôn cao nhưng không nói lên gì về chất lượng thật của agent. Vì vậy em chủ động thêm các case hard và adversarial để bộ dữ liệu có khả năng phân biệt agent tốt và agent yếu.

Em cũng nhận ra tầm quan trọng của việc tách bạch giữa đánh giá Retrieval và đánh giá Generation. Nếu không có `ground_truth_doc_id`, nhóm sẽ không biết một câu trả lời sai là do retrieval lấy nhầm tài liệu hay do generation diễn đạt kém. Hit Rate cho biết tài liệu đúng có được lấy ra hay không, còn MRR cho biết tài liệu đúng đứng ở vị trí nào trong kết quả — hai chỉ số này bổ sung cho nhau và đều cần dữ liệu ground truth chính xác.

## Việc cần cải thiện tiếp

- Thay phần sinh dữ liệu giả lập bằng việc gọi LLM API thật để tạo câu hỏi và câu trả lời đa dạng, tự nhiên hơn.
- Bổ sung các case multi-document (cần ghép thông tin từ nhiều tài liệu) để tăng độ khó cho retrieval.
- Thêm các case out-of-context (câu hỏi không có trong tài liệu) để kiểm tra khả năng agent từ chối trả lời thay vì bịa đáp án.
- Mở rộng số lượng tài liệu nguồn để Hit Rate và MRR có ý nghĩa thống kê rõ hơn khi pool tài liệu lớn hơn.
