import json
import asyncio
import os
from typing import List, Dict
import random

DOCUMENTS = {
    "doc_001": {
        "title": "Company Password Policy",
        "content": "Mật khẩu phải dài ít nhất 12 ký tự, chứa chữ hoa, chữ thường, số và ký tự đặc biệt. Mật khẩu phải được đổi mỗi 90 ngày. Các nhân viên sẽ nhận được thông báo 14 ngày trước khi hết hạn."
    },
    "doc_002": {
        "title": "Remote Work Guidelines",
        "content": "Nhân viên làm việc từ xa phải sử dụng VPN có xác thực hai yếu tố. Các cuộc họp video phải được bảo mật bằng mật khẩu. Máy tính phải được khóa khi vắng mặt. Dữ liệu nhạy cảm không được lưu trữ trên máy cục bộ."
    },
    "doc_003": {
        "title": "Leave Management Procedure",
        "content": "Nhân viên có 20 ngày phép hàng năm. Phép bệnh không giới hạn nhưng cần hóa đơn y tế. Yêu cầu phép phải gửi trước 2 tuần. Phê duyệt được thực hiện bởi quản lý trực tiếp. Phép không sử dụng sẽ được tính thành tiền mặt khi kết thúc hợp đồng."
    },
    "doc_004": {
        "title": "Performance Review Process",
        "content": "Đánh giá hiệu suất hàng năm được thực hiện vào tháng 6 và tháng 12. Nhân viên phải hoàn thành tự đánh giá trước hạn. Quản lý sẽ làm việc với nhân viên để thiết lập OKR cho năm tiếp theo. Xếp hạng hiệu suất: Exceeds (Vượt trội), Meets (Đạt), Needs Improvement (Cần cải thiện)."
    },
    "doc_005": {
        "title": "Training & Development Budget",
        "content": "Mỗi nhân viên được cấp 2000 USD/năm cho đào tạo. Khóa học phải được phê duyệt trước bởi quản lý. Khoá học tại trường đại học có thể được tài trợ 50-100% tùy theo mức độ liên quan. Sách, hội thảo, chứng chỉ đều được bao gồm."
    },
    "doc_006": {
        "title": "Expense Reimbursement Policy",
        "content": "Hóa đơn phải được gửi trong vòng 30 ngày. Tất cả chi phí phải có biên lai gốc. Tiền ăn được phép 50 USD/ngày khi công tác. Khách sạn phải được phê duyệt trước. Chi phí vận chuyển phải là giá rẻ nhất hợp lý."
    },
    "doc_007": {
        "title": "Health Insurance Coverage",
        "content": "Bảo hiểm sức khỏe bắt đầu từ ngày đầu tiên của nhân viên. Phí bảo hiểm được chia giữa công ty (75%) và nhân viên (25%). Kế hoạch bao gồm khám chữa bệnh, nha khoa, và thị lực. Phương pháp sinh sản và sức khỏe tâm thần được bảo hiểm 100%."
    },
    "doc_008": {
        "title": "Code of Conduct",
        "content": "Tất cả nhân viên phải tuân thủ tiêu chuẩn lạm dụng tính dục bắt buộc. Độc lập không được chấp nhận. Bất cứ hành vi thù địch nào sẽ dẫn đến kỷ luật lên đến sa thải. Khiếu nại có thể được nộp cho HR hoặc đường dây nóng vô danh."
    },
    "doc_009": {
        "title": "Flexible Work Arrangements",
        "content": "Nhân viên có thể làm việc bốn ngày một tuần sau khi hoàn thành 6 tháng thử việc. Các cuộc họp chính phải có mặt trực tiếp ít nhất một lần mỗi hai tuần. Sơ đồ làm việc linh hoạt phải được phê duyệt bởi quản lý. Công việc tại nhà được hỗ trợ với phụ cấp thiết bị 500 USD."
    },
    "doc_010": {
        "title": "Emergency Response Procedures",
        "content": "Khi xảy ra sự cố, trước tiên hãy đến nơi an toàn. Báo cáo sự cố ngay cho quản lý tầng. Không khoe video hoặc chia sẻ trên phương tiện truyền thông xã hội. Công ty sẽ cung cấp sự hỗ trợ tâm lý sau sự cố."
    }
}

QUESTIONS = [
    ("Mật khẩu phải dài bao nhiêu ký tự?", "doc_001", "easy", "fact-check"),
    ("Mật khẩu phải được đổi bao lâu một lần?", "doc_001", "easy", "fact-check"),
    ("Những yêu cầu nào cho một mật khẩu hợp lệ?", "doc_001", "medium", "list"),
    ("Tôi nhận được thông báo trước khi hết hạn mật khẩu bao lâu?", "doc_001", "medium", "fact-check"),
    ("VPN có xác thực mấy yếu tố là bắt buộc?", "doc_002", "easy", "fact-check"),
    ("Khi nào phải khóa máy tính?", "doc_002", "medium", "fact-check"),
    ("Dữ liệu nhạy cảm có thể lưu ở đâu?", "doc_002", "hard", "reasoning"),
    ("Làm sao để bảo vệ cuộc họp video?", "doc_002", "medium", "fact-check"),
    ("VPN phải có những yêu cầu gì?", "doc_002", "hard", "reasoning"),
    ("Máy tính phải được bảo vệ như thế nào?", "doc_002", "medium", "fact-check"),
    ("Một nhân viên có bao nhiêu ngày phép hàng năm?", "doc_003", "easy", "fact-check"),
    ("Phép bệnh có giới hạn không?", "doc_003", "medium", "fact-check"),
    ("Yêu cầu phép phải gửi trước bao lâu?", "doc_003", "easy", "fact-check"),
    ("Phép không sử dụng sẽ xảy ra điều gì?", "doc_003", "medium", "reasoning"),
    ("Ai phê duyệt yêu cầu phép?", "doc_003", "easy", "fact-check"),
    ("Đánh giá hiệu suất được thực hiện bao nhiêu lần mỗi năm?", "doc_004", "easy", "fact-check"),
    ("Các xếp hạng hiệu suất là gì?", "doc_004", "medium", "list"),
    ("OKR được thiết lập khi nào?", "doc_004", "medium", "fact-check"),
    ("Tự đánh giá phải hoàn thành khi nào?", "doc_004", "hard", "reasoning"),
    ("Mỗi nhân viên được cấp bao nhiêu cho đào tạo?", "doc_005", "easy", "fact-check"),
    ("Khoá học tại trường đại học được tài trợ bao nhiêu phần trăm?", "doc_005", "medium", "fact-check"),
    ("Những gì được bao gồm trong ngân sách đào tạo?", "doc_005", "medium", "list"),
    ("Ai phải phê duyệt các khóa học?", "doc_005", "easy", "fact-check"),
    ("Hóa đơn phải được gửi trong vòng bao nhiêu ngày?", "doc_006", "easy", "fact-check"),
    ("Tiền ăn được phép bao nhiêu mỗi ngày?", "doc_006", "easy", "fact-check"),
    ("Điều gì cần thiết để hoàn lại tiền?", "doc_006", "medium", "list"),
    ("Có thể lựa chọn khách sạn nào?", "doc_006", "hard", "reasoning"),
    ("Phí bảo hiểm được chia như thế nào?", "doc_007", "medium", "fact-check"),
    ("Kế hoạch bảo hiểm bao gồm những gì?", "doc_007", "medium", "list"),
    ("Các phương pháp sinh sản được bảo hiểm bao nhiêu phần trăm?", "doc_007", "easy", "fact-check"),
    ("Bảo hiểm sức khỏe bắt đầu khi nào?", "doc_007", "easy", "fact-check"),
    ("Hành vi nào là không được chấp nhận?", "doc_008", "hard", "reasoning"),
    ("Hành động gì có thể dẫn đến sa thải?", "doc_008", "medium", "fact-check"),
    ("Khiếu nại có thể được nộp cho ai?", "doc_008", "medium", "list"),
    ("Nhân viên có thể làm việc bốn ngày một tuần sau bao lâu?", "doc_009", "easy", "fact-check"),
    ("Các cuộc họp chính cần có mặt trực tiếp bao thường xuyên?", "doc_009", "medium", "fact-check"),
    ("Phụ cấp thiết bị cho việc tại nhà là bao nhiêu?", "doc_009", "easy", "fact-check"),
    ("Ai phê duyệt sơ đồ làm việc linh hoạt?", "doc_009", "easy", "fact-check"),
    ("Bước đầu tiên khi xảy ra sự cố là gì?", "doc_010", "medium", "fact-check"),
    ("Ai nên báo cáo sự cố?", "doc_010", "medium", "fact-check"),
    ("Không được làm gì khi xảy ra sự cố?", "doc_010", "hard", "reasoning"),
    ("Công ty cung cấp hỗ trợ nào?", "doc_010", "easy", "fact-check"),
]

ADVERSARIAL_CASES = [
    ("Theo chính sách công ty, mật khẩu hợp lệ là gì?", "doc_001", "Mật khẩu phải dài ít nhất 12 ký tự, chứa chữ hoa, chữ thường, số và ký tự đặc biệt"),
    ("Có thể lưu trữ dữ liệu nhạy cảm ở đâu khi làm việc từ xa?", "doc_002", "Dữ liệu nhạy cảm không được lưu trữ trên máy cục bộ, chỉ được lưu trữ trên các hệ thống được xác thực"),
    ("Nếu tôi không sử dụng tất cả phép của mình trong năm, điều gì sẽ xảy ra?", "doc_003", "Phép không sử dụng sẽ được tính thành tiền mặt khi kết thúc hợp đồng"),
    ("Số lần mà nhân viên được đánh giá hiệu suất là bao nhiêu?", "doc_004", "Đánh giá hiệu suất được thực hiện hai lần mỗi năm: tháng 6 và tháng 12"),
    ("Tổng ngân sách đào tạo mà một nhân viên nhận được hàng năm là bao nhiêu?", "doc_005", "2000 USD mỗi năm"),
    ("Làm cách nào để có thể tái bảo hiểm các chi phí?", "doc_006", "Gửi hóa đơn gốc trong vòng 30 ngày"),
    ("Nếu một nhân viên muốn theo học khóa đại học trong giờ làm việc, họ nên làm gì?", "doc_005", "Nhân viên nên xin phép từ quản lý trước"),
    ("Phương pháp nào có thể được sử dụng để đề xuất một loại hình làm việc mới?", "doc_009", "Liên hệ với quản lý trực tiếp để xin phê duyệt"),
]

def generate_expected_answer(question: str, doc_id: str) -> str:
    doc_content = DOCUMENTS[doc_id]["content"]
    return doc_content

async def generate_golden_set() -> List[Dict]:
    qa_pairs = []
    used_docs = set()

    for question, doc_id, difficulty, q_type in QUESTIONS:
        expected_answer = generate_expected_answer(question, doc_id)
        qa_pairs.append({
            "question": question,
            "expected_answer": expected_answer,
            "context": DOCUMENTS[doc_id]["content"],
            "ground_truth_doc_id": doc_id,
            "document_title": DOCUMENTS[doc_id]["title"],
            "metadata": {
                "difficulty": difficulty,
                "type": q_type,
                "retrieval_required": True,
                "num_relevant_docs": 1
            }
        })
        used_docs.add(doc_id)

    for question, doc_id, expected_answer in ADVERSARIAL_CASES:
        qa_pairs.append({
            "question": question,
            "expected_answer": expected_answer,
            "context": DOCUMENTS[doc_id]["content"],
            "ground_truth_doc_id": doc_id,
            "document_title": DOCUMENTS[doc_id]["title"],
            "metadata": {
                "difficulty": "adversarial",
                "type": "reasoning",
                "retrieval_required": True,
                "num_relevant_docs": 1
            }
        })

    return qa_pairs

async def main():
    print("Generating 50+ high-quality test cases for Phase 1...")

    qa_pairs = await generate_golden_set()

    output_path = "data/golden_set.jsonl"
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for pair in qa_pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")

    print(f"[OK] Generated {len(qa_pairs)} test cases")
    print(f"[SAVED] {output_path}")
    print(f"\nDataset Breakdown:")
    print(f"  - Easy: {sum(1 for p in qa_pairs if p['metadata']['difficulty'] == 'easy')}")
    print(f"  - Medium: {sum(1 for p in qa_pairs if p['metadata']['difficulty'] == 'medium')}")
    print(f"  - Hard: {sum(1 for p in qa_pairs if p['metadata']['difficulty'] == 'hard')}")
    print(f"  - Adversarial: {sum(1 for p in qa_pairs if p['metadata']['difficulty'] == 'adversarial')}")

if __name__ == "__main__":
    asyncio.run(main())
