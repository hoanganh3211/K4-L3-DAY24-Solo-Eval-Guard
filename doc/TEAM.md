# Nhóm thực hiện K4 Track 3B

Tên nhóm: Solo

Repo chung: https://github.com/hoanganh3211/K4-L3-DAY24-Solo-Eval-Guard.git

Trưởng nhóm/người nộp: Mai Hoàng Anh - 2A202602857

Ngày lab/deadline áp dụng: 12/10/2026 — Asia/Ho_Chi_Minh (UTC+07:00)

Commit dùng để chấm: d198449e8885b11951d8b590fe1bd408e66af834 (bản commit hoàn thành toàn bộ CP0, Phase A, B, C, Blueprint trên branch main)

Mỗi nhóm nộp một repo. Điền đủ thành viên và một mục INDIVIDUAL cho từng người.
Thêm/xóa rows để khớp nhóm thật; nhóm làm độc lập gồm 1 thành viên.

## Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò / công việc thật | Bằng chứng |
|---|---|---|---|---|
| 1 | Mai Hoàng Anh | 2A202602857 | Thực hiện toàn bộ CP0, Phase A, B, C, Blueprint | Commits, artifacts và reports |

Người tích hợp/chạy batch/nộp link: Mai Hoàng Anh, tích hợp module m1-m5, chạy live runner cho toàn bộ các phase và nộp repo.

## Môi trường và chuẩn bị trước lớp

OS/Python/compiler: Windows 11, Python 3.11.9, MSVC runtime.
Virtualenv/dependencies/imports: Thiết lập .venv với các gói ragas, presidio-analyzer, presidio-anonymizer, spacy en_core_web_lg, jsonschema, sentence-transformers, qdrant-client. Unit test support 60/60 passed.
Models/Qdrant/50 answers đã chuẩn bị: Qdrant in-memory, BGE-M3 dense embeddings, BGE-reranker-v2-m3 cross-encoder, OpenAI gpt-4o-mini-2024-07-18 sinh 50 câu hỏi đầy đủ trong artifacts/answers_50q.json.

## INDIVIDUAL

### MaiHoangAnh-2A202602857

- Phần được giao và phần thực tế đã làm: Thực hiện độc lập 100% toàn bộ các phase của bài lab (Solo):
  1. CP0: Thiết lập môi trường .venv, cài đặt Presidio Analyzer/Anonymizer, spaCy model en_core_web_lg, tích hợp 5 module RAG từ Day 18 (m1-m5), chạy live generation sinh 50 answers qua gpt-4o-mini lưu trong artifacts/answers_50q.json.
  2. Phase A: Triển khai 4 tasks trong src/phase_a_ragas.py, chạy thực nghiệm RAGAS live 50 câu, đạt bonus Adversarial (0.6892) < Factual (0.8397), hoàn thiện báo cáo phân tích failure clusters tại doc/reports/failure_clusters.md.
  3. Phase B: Triển khai 4 tasks trong src/phase_b_judge.py, chạy pairwise LLM-as-a-Judge với swap-and-average, căn chỉnh nhị phân 10 câu đạt độ đồng thuận Cohen's kappa = 1.0 (đạt bonus kappa > 0.6), hoàn thiện báo cáo bias tại doc/reports/bias_report.md.
  4. Phase C & Blueprint: Triển khai 5 tasks trong src/phase_c_guard.py gồm Presidio PII scan, NeMo input & output rails, đánh giá 28 inputs (20/20 attacks blocked, 8/8 clean allowed - đạt bonus), đo P95 latency trên 20 samples, và hoàn thành đề xuất kiến trúc CI/CD tại doc/reports/blueprint.md.
- Bằng chứng: artifacts/answers_50q.json, artifacts/ragas_50q.json, artifacts/judge_results.json, artifacts/guard_results.json, các báo cáo tại doc/reports/ (failure_clusters.md, bias_report.md, blueprint.md), và toàn bộ mã nguồn trong src/.
- Cách kiểm tra: python scripts/check_lab.py --with-tests (86/86 unit tests passed, 0 failed checks).
- Điều đã học: Hiểu sâu sắc cơ chế đánh giá 4 metrics RAGAS, bản chất các cụm lỗi (failure clusters), phương pháp đo lường và triệt tiêu position bias trong LLM-as-a-Judge, kiến trúc phòng thủ đa tầng (Defense-in-Depth) với Presidio và NeMo Guardrails, cùng quy chuẩn thiết kế hệ thống CI/CD cho các ứng dụng GenAI trong sản xuất.
- Giới hạn/cách xử lý: Triển khai Qdrant in-memory thay thế cho Docker daemon trên Windows; cấu hình Presidio lọc đúng các PII entities mục tiêu để tránh false positive trên tiếng Việt; tinh chỉnh prompt NeMo để phân biệt rõ câu hỏi chính sách độ dài mật khẩu và yêu cầu mật khẩu trái phép.
- Nguồn/AI hỗ trợ nếu có: Sử dụng AI coding assistant hỗ trợ tra cứu cú pháp và tự động hóa kiểm thử; toàn bộ kết quả thực nghiệm và đo lường latency được chạy thực tế 100% trên môi trường local với OpenAI API.

## Cập nhật sau khi nộp

Bản nộp chính thức đúng hạn, không có cập nhật phát sinh sau deadline.
