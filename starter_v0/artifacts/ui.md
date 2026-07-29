# Kế hoạch triển khai Giao diện Streamlit (Research Agent UI)

Tài liệu này ghi nhận kế hoạch và kết quả xây dựng ứng dụng giao diện tương tác (Streamlit App) cho Research Agent, hỗ trợ chạy thử nghiệm, so sánh và đánh giá các phiên bản từ `v0` đến `v4`.

---

## 1. Thiết lập môi trường (Setup)

- Thêm thư viện `streamlit>=1.30.0` vào cuối file `requirements.txt`.
- Đảm bảo các thư viện phụ trợ khác đã cài đặt đầy đủ.

---

## 2. Thiết kế giao diện `app.py`

File ứng dụng giao diện chính nằm tại [app.py](file:///c:/Users/nguyenloc/OneDrive/Desktop/vinAi/day_4/lab/Day04-C401-Prompt-Engineering-Tool-Calling-Labs-student-k3/starter_v0/app.py) bao gồm các thành phần:

### Sidebar (Cấu hình hệ thống & Chọn phiên bản)
1. **Model Provider Settings**:
   - Chọn Provider (`openrouter`, `openai`, `anthropic`, `gemini`).
   - Nhập tên Model (mặc định lấy theo provider đã chọn).
2. **Version Selector (Bộ chọn phiên bản)**:
   - Cho phép chọn phiên bản: `v0`, `v1`, `v2`, `v3`, `v4`.
   - **Tự động Reset Chat:** Khi chuyển đổi giữa các phiên bản, lịch sử chat cũ sẽ tự động được làm sạch để tránh lẫn lộn ngữ cảnh.
   - **Xem cấu hình:** Hỗ trợ xem nhanh nội dung của system prompt và danh sách các tool trong tab phụ thông qua hộp mở rộng.
3. **Test Case Runner (Bộ chọn kịch bản kiểm thử thông minh)**:
   - **Chọn Test Suite:** Cho phép lựa chọn giữa `base` (eval_base.json), `group` (eval_group.json - bộ test case nhóm tự thiết kế), và `extension` (eval_research_extension.json).
   - **Sắp xếp thông minh theo trạng thái:** Quét file log chạy gần đây nhất của phiên bản hiện tại để gắn nhãn trạng thái Đúng/Sai cho từng case. Đẩy toàn bộ các case bị thất bại **`❌ [FAIL]`** lên đầu danh sách để chọn nhanh, các case chưa test **`⚪ [UNTESTED]`** ở giữa, và các case đã đạt **`✅ [PASS]`** xuống cuối danh sách.
   - Nút **"Load Test Case to Chat"** sẽ tự động nạp chuỗi hội thoại/câu hỏi của case đó vào khung chat.
4. **Version Log Summary (Bảng tóm tắt kết quả nâng cấp)**:
   - Đọc trực tiếp từ file `version_log.csv` và hiển thị bảng so sánh điểm số trước/sau (Before/After metric) của các phiên bản mà không hiển thị các chuỗi mã băm thô gây nhiễu giao diện.

### Main Panel (Khung Chat, Trace và Đánh giá thời gian thực)
1. **Khung Chat**:
   - Sử dụng `st.chat_message` hiển thị trực quan lịch sử hội thoại giữa Người dùng và Agent.
2. **Quá trình thực thi Tool (Tool Trace)**:
   - Khi Agent chạy, hiển thị trực quan các vòng gọi tool (rounds) thông qua các hộp trạng thái:
     - Tên Tool đang gọi + Tham số truyền vào (Arguments).
     - Kết quả phản hồi từ Tool (Success/Error).
3. **Đánh giá Đúng/Sai thời gian thực**:
   - Tái sử dụng logic chấm điểm `evaluate_phase_b` từ file `run_eval.py`.
   - Đối chiếu các tool thực tế mà Agent gọi với dữ liệu kỳ vọng (`expect`) của test case để báo kết quả **✅ CORRECT (ĐÚNG)** hoặc **❌ SAI (INCORRECT)** kèm chi tiết lỗi mismatch trực tiếp trên màn hình.
4. **Lưu lịch sử (Transcripts)**:
   - Tự động lưu lại transcript phiên chat dưới dạng tệp `.transcript.json` trong thư mục `transcripts/` để nộp bài.

---

## 3. Quy trình kiểm thử & Xác thực UI

1. **Khởi chạy local**:
   ```bash
   streamlit run app.py
   ```
2. **Kiểm tra chức năng**:
   - Kiểm tra xem app có mở được tại `http://localhost:8501`.
   - Chọn suite `group` -> Chọn case `G09_chat_meta_no_tool` ở phiên bản `v0` -> Chạy thử -> Xem kết quả báo lỗi `SAI` trên màn hình.
   - Chuyển sang phiên bản `v4` -> Toàn bộ khung chat reset -> Load lại case đó -> Chạy thử -> Xem kết quả báo **ĐÚNG** nhờ các cập nhật prompt mới nhất.
