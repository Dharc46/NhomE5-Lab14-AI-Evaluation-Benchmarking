# Báo cáo cá nhân - Nguyễn Khởi Lâm

- Họ và tên: Nguyễn Khởi Lâm
- Mã sinh viên: 2A202600607
- Vai trò: Member 3 - Benchmark Runner, Cost, and Release Gate

## Đóng góp

Em đã triển khai lớp chạy benchmark để so sánh hai phiên bản agent. Runner chạy các test case theo batch bất đồng bộ, ghi nhận độ trễ của từng case, lấy thông tin token usage từ metadata trong phản hồi của agent, và ước tính chi phí đánh giá bằng USD dựa trên đơn giá token của từng model.

Em cũng bổ sung phần báo cáo regression trong `main.py`. File `reports/summary.json` được tạo ra hiện bao gồm các chỉ số tổng hợp về chất lượng, retrieval, mức độ đồng thuận của judge, độ trễ, token và chi phí. File chi tiết `reports/benchmark_results.json` lưu summary của phiên bản cũ, summary của phiên bản mới, kết quả release gate và output benchmark của từng case.

## Logic Release Gate

Release gate tự động quyết định giữa `Release` và `Rollback` dựa trên ba nhóm ràng buộc theo hướng vận hành thực tế:

- Chất lượng: agent mới phải đạt điểm trung bình tối thiểu và không được giảm quá ngưỡng regression cho phép.
- Chi phí: chi phí ước tính trung bình trên mỗi case không được tăng quá ngưỡng đã cấu hình.
- Hiệu năng: độ trễ trung bình không được tăng quá ngưỡng đã cấu hình.

Cách làm này giúp quyết định release bớt cảm tính hơn, vì hệ thống kiểm tra đồng thời chất lượng, chi phí và độ trễ thay vì chỉ so sánh điểm câu trả lời.

## Bài học rút ra

Benchmark bất đồng bộ rất quan trọng vì quá trình đánh giá có thể chậm khi mỗi case phải gọi retrieval, generation và nhiều judge. Theo dõi chi phí cũng cần thiết vì chất lượng đánh giá có thể tăng nhưng chi phí vận hành lại trở nên quá cao để chạy thường xuyên. Vì vậy, một release gate thực tế cần bảo vệ cả chất lượng model lẫn các ràng buộc vận hành.
