# Báo cáo cá nhân - Mai Văn Thuyên

- Họ và tên: Mai Văn Thuyên
- Mã sinh viên: 2A202600926
- Vai trò: Member 2 - Evaluation Engine & Multi-Judge Consensus

## Đóng góp

Em chịu trách nhiệm thiết kế và phát triển **Hệ thống đánh giá đa thẩm phán (Multi-Judge Consensus Engine)** trong module `engine/llm_judge.py` và tích hợp nó vào luồng benchmark chính của dự án. Đây là thành phần quan trọng quyết định tính khách quan và độ tin cậy của điểm số đánh giá câu trả lời của AI Agent.

Các công việc cụ thể em đã triển khai bao gồm:

1.  **Thiết kế Rubrics đánh giá chi tiết**: Định nghĩa rõ ràng thang điểm từ 1-5 cho hai tiêu chí quan trọng:
    *   **Accuracy (Độ chính xác)**: Đánh giá dựa trên mức độ khớp thông tin so với tài liệu đối chứng (Ground Truth).
    *   **Tone (Phong thái/Văn phong)**: Đánh giá tính chuyên nghiệp, lịch sự và chuẩn mực của câu trả lời.
2.  **Tích hợp Multi-Judge song song**: Sử dụng thư viện `AsyncOpenAI` kết hợp với `asyncio.gather` để truy vấn đánh giá song song từ hai mô hình Judge khác nhau (`gpt-4o-mini` và `gpt-4o`), giúp tối ưu hóa thời gian chạy dưới 2 phút cho toàn bộ test suite.
3.  **Xây dựng Logic xử lý xung đột (Conflict Resolution)**: Khi hai Judge có điểm số đánh giá lệch nhau quá lớn (lệch > 1 điểm), hệ thống sẽ tự động kích hoạt cơ chế chọn điểm an toàn (lấy cận dưới tối thiểu) để đảm bảo chất lượng phát hành nghiêm ngặt, ngăn ngừa lỗi lọt lưới.
4.  **Tính toán chỉ số đồng thuận (Agreement Rate)**: Thay vì chỉ đánh giá đồng ý/không đồng ý nhị phân, em đã triển khai công thức tính độ đồng thuận mượt mà dựa trên khoảng cách điểm chuẩn hóa giữa các Judge.
5.  **Hệ thống giả lập an toàn (Simulated Fallback)**: Thiết lập cơ chế tự động giả lập điểm số dựa trên hash nội dung câu hỏi/câu trả lời khi thiếu biến môi trường `OPENAI_API_KEY`, đảm bảo pipeline benchmark luôn có thể chạy offline mà không bị crash.
6.  **Kiểm tra thiên vị vị trí (Position Bias Check)**: Xây dựng helper hỗ trợ hoán đổi vị trí câu trả lời A và B để đánh giá xem Judge có xu hướng thiên vị câu trả lời xuất hiện trước hay không.

## Bài học rút ra

Qua buổi lab này, em đã học được rất nhiều kiến thức thực tế về AI Evaluation:

*   **Sự nguy hiểm của Single Judge**: Việc chỉ phụ thuộc vào một mô hình duy nhất (như GPT-4o) dễ dẫn đến sai số hệ thống hoặc position bias. Việc kết hợp nhiều Judge và đo lường sự đồng thuận giúp tăng độ tin cậy của kết quả benchmark một cách khoa học.
*   **Xử lý xung đột là bắt buộc**: Trong môi trường production, các mô hình ngôn ngữ lớn thường xuyên có những đánh giá lệch nhau. Logic giải quyết xung đột tự động bằng phương án "chọn cận dưới an toàn" (conservative approach) giúp giảm thiểu tối đa rủi ro release một agent có chất lượng kém.
*   **Tối ưu hóa thời gian chạy bằng Bất đồng bộ**: Đánh giá bằng LLM tốn rất nhiều thời gian chờ mạng. Sử dụng lập trình bất đồng bộ (`asyncio`) là chìa khóa để giữ hiệu năng hệ thống đạt chuẩn Expert (đánh giá 50 cases chỉ mất dưới 1 phút).

## Việc cần cải thiện tiếp

*   Bổ sung thêm mô hình thứ ba làm trọng tài (ví dụ: Claude 3.5 Sonnet hoặc Gemini 1.5 Pro) để giải quyết xung đột bằng phương pháp bỏ phiếu (majority voting) thay vì chỉ lấy cận dưới.
*   Tối ưu hóa cấu trúc prompt đánh giá để giảm thiểu lượng token tiêu thụ của các Judge, từ đó cắt giảm chi phí chạy benchmark.
*   Kết nối Position Bias Check trực tiếp vào pipeline chạy chính để tự động cảnh báo khi Judge có dấu hiệu thiên vị.
