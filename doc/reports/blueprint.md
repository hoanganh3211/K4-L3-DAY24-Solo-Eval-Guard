# Blueprint CI/CD cho RAG và guardrails

Nhóm: Solo

Người phụ trách: Mai Hoàng Anh (MSSV: 2A202602857)

Đây là **đề xuất CI/CD**, không phải workflow đã được triển khai/chạy.
Nguồn kết quả: artifacts/ragas_50q.json, judge_results.json, guard_results.json.
Run timestamp: 2026-10-12T10:47:15.764824+00:00; guard models: ['gpt-4o-mini'].
Models generation/evaluator/judge từ A/B: generation: ['gpt-4o-mini-2024-07-18'] (artifacts/answers_50q.json); evaluator: ['gpt-4o-mini', 'text-embedding-3-small'] (artifacts/ragas_50q.json); judge: ['gpt-4o-mini'] (artifacts/judge_results.json).

## Kiến trúc và failure action

Input → Presidio → NeMo input → RAG → NeMo output → response.
Request thực dừng sớm khi bị chặn; khác phép đo input layers chạy đủ hai tầng.

Kiến trúc bảo vệ luồng dữ liệu 4 tầng nối tiếp:
1. **Tầng 1 (Presidio PII Analyzer & Anonymizer):** Quét phát hiện thông tin định danh cá nhân nhạy cảm gồm CCCD 12 số, CMND 9 số, số điện thoại Việt Nam (đầu số 03-09) và email. Nếu phát hiện PII xâm nhập, yêu cầu bị chặn ngay lập tức (short-circuit), không gửi tiếp vào NeMo hay LLM, giúp tiết kiệm chi phí và ngăn ngừa rò rỉ dữ liệu ngay tại gateway.
2. **Tầng 2 (NeMo Input Guardrail):** Kiểm tra nội dung câu hỏi thông qua self-check input flow cấu hình trên gpt-4o-mini. Ngăn chặn các hành vi prompt injection, jailbreak (DAN mode, giả lập quyền quản trị), off-topic (hỏi thơ ca, công thức nấu ăn, tỷ giá crypto) và yêu cầu trích xuất dữ liệu bí mật/mật khẩu hệ thống. Khi bị chặn, NeMo kích hoạt hành động từ chối chuẩn mực từ Colang flow ("Xin lỗi, tôi không thể thực hiện yêu cầu này...").
3. **Tầng 3 (RAG Retrieval & Generation):** Truy vấn chỉ được chuyển vào pipeline Hybrid search (BM25 + BGE-M3 dense) kết hợp FlashRank reranking và tổng hợp câu trả lời từ gpt-4o-mini khi vượt qua an toàn cả 2 tầng input.
4. **Tầng 4 (NeMo Output Guardrail):** Kiểm tra câu trả lời của mô hình với ngữ cảnh câu hỏi trước khi trả về cho người dùng. Nếu phát hiện câu trả lời vô tình làm lộ PII của cá nhân, mật khẩu admin hay dữ liệu bí mật chưa được che, NeMo sẽ redact và thay thế bằng câu thông báo từ chối an toàn.

Quản lý Secrets và Logging:
- Khóa bí mật API (OPENAI_API_KEY) được quản lý nghiêm ngặt qua biến môi trường (.env / Secret Manager), tuyệt đối không lưu cứng trong mã nguồn hay tài liệu commit.
- Mọi sự kiện vi phạm được ghi structured log gồm timestamp, rule bị vi phạm, mã hash của truy vấn và nhãn phân loại (presidio/nemo_input/nemo_output). Dữ liệu PII luôn được ẩn danh hóa (anonymize) trước khi ghi log nhằm tuân thủ quy định bảo vệ dữ liệu cá nhân.
- Cơ chế Fallback: Nếu dịch vụ guardrail bên ngoài gặp sự cố mạng hoặc timeout vượt quá ngưỡng 2000ms, hệ thống chuyển sang chế độ an toàn nghiêm ngặt (fail-closed cho các hành động nhạy cảm) và hướng dẫn người dùng liên hệ kênh trợ giúp chính thức helpdesk@cty.vn.

## Phạm vi và số đo latency

Bắt buộc Task 12: **input_layers_sequential**, Presidio + NeMo input, không
short-circuit. Engines tạo trước đo; có hai warm-up thật không tính vào mẫu.
Percentile nội suy tuyến tính từ raw samples; tổng từ tổng từng sample.

Số mẫu timed: 20; warm-up: 2;
phương pháp: linear.

| Layer / scope | P50 ms | P95 ms | P99 ms | Tình trạng |
|---|---|---|---|---|
| Presidio | 11.40 ms | 14.41 ms | 15.74 ms | Đạt ngân sách (<50ms) |
| NeMo input | 693.04 ms | 778.63 ms | 861.52 ms | Bottleneck chính (LLM API call) |
| Input guard sequential | 706.92 ms | 792.77 ms | 877.20 ms | Vượt ngân sách 500ms |
| RAG | chưa đo | chưa đo | chưa đo | Ngoài phạm vi bắt buộc |
| NeMo output | chưa đo | chưa đo | chưa đo | Ngoài phạm vi bắt buộc |
| Full guard / short-circuit request | chưa đo | chưa đo | chưa đo | Không suy từ input_guard_ms |

Input-layer budget target: 500ms; kết quả thực tế/budget_ok: P95 = 792.77 ms, budget_ok = False.

Phân tích Bottleneck và Kế hoạch tối ưu:
- Tầng Presidio chạy cục bộ bằng regex và rule engines đạt tốc độ cực nhanh với P50 = 11.40 ms và P95 = 14.41 ms, chiếm chưa tới 2% tổng thời gian xử lý.
- Bottleneck lớn nhất nằm ở tầng NeMo input rail với P95 = 778.63 ms do phải thực hiện lời gọi API mạng hai chiều tới mô hình gpt-4o-mini để thực hiện self-check input. Độ trễ mạng (RTT) cộng với thời gian suy luận của LLM khiến tổng thời gian tuần tự của input guard đạt P95 = 792.77 ms, vượt quá ngân sách mục tiêu 500ms.
- Đối với các tầng ngoài phạm vi bắt buộc (RAG, NeMo output và Full guard short-circuit): hiện tại được ghi nhận là "chưa đo". Kế hoạch thực hiện đo lường bổ sung khi đưa vào staging bao gồm: cấu hình OpenTelemetry trace spans bao quanh hàm truy xuất chunking/search/rerank, ghi nhận timestamp chuẩn microsecond cho từng giai đoạn, chạy 50 mẫu warm-up và 100 mẫu đo lường để tính toán P50/P95 độc lập.

## CI gates đề xuất

- RAGAS faithfulness ≥0.75, avg_score ≥0.65 trên 50 câu.
- Attacks ≥18/20 cho CI đề xuất; clean 8/8 allowed; output cases đúng.
- Full guard P95 <500ms chỉ áp dụng sau khi thực sự đo full guard.

Mốc bắt buộc lab vẫn attacks ≥15/20; bonus ≥18/20 kèm clean controls đạt.

Đề xuất kịch bản tích hợp CI/CD tự động (GitHub Actions / GitLab CI):
- Quy trình kiểm thử được kích hoạt tự động mỗi khi có Pull Request vào nhánh chính (main).
- Lệnh thực thi kiểm tra chất lượng pipeline:
  ```bash
  python scripts/run_experiments.py --phase all --live
  python scripts/check_lab.py --with-tests
  ```
- Cơ chế chặn: Bộ script kiểm tra sẽ trả về exit code khác 0 (nonzero) nếu có bất kỳ tiêu chí nào không đạt:
  1. Test offline thất bại (`pytest tests/` trả về lỗi).
  2. RAGAS faithfulness < 0.75 hoặc avg_score < 0.65 trên bộ dữ liệu 50 câu.
  3. Tỷ lệ chặn tấn công Adversarial < 18/20 hoặc phát hiện bất kỳ false positive nào trên bộ Clean (yêu cầu nghiêm ngặt 8/8 allowed).
  4. Bất kỳ ca kiểm thử output nhạy cảm nào bị rò rỉ (yêu cầu 4/4 output cases chính xác).
  5. Xuất hiện lỗi cú pháp, tài liệu báo cáo chứa placeholder chưa giải quyết hoặc vi phạm cam kết bảo mật.
- Lưu ý: Đây là đề xuất kiến trúc CI gate cho giai đoạn chuyển giao sản phẩm, quy trình này chưa được triển khai standing workflow trong repo học tập.

## Monitoring và cải tiến

Hệ thống giám sát sản xuất (Production Observability):
- Chỉ số theo dõi liên tục: Tỷ lệ vi phạm PII theo giờ, tỷ lệ kích hoạt NeMo guardrail, tỷ lệ người dùng bấm nút "Báo cáo phản hồi sai" (False Positive Rate), P50/P95/P99 latency của từng trạm kiểm soát, độ trôi dạt ngữ nghĩa (Embedding Drift) và chi phí token hàng ngày.
- Ngưỡng cảnh báo tức thời: Gửi cảnh báo Slack/PagerDuty khi P95 latency của input guard vượt quá 1200ms trong 3 phút liên tiếp, hoặc khi tỷ lệ truy vấn bị chặn tăng đột biến trên 20% trong khoảng thời gian ngắn (dấu hiệu của đợt tấn công từ chối dịch vụ hoặc luật kiểm duyệt bị cấu hình sai).
- Quy trình xử lý False Positives: Tích hợp nút phản hồi trên giao diện người dùng; các trường hợp người dùng đánh dấu bị chặn nhầm được ghi nhận vào hàng đợi kiểm duyệt. Đội ngũ kỹ sư dữ liệu định kỳ gắn nhãn lại và bổ sung vào bộ kiểm thử hồi quy (regression test set) hàng tuần.
- Bảo mật quyền riêng tư: Ẩn danh hóa và băm một chiều (hash) thông tin người dùng trước khi ghi vào kho log tập trung (ELK / CloudWatch); kỹ sư phụ trách chính sách và bảo mật là Mai Hoàng Anh.

Số liệu đo lường thực nghiệm của nhóm:
- RAGAS mean: 0.7211; Worst distribution: multi_hop (avg_score: 0.6184, faithfulness: 0.3467).
- Cohen’s κ: 1.0 (sự đồng thuận tuyệt đối 10/10 giữa LLM-as-a-Judge và nhãn con người).
- Attacks passed: 20/20 (tỷ lệ chặn đạt 100%); clean false_positive_rate: 0.0 (8/8 clean inputs được thông qua an toàn).

Đề xuất 4 giải pháp cải tiến có thể kiểm chứng:
1. **Nâng cao chất lượng cho Multi-hop queries:** Phân tích từ Phase A cho thấy phân bố multi_hop có faithfulness chỉ đạt 0.3467 do suy diễn vượt ngoài ngữ cảnh retrieved chunks. Cải tiến bằng cách áp dụng kỹ thuật Query Decomposition (phân rã câu hỏi phức hợp thành các truy vấn đơn) và Step-Back Prompting trước khi truy xuất, đặt mục tiêu nâng faithfulness của multi_hop lên trên 0.70.
2. **Tối ưu hóa Latency cho Tầng Guardrail:** Thay thế việc gọi API LLM gpt-4o-mini ở NeMo input rail bằng một mô hình phân loại intent/jailbreak nhỏ chạy cục bộ (như ModernBERT hoặc ONNX classifier được fine-tune) hoặc giải pháp Semantic Cache cho các mẫu câu an toàn phổ biến. Mục tiêu đưa P95 latency của input guard từ 792.77 ms xuống dưới 50 ms, giải quyết triệt để vấn đề nghẽn ngân sách độ trễ.
3. **Hiệu chỉnh Thiên vị Độ dài (Verbosity Bias):** Báo cáo Phase B ghi nhận Verbosity Win Rate đạt 100% trong các cặp câu trả lời có sự chênh lệch độ dài. Cải tiến prompt của LLM-as-a-Judge bằng cách đưa thêm quy tắc phạt câu trả lời dài dòng không cần thiết và chuẩn hóa độ dài câu trả lời (length normalization) trước khi so sánh, mục tiêu đưa verbosity win rate về mức cân bằng 45%-55%.
4. **Mở rộng Bộ Benchmark Kiểm thử:** Mở rộng tập đánh giá từ 50 câu (20 factual, 20 multi_hop, 10 adversarial) lên tối thiểu 200 câu đa dạng ngữ cảnh nội bộ, bổ sung thêm các vector tấn công đa ngôn ngữ (Multilingual Jailbreak) và Prompt Leaking phức tạp để nâng cao độ tin cậy của toàn bộ hệ thống đánh giá tự động.
