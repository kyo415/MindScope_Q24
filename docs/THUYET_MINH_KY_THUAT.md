# THUYẾT MINH KỸ THUẬT WEBSITE MINDSCOPE Q24

## 1. Phạm vi và mục tiêu

Đề tài nghiên cứu tổng quát: **Phân tích và dự đoán sức khỏe tâm thần, tâm lý ở thanh thiếu niên tại Bhutan, Morocco và UAE** dựa trên khảo sát **GSHS 2016**. Website này là module minh họa **dự đoán câu trả lời Q24** (ý nghĩ tự tử trong 12 tháng qua) từ **10 biến khảo sát khác**, không thay thế đánh giá lâm sàng hoặc dự đoán toàn diện sức khỏe tâm thần.

## 2. Kiến trúc

```text
Trình duyệt (HTML / CSS / JavaScript)
        | GET /api/questions
        | POST /api/predict (10 câu + quốc gia + tùy chọn lưu)
        v
FastAPI (app.py) + Pydantic (kiểm tra cấu trúc JSON)
        |
        +-- prediction_service.py
        |     +-- kiểm tra mã + tính nhất quán Q20/Q21
        |     +-- đọc models/metadata.json
        |     +-- joblib.load(...) chọn 1 trong 3 Random Forest
        |     +-- model.predict_proba(...) -> Q24 Có / Không
        |
        +-- response_store.py CHỈ NẾU CHỌN ĐỒNG Ý LƯU
              +-- SQLite database/q24_responses.sqlite3
              +-- mã biên nhận bí mật (chỉ lưu SHA-256)
```

## 3. Các phương thức chính — trả lời khi giảng viên hỏi

| Tập tin | Hàm / API | Vai trò |
|---|---|---|
| `app.py` | `index()` | Trả trang HTML qua Jinja2. |
| `app.py` | `get_questions()` | Trả đúng 10 câu và đáp án từ định nghĩa khảo sát. |
| `app.py` | `model_info()` | Trả chỉ số đã đánh giá theo quốc gia. |
| `app.py` | `predict()` | Giao tiếp frontend và mô hình, chỉ lưu khi đồng ý. |
| `app.py` | `lookup()` / `delete()` | Tra cứu và xóa bản ghi bằng biên nhận bí mật. |
| `prediction_service.py` | `validate_answers()` | Kiểm tra thiếu/thừa câu, mã số ngoài quy ước, sự nhất quán Q20–Q21. |
| `prediction_service.py` | `get_model()` | Dùng `@lru_cache` để nạp model một lần cho mỗi quốc gia. |
| `prediction_service.py` | `infer()` | Tạo DataFrame 1 hàng đúng thứ tự biến, gọi `predict_proba` và quy đổi mã Q24. |
| `train_predictor.py` | `load_labeled_data()` | Đọc CSV và làm sạch nhãn/biến đầu vào. |
| `train_predictor.py` | `build_model()` | Tạo sklearn Pipeline: Imputer → OneHotEncoder → RandomForestClassifier. |
| `train_predictor.py` | `main()` | Chia dữ liệu, huấn luyện 3 mô hình, đánh giá và lưu Joblib + metadata. |
| `response_store.py` | `save_response()` | Chỉ tạo DB + lưu nếu opt-in, trả biên nhận ngẫu nhiên. |
| `response_store.py` | `retrieve_response()` | Truy vấn bằng SHA-256 của biên nhận. |
| `response_store.py` | `delete_response()` | Xóa bản ghi tương ứng với biên nhận. |
| `static/js/app.js` | `buildQuestions()` | Tạo các lựa chọn radio từ API bằng DOM an toàn. |
| `static/js/app.js` | `syncBullying()` | Q20 = 0 ngày thì Q21 tự là "không bị bắt nạt". |
| `static/js/app.js` | `updateProgress()` | Cập nhật số câu hoàn thành và tiến độ. |
| `static/js/app.js` | `submitPrediction()` | Gửi fetch POST tới Python và nhận kết quả JSON. |
| `static/js/app.js` | `showResult()` | Hiển thị phân loại Q24, điểm mô hình, F1/Recall/ROC-AUC. |

## 4. Huấn luyện và đánh giá

1. Đọc tệp CSV của từng quốc gia, lấy Q1, Q2, Q15–Q17, Q20–Q23, Q27 làm input.
2. Loại mẫu không có nhãn Q24 hợp lệ; mã trả lời không hợp lệ của input thành giá trị thiếu.
3. Q24 mã 1 = Có, mã 2 = Không; xây dựng nhãn nhị phân 1 cho Có, 0 cho Không.
4. Chia train/test 80/20 bằng `train_test_split(..., stratify=y, random_state=42)`.
5. Dùng `Pipeline` để bộ tiền xử lý (điền thiếu + mã hóa one-hot) **chỉ fit trên training set** để tránh rò rỉ thống kê của test.
6. `RandomForestClassifier(n_estimators=240, max_depth=12, min_samples_leaf=5, min_samples_split=10, class_weight='balanced_subsample', random_state=42)`.
7. Đánh giá accuracy, precision, recall, F1, ROC-AUC. Tính điểm phản hồi Có từ `predict_proba` và ngưỡng phân loại mặc định 0,5.
8. Tạo tệp model `.joblib` và `models/metadata.json`. Website tải model từ máy, không tự học từ câu trả lời mới.

**Lưu ý:** Đây là kết quả tập kiểm tra giữ lại, chưa chứng minh mô hình hoạt động trên người dùng mới, khác quốc gia/khác năm. Hạn chế lớn là class imbalance, dữ liệu thiếu và khả năng không khái quát. Không suy diễn mối liên hệ quan sát được thành nguyên nhân.

## 5. Lưu trữ và bảo mật

- Mặc định không lưu; không có tài khoản, không yêu cầu danh tính.
- Khi chọn opt-in, chỉ lưu 10 mã câu trả lời, tên quốc gia, mã phản hồi dự đoán, điểm mô hình và thời điểm; không lưu email, họ tên, IP.
- Biên nhận là chuỗi ngẫu nhiên và được **băm SHA-256** trước khi lưu vào SQLite. Người có mã có thể tra cứu hoặc xóa bản ghi. Bản ghi quá 30 ngày được dọn khi DB truy cập tiếp.
- SQLite **không mã hóa dữ liệu**; đây chỉ là bản demo chạy trên localhost. Nếu triển khai ra Internet phải thiết kế bảo vệ dữ liệu mới và xin chấp thuận phù hợp.

## 6. Kịch bản demo

1. Trong **File Explorer**, nhấp `CHAY_Q24_WINDOWS.bat`.
2. Chọn Bhutan → trả lời thông tin Q1, Q2 → sang bước trải nghiệm.
3. Chọn Q20 = 0 ngày, kiểm tra Q21 tự chọn không bị bắt nạt.
4. Hoàn tất Q22, Q23, Q27 → dự đoán → giải thích Q24, điểm mô hình, F1/Recall/AUC và giới hạn.
5. Làm lần khác, đánh dấu đồng ý lưu → dự đoán → kiểm tra mã biên nhận → tra cứu và xóa.
6. Xác nhận `database/q24_responses.sqlite3` chỉ xuất hiện khi có người dùng chọn lưu.
7. Chạy `python -m pytest -q` để kiểm tra backend.

## 7. Hướng phát triển trong tương lai

Nếu cần dự đoán thêm cô đơn hoặc mất ngủ (mục tiêu Q22/Q23), cần coi đó là bài toán mới, chọn lại input để **loại chính biến mục tiêu**, huấn luyện và đánh giá riêng. Không dùng dự đoán Q24 như thước đo tổng quát sức khỏe tâm thần.
