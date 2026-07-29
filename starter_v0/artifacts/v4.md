# Kế hoạch & Điều kiện Hoàn thành Tích hợp Tool mới & Đánh giá Nhóm

Tài liệu này định hình quy chuẩn thiết kế tool mới, đăng ký hệ thống, bộ test case đánh giá nhóm, và các tiêu chí bắt buộc phải tự kiểm tra để đạt điều kiện hoàn thành bài Lab.

---

## 1. Hướng dẫn thiết kế Tool mới (Bonus Track)

Mỗi tool mới được thêm vào bắt buộc phải thỏa mãn đầy đủ các điều kiện sau:

### 1.1. Cấu trúc thư mục của Tool
Mỗi tool phải nằm trong một thư mục riêng biệt tại: `tools/<tool_name>/`
- **Tài liệu hướng dẫn (`tools/<tool_name>/TOOL.md`)**:
  - Chứa Frontmatter YAML định nghĩa metadata (name, track, kind, inputs, outputs, side_effect, requires_confirmation...).
  - Phần mô tả (Description) phải đóng vai trò là prompt engineering: Nói rõ **khi nào dùng**, **khi nào không dùng**, quy ước tham số/giá trị mặc định (arguments conventions/defaults), và ranh giới xác nhận (confirmation boundary) nếu có side-effect.
- **Mã nguồn thực thi (`tools/<tool_name>/tool.py`)**:
  - Chứa hàm Python tự đóng gói xử lý các phép toán/logic tương ứng.

### 1.2. Đăng ký & Khai báo đồng bộ
- **Đăng ký trong `tools/__init__.py`**: Import và đưa vào từ điển `TOOL_FUNCTIONS`.
- **Khai báo trong `artifacts/tools.yaml`**: Mô tả schema tham số đầu vào đầy đủ cho LLM.

---

## 2. Thiết kế kịch bản đánh giá (`data/eval_group.json`)

Chúng ta sẽ thiết kế đúng **10 case** trong `data/eval_group.json`:
- **5 single-turn** sử dụng trường `query`.
- **5 multi-turn** sử dụng trường `turns` (phần tử cuối của turns là user turn đang được chấm).

### 2.1. Cấu trúc bắt buộc của mỗi case
- `id`
- `phase`: luôn là `"B"`
- `failure_type`: một trong `wrong_tool`, `wrong_arg_value`, `wrong_boundary`, `unnecessary_tool`, `out_of_scope`, `missing_info`.
- `expect`: chứa `tool_calls` mong đợi hoặc `no_tool: true`.
- `metadata.what_it_tests`: giải thích mục đích kiểm thử.

---

## 3. Quy trình thực thi & Đánh giá v3

1. **Chạy đánh giá bộ test case của nhóm**:
   ```bash
   python run_eval.py --provider openrouter --version v3 --suite group --eval-cases data/eval_group.json
   ```
2. **Chạy live chat (3 turns khác nhau) để ghi nhận transcript**:
   ```bash
   python chat.py --provider openrouter --version v3
   ```
   *Ba kịch bản live chat cần thực hiện:*
   - Lượt 1: Một câu hỏi nghiên cứu (research request) bình thường.
   - Lượt 2: Một yêu cầu thiếu thông tin ban đầu, sau đó được cung cấp bổ sung ở lượt tiếp theo (kiểm tra clarify + carryover).
   - Lượt 3: Một hành động nhạy cảm đòi hỏi hỏi lại/xác nhận an toàn (kiểm tra safety confirmation boundary).

---

## 4. Tiêu chí Tự Kiểm tra & Hoàn thành

Bài Lab được coi là hoàn thành khi đáp ứng đủ các bằng chứng:
- [x] **Tool mới**: Có đủ file `TOOL.md`, `tool.py`, đăng ký trong `tools/__init__.py`, khai báo trong `tools.yaml`, và có bằng chứng chạy thử (quicktest).
- [x] **Eval Group**: File `data/eval_group.json` có đúng 10 case (tỷ lệ 5/5).
- [x] **Lịch sử chạy**: Có file JSON kết quả chạy nhóm (`runs/v3_B_group_*.json`) và file transcript hội thoại nhiều lượt (`transcripts/*.transcript.json`).
