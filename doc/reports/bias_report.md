# Đánh giá LLM Judge Phase B

Nhóm: Solo

Người phụ trách: Mai Hoàng Anh - 2A202602857

Nguồn: `artifacts/judge_results.json`; run timestamp: 2026-10-12T10:14:01.908845+00:00.
Models generation/judge: Generation: `gpt-4o-mini-2024-07-18`; Judge: `gpt-4o-mini`.

## Năm cặp A/B và hai lượt

Nguồn cố định: A từ artifacts/answers_50q.json:answer; B từ fixtures/human_labels_10q.json:model_answer; reference từ fixtures/test_set_50q.json:ground_truth.
Ids: 1, 5, 12, 21, 41. Không đổi nguồn sau khi xem kết quả judge.

| ID | Candidate A | Candidate B | Winner Pass 1 | Winner Pass 2 | Final Winner | Consistent | Scores P1 (A/B) | Scores P2 (A/B) | Lý do chính |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Nhân viên được nghỉ 3 ngày làm việc khi kết hôn. | Nhân viên được nghỉ 3 ngày làm việc có lương khi kết hôn. | B | B | B | True | 0.8 / 1.0 | 0.8 / 1.0 | B nêu rõ quyền lợi nghỉ có lương theo đúng chính sách |
| 5 | Tổng Giám đốc (CEO) là người phê duyệt cho đơn hàng trị giá 55 triệu VNĐ. | Cần Giám đốc phòng ban phê duyệt. | A | A | A | True | 1.0 / 0.0 | 1.0 / 0.0 | A chỉ đúng thẩm quyền CEO; B sai thẩm quyền phòng ban |
| 12 | Thưởng Tết tối thiểu cho nhân viên chính thức có từ 6 tháng trở lên là 1 tháng lương. | Nhân viên được thưởng Tết tối thiểu 1 tháng lương. | A | A | A | True | 1.0 / 0.7 | 1.0 / 0.7 | A nêu đủ điều kiện thời gian công tác từ 6 tháng trở lên |
| 21 | Không tìm thấy. | Được nghỉ 18 ngày phép (15 cơ bản + 3 thâm niên). Lương Senior từ 20 đến 35 triệu. | B | B | B | True | 0.0 / 1.0 | 0.0 / 1.0 | A từ chối trả lời; B tính đúng phép năm và khung lương |
| 41 | Mỗi nhân viên được hưởng 15 ngày phép năm. | Nhân viên được nghỉ 12 ngày phép năm. | A | A | A | True | 1.0 / 0.0 | 1.0 / 0.3 | A đúng theo chính sách v2024; B sai do lấy số liệu cũ v2023 |

Position bias count/rate: 0 (0.0%).
Verbosity win rate: 1.0 (100.0%); decisive cases: 5.

### Phân tích Position Bias và Verbosity Bias

- **Position Bias (0.0%):** Cả 5 cặp đều đạt sự nhất quán tuyệt đối giữa 2 lượt đánh giá ban đầu và hoán đổi vị trí (Pass 1 và Pass 2 quy đổi đều cho ra cùng một winner: B, A, A, B, A). Khi có tiêu chí đánh giá rõ ràng và reference chuẩn xác, `gpt-4o-mini` không bị ảnh hưởng bởi việc ứng viên nào xuất hiện trước.
- **Verbosity Bias (100.0%):** Trong toàn bộ 5 ca có kết quả phân định rõ ràng (decisive cases), câu trả lời dài hơn đều giành chiến thắng. Tuy nhiên, qua phân tích ngữ nghĩa:
  - Ở ID 1, B dài hơn A 9 ký tự vì bổ sung cụm từ mang tính pháp lý cốt lõi "có lương".
  - Ở ID 5 và ID 12, A dài hơn B vì trích dẫn đầy đủ chức danh thẩm quyền ("Tổng Giám đốc (CEO)") và điều kiện thâm niên.
  - Ở ID 21, A chỉ có 15 ký tự ("Không tìm thấy.") trong khi B đưa ra đầy đủ phép tính 18 ngày và dải lương.
  - Ở ID 41, A đưa ra 15 ngày (chính sách hiện hành) thay vì 12 ngày lỗi thời.
  Như vậy, độ dài trong các ca này tương quan trực tiếp với độ đầy đủ (completeness) và độ chính xác (accuracy) của thông tin chứ không phải do LLM thiên vị số lượng từ ngữ thuần túy.

## Calibration đúng model_answer

Helper đánh giá đúng question/model_answer đang có trong fixtures/human_labels_10q.json; không lấy answer mới của pipeline. Prompt chỉ nhận question, answer, reference. Không gửi human_label, human_note hoặc phân bố nhãn human vào prompt.

| ID | Model Answer Gốc | Nhãn Judge | Reasoning | Human Label | Agree |
|---|---|---|---|---|---|
| 1 | Nhân viên được nghỉ 3 ngày làm việc có lương khi kết hôn. | 1 | Trả lời chính xác số ngày và điều kiện có lương theo reference | 1 | True |
| 5 | Cần Giám đốc phòng ban phê duyệt. | 0 | Sai thẩm quyền; đơn hàng 55 triệu thuộc thẩm quyền Tổng Giám đốc | 0 | True |
| 12 | Nhân viên được thưởng Tết tối thiểu 1 tháng lương. | 1 | Nêu đúng mức thưởng Tết tối thiểu cho nhân viên đủ điều kiện | 1 | True |
| 21 | Được nghỉ 18 ngày phép (15 cơ bản + 3 thâm niên). Lương Senior từ 20 đến 35 triệu. | 1 | Tính đúng 18 ngày phép và nêu chính xác khung lương Senior | 1 | True |
| 23 | Hoàn trả 25 triệu vì chưa đủ 1 năm cam kết. | 1 | Nêu đúng số tiền hoàn trả đào tạo do vi phạm cam kết thâm niên | 1 | True |
| 29 | Trưởng phòng phê duyệt. Phạt 2% tháng trên 8 triệu. | 0 | Thiếu sự phê duyệt của Kế toán trưởng đối với mức tạm ứng trên 5 triệu | 0 | True |
| 33 | Phép: 19 ngày. Phụ cấp: 1.500.000 VNĐ/tháng. | 1 | Tính đúng tổng phụ cấp tháng và số ngày phép theo chính sách v2024 | 1 | True |
| 41 | Nhân viên được nghỉ 12 ngày phép năm. | 0 | Sai phiên bản; 12 ngày là chính sách cũ v2023, hiện hành là 15 ngày | 0 | True |
| 46 | Nhân viên thử việc không được nghỉ phép năm và phải xin nghỉ không lương nếu cần. | 1 | Khẳng định chính xác quy định cấm nghỉ phép năm đối với nhân viên thử việc | 1 | True |
| 50 | Được, miễn là đảm bảo kết nối an toàn. | 0 | Sai chính sách; công ty cấm tuyệt đối VPN cá nhân khi làm việc WFH | 0 | True |

Cohen’s κ: 1.0.
Observed/chance agreement và diễn giải:
- Tỷ lệ đồng thuận quan sát: $P_o = 10 / 10 = 1.0$.
- Tỷ lệ đồng thuận ngẫu nhiên: Với tập dữ liệu gồm 6 nhãn 1 và 4 nhãn 0, $P_e = (6/10 \times 6/10) + (4/10 \times 4/10) = 0.36 + 0.16 = 0.52$.
- Hệ số Cohen’s $\kappa = (1.0 - 0.52) / (1.0 - 0.52) = 1.0$.
- Kết quả đạt mức "Almost Perfect Agreement" theo thang đo Landis-Koch ($\kappa > 0.8$), vượt xa ngưỡng yêu cầu và đạt mốc bonus $\kappa > 0.6$.

## Giới hạn và cách dùng judge

- **Quy mô tập dữ liệu calibration:** Bộ kiểm định 10 câu hỏi nhãn con người là một tập mẫu tốt cho kiểm tra căn chỉnh (calibration), nhưng chưa đủ lớn để đại diện cho toàn bộ các tình huống ngôn ngữ phức tạp trong thực tế.
- **Tính chất của LLM Judge:** Mặc dù đạt $\kappa = 1.0$ trên bộ 10 câu, LLM Judge vẫn phụ thuộc chặt chẽ vào chất lượng của `reference`. Nếu reference không đầy đủ hoặc thiếu chi tiết, LLM Judge có thể đưa ra phán quyết thiếu chuẩn xác.
- **Khuyến nghị vận hành:**
  1. Trong quy trình CI/CD tự động, bắt buộc áp dụng kỹ thuật Swap-and-Average để triệt tiêu nguy cơ position bias tiềm ẩn.
  2. Các trường hợp phán quyết hòa ("tie") hoặc có điểm chênh lệch sít sao giữa 2 ứng viên cần được đưa vào hàng đợi kiểm duyệt bán tự động bởi chuyên viên con người (Human-in-the-Loop).
  3. Không coi LLM Judge là chân lý tuyệt đối mà xem như một bộ lọc đánh giá sơ bộ tốc độ cao.
