# Kế hoạch triển khai Giao diện Streamlit (Research Agent UI)

Kế hoạch này chi tiết hóa cách thức xây dựng giao diện tương tác (Streamlit App) cho Research Agent, cho phép chạy thử nghiệm và so sánh kết quả qua các phiên bản `v0` đến `v3`.

---

## 1. Thiết lập môi trường (Setup)

- Thêm thư viện `streamlit>=1.30.0` vào cuối file `requirements.txt`.
- Đảm bảo các thư viện phụ trợ khác đã cài đặt đầy đủ.

---

## 2. Thiết kế giao diện `app.py`

Chúng ta sẽ tạo file mới `starter_v0/app.py` với cấu trúc như sau:

### Sidebar (Cấu hình hệ thống & Chọn phiên bản)
1. **Model Provider Settings**:
   - Chọn Provider (`openrouter`, `openai`, `anthropic`, `gemini`).
   - Nhập tên Model (mặc định lấy theo provider đã chọn).
2. **Version Selector (Bộ chọn phiên bản)**:
   - Cho phép chọn phiên bản: `v0`, `v1`, `v2`, `v3`.
   - Khi chọn phiên bản, hệ thống sẽ:
     - Tự động load `system_prompt` và `tools` tương ứng từ thư mục `artifacts/history/`.
     - Hiển thị `prompt_hash`, `tools_hash`, và chuỗi `artifact_version` (ví dụ: `v3+p65cf8283d409...`) để kiểm soát phiên bản đang chạy.
     - Cho phép xem nhanh nội dung của system prompt và danh sách các tool trong tab phụ.
3. **Test Case Runner (Chạy thử kịch bản có sẵn)**:
   - Đọc danh sách 20 test case từ file `data/eval_base.json`.
   - Cho phép chọn nhanh 1 test case từ dropdown (ví dụ: `R10_missing_handle` - *Tóm tắt 5 tweet mới nhất*).
   - Hiển thị metadata của test case (Skill kiểm tra, Độ khó, Tool mong đợi).
   - Nút **"Load Case"** sẽ tự động nạp chuỗi hội thoại/câu hỏi của case đó vào khung chat.

### Main Panel (Khung Chat & Vết chạy Tool & Đánh giá)
1. **Khung Chat**:
   - Sử dụng `st.chat_message` để hiển thị lịch sử hội thoại giữa Người dùng (User) và Agent.
2. **Quá trình thực thi Tool (Tool Trace)**:
   - Khi Agent chạy, hiển thị trực quan các vòng gọi tool (rounds) thông qua các hộp trạng thái (`st.status` hoặc `st.expander`):
     - Vòng thực thi (`Round 1`, `Round 2`...).
     - Tên Tool đang gọi + Tham số truyền vào (Arguments).
     - Kết quả phản hồi từ Tool (Success/Error).
3. **Đánh giá Đúng/Sai (Verification Evaluation)**:
   - Tái sử dụng logic so sánh `evaluate_phase_b` từ file `run_eval.py`.
   - Nếu câu hỏi hiện tại khớp với một test case có sẵn:
     - So sánh kết quả tool gọi thực tế của Agent với tool mong đợi (`expect`).
     - Hiển thị bảng thông báo: **✅ ĐÚNG (CORRECT)** hoặc **❌ SAI (INCORRECT)** kèm mô tả chi tiết lỗi mismatch (ví dụ: *Thiếu gọi clarify*, *Truyền sai limit=10 thay vì 5*).
     - Giúp người dùng thấy rõ sự cải thiện khi đổi phiên bản (`v0` -> `v3`) cho cùng một câu hỏi.
4. **Lưu lịch sử (Transcripts)**:
   - Mỗi phiên chat sẽ lưu lại thành file `.transcript.json` trong thư mục `transcripts/` để làm bằng chứng nộp bài (tương đương với `chat.py`).

---

## 3. Kế hoạch kiểm thử & Xác thực UI

1. **Khởi chạy local**:
   Chạy ứng dụng bằng lệnh:
   ```bash
   streamlit run app.py
   ```
2. **Kiểm tra chức năng**:
   - Kiểm tra xem app có mở được tại `http://localhost:8501`.
   - Chọn case `R12_confirm_before_send` ở phiên bản `v0` -> Chạy -> Xem trạng thái báo **SAI** (vì v0 tự gửi tin không hỏi xác nhận).
   - Giữ nguyên case đó, đổi sang phiên bản `v3` -> Chạy -> Xem trạng thái báo **ĐÚNG** (vì v3 đã gọi clarify yes/no để hỏi lại).
   - Kiểm tra trace của tool hiển thị chi tiết các arguments và kết quả.
