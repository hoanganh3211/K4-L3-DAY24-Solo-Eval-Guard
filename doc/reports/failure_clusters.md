# Phân tích lỗi Phase A

Nhóm: Mai Hoàng Anh (Solo)

Người phụ trách: Mai Hoàng Anh - 2A202602857

Nguồn: `artifacts/ragas_50q.json`; run timestamp: 2026-10-12T10:04:34.285073+00:00.
Generation mode/fallback và điều kiện chạy: 100% sinh qua LLM (`gpt-4o-mini-2024-07-18`), không có fallback. Qdrant chạy in-memory, retrieval kết hợp BM25 và Dense Search (BGE-M3), rerank bằng BGE-reranker-v2-m3.
Models generation/evaluator: Generation: `gpt-4o-mini-2024-07-18`; Evaluator: `gpt-4o-mini`, `text-embedding-3-small` (từ m4_eval).

## Điểm theo distribution

| Metric | factual (20) | multi_hop (20) | adversarial (10) |
|---|---|---|---|
| faithfulness | 0.8833 | 0.3467 | 0.6667 |
| answer_relevancy | 0.6337 | 0.4021 | 0.4735 |
| context_precision | 0.9417 | 0.9042 | 0.9333 |
| context_recall | 0.9000 | 0.8208 | 0.6833 |
| avg_score | 0.8397 | 0.6184 | 0.6892 |

## Bottom 10 và nguyên nhân

| Rank | ID | Question | Distribution | Avg Score | Worst Metric | Diagnosis | Suggested Fix |
|---|---|---|---|---|---|---|---|
| 1 | 39 | So sánh yêu cầu mật khẩu giữa policy v1.0 và v2.0 về độ dài tối thiểu, thời hạn đổi và MFA. | multi_hop | 0.2500 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 2 | 40 | Nhân viên cấp Manager có thời hạn thử việc 90 ngày, đang trong tháng thứ 3, phát hiện vi phạm bảo mật. Họ nên và không nên làm gì theo chính sách? | multi_hop | 0.2917 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 3 | 21 | Một nhân viên Senior có 9 năm thâm niên được nghỉ bao nhiêu ngày phép năm và lương trong khoảng nào? | multi_hop | 0.3750 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 4 | 33 | Nhân viên Manager có thâm niên 12 năm: tổng phụ cấp hàng tháng và số ngày phép năm theo v2024 là bao nhiêu? | multi_hop | 0.3750 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 5 | 44 | Bao lâu phải đổi mật khẩu một lần? | adversarial | 0.3750 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 6 | 25 | Lương thử việc của nhân viên Junior mức cao nhất là bao nhiêu? | multi_hop | 0.3958 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 7 | 46 | Nhân viên thử việc có được nghỉ phép năm không? | adversarial | 0.4167 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 8 | 50 | Nhân viên Manager có thể dùng VPN cá nhân (như NordVPN) khi WFH để tăng bảo mật thêm không? | adversarial | 0.4167 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 9 | 34 | Nhân viên tạm ứng 4 triệu và một nhân viên khác tạm ứng 7 triệu: quy trình phê duyệt khác nhau thế nào? | multi_hop | 0.4167 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 10 | 9 | Nam nhân viên được nghỉ bao nhiêu ngày khi vợ sinh con? | factual | 0.5000 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |

### Đối chiếu và phân tích nguyên nhân các ca điển hình

1. **Nhóm Multi-hop (ID 39, ID 21, ID 33):**
   - *Hiện tượng:* Các câu hỏi yêu cầu tổng hợp thông tin từ 2 tài liệu/chính sách khác nhau (ví dụ ID 21: chính sách nghỉ phép năm + bảng khung lương; ID 39: chính sách mật khẩu v1.0 + v2.0).
   - *Nguyên nhân:* Mặc dù context_precision đạt cao (0.90-1.0), do thiết lập `top_k=3` ở tầng reranker, pipeline chỉ giữ 3 đoạn trích dẫn ngắn. Thông tin đa nguồn không thể tập hợp đủ trong 3 chunks này. Khi context thiếu một vế so sánh, prompt nghiêm ngặt của generator (`Nếu không có -> nói 'Không tìm thấy.'`) đã khiến mô hình trả lời "Không tìm thấy.", dẫn tới điểm faithfulness và answer_relevancy đều rơi về 0.0.
   - *Giải pháp:* Tăng `top_k` sau rerank từ 3 lên 5 cho các câu hỏi phức tạp, hoặc bổ sung kỹ thuật Query Decomposition (tách multi-hop query thành các sub-queries).

2. **Nhóm Adversarial (ID 44, ID 46, ID 50):**
   - *Hiện tượng:* ID 44 là bẫy version conflict (v1.0 quy định 90 ngày, v2.0 quy định 120 ngày); ID 46 là negation trap (hỏi về quyền lợi nhưng luật quy định cấm/không áp dụng).
   - *Nguyên nhân:* Corpus chứa đồng thời cả tài liệu cũ và tài liệu mới. Tầng retrieval đưa cả thông tin v1.0 và v2.0 vào context nhưng không có cơ chế lọc metadata theo ngày hiệu lực. Khi gặp mâu thuẫn chính sách, mô hình LLM có xu hướng từ chối trả lời hoặc phân vân, khiến điểm recall và faithfulness bị tụt giảm nghiêm trọng.
   - *Giải pháp:* Áp dụng metadata filtering ưu tiên phiên bản có `is_active: True` hoặc thêm cảnh báo phiên bản vào prompt.

3. **Nhóm Factual (ID 9):**
   - *Hiện tượng:* Câu hỏi về chế độ nghỉ khi vợ sinh con bị điểm thấp.
   - *Nguyên nhân:* Chunk trích xuất từ tài liệu nghỉ phép đặc biệt bị ngắt đoạn khiến thông tin số ngày nghỉ liên tục bị rơi vào ranh giới chunk, làm mô hình thiếu tự tin khi sinh câu trả lời.

## Matrix và nhóm yếu nhất

| Metric | factual (20) | multi_hop (20) | adversarial (10) | Tổng cộng |
|---|---|---|---|---|
| faithfulness | 3 | 16 | 4 | 23 |
| answer_relevancy | 15 | 4 | 1 | 20 |
| context_precision | 1 | 0 | 0 | 1 |
| context_recall | 1 | 0 | 5 | 6 |
| Tổng số câu | 20 | 20 | 10 | 50 |

Nhóm yếu theo mean thấp nhất: `multi_hop`; mean: `0.6184`.
Worst metric xuất hiện nhiều nhất: `faithfulness`; số câu: `23`.

### Phân tích nguyên nhân và đề xuất cải tiến

- **Vì sao multi_hop là nhóm yếu nhất:** Điểm trung bình của nhóm multi_hop chỉ đạt 0.6184 (thấp hơn factual 0.8397 và adversarial 0.6892). Nguyên nhân chủ đạo là `faithfulness` cực kỳ thấp (0.3467), chiếm tới 16/20 câu có metric yếu nhất là faithfulness. Việc RAG đơn tầng (single-step retrieval) không thể gom đủ các mắt xích thông tin nằm rải rác ở nhiều tài liệu khiến mô hình hallucinate hoặc chọn cách nói "Không tìm thấy".
- **Đề xuất kỹ thuật sửa chữa:**
  1. Nâng cấp retrieval thành Multi-step / Iterative RAG: Sau khi truy xuất lượt 1, dùng LLM xác định thông tin còn thiếu để sinh sub-query tìm kiếm lượt 2.
  2. Nâng ngưỡng Top-K của CrossEncoder từ 3 lên 5 để mở rộng cửa sổ ngữ cảnh.
  3. Cải tiến prompt generation để trích dẫn nguồn rành mạch theo từng ý thay vì trả lời gộp.
- **Cách kiểm chứng:** Sau khi cập nhật pipeline, chạy lại `python scripts/setup_answers.py --live` và `python scripts/run_experiments.py --phase a --live` để đối chiếu xem điểm `avg_score` của nhóm multi_hop có tăng vượt mốc 0.75 hay không.

## Bẫy adversarial và giới hạn

### Bẫy Version Conflict & Negation Traps
- Điểm trung bình của nhóm `adversarial` đạt 0.6892, thấp hơn rõ rệt so với nhóm `factual` (0.8397). Điều này phản ánh pipeline gặp khó khăn thực sự trước các câu hỏi gài bẫy.
- **Version Conflict (ID 44: đổi mật khẩu; ID 48: phép năm 2023 vs 2024):** Cả hai văn bản `mat_khau_v1.md` và `mat_khau_v2.md` đều có độ tương đồng từ vựng rất cao với câu hỏi. Reranker chấm điểm cả hai đoạn trích xấp xỉ nhau, khiến context chứa thông tin đối lập mà không có thứ tự ưu tiên phiên bản.
- **Negation Traps (ID 46: thử việc nghỉ phép năm; ID 50: dùng VPN cá nhân):** Dense search thường bắt các từ khóa "VPN", "thử việc", "phép năm" dựa trên ngữ nghĩa tích cực mà dễ bỏ qua toán tử phủ định ("KHÔNG được", "cấm sử dụng").

### Giới hạn thực nghiệm
- Tập dữ liệu gồm 50 câu (20 factual, 20 multi_hop, 10 adversarial) đủ để chỉ ra xu hướng nhưng kích thước mẫu adversarial (10 câu) còn khiêm tốn.
- Quá trình chạy dùng `gpt-4o-mini-2024-07-18` làm generation model và evaluator. Mô hình này rất thận trọng khi gặp prompt yêu cầu chỉ trả lời dựa trên context, dẫn đến hiện tượng từ chối trả lời khá phổ biến khi context bị thiếu hụt dù chỉ một phần nhỏ.
