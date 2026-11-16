# MindScope Q24 — Research Edition 2.0

**Đề tài:** Phân tích và dự đoán sức khỏe tâm thần, tâm lý ở thanh thiếu niên tại **Bhutan, Morocco và UAE** từ khảo sát GSHS 2016. Đây là **module ứng dụng website dự đoán phản hồi Q24**, không phải toàn bộ các phân tích của đề tài.

> **Lưu ý khoa học / đạo đức:** Q24 hỏi về việc nghiêm túc nghĩ đến tự tử trong 12 tháng qua. Q24 chỉ là **một biến khảo sát**, không đại diện cho toàn bộ sức khỏe tâm thần và không thể dùng để chẩn đoán, sàng lọc nguy cơ, khẳng định tình trạng an toàn hay đưa ra quyết định chăm sóc sức khỏe cho một cá nhân. Mô hình có sai số đáng kể.

## Bản sửa giao diện (tháng 11/2026)

- Sửa hiện tượng **trang trắng, chữ bé xíu ở góc và vòng tròn cực lớn** khi CSS không tải.
- CSS và JavaScript được gói trực tiếp trong `templates/index.html`, không cần browser tải `/static/css` để dựng giao diện; vẫn giữ các file CSS/JS gốc để chỉnh sửa.
- Bỏ các vòng tròn trang trí khổng lồ, ấn định kích thước SVG logo.
- Đổi cổng sang **5055** để tránh mở nhầm website bản cũ đang còn chạy ở cổng 5000.
- **Trong Chrome nhấn Ctrl+0 để đặt lại zoom 100%**, và **Ctrl+Shift+R** để tải lại trang.
- Không cần xóa Python hay huấn luyện lại mô hình. Dự án vẫn chỉ dự đoán Q24.
- Nếu tự chỉnh `static/css` hoặc `static/js`, chạy `python CAP_NHAT_GIAO_DIEN.py` rồi khởi động lại để cập nhật bản HTML tích hợp.

## Chạy trên Windows 10 / 11

1. Giải nén ZIP, mở thư mục `MindScope_Q24_GiaoDien_DaSua` bằng **File Explorer (Win+E)**.
2. Nhấp đúp file **`CHAY_Q24_WINDOWS.bat`** trong *File Explorer* (nhấp trong VS Code chỉ mở file).
3. Mở Chrome: **http://127.0.0.1:5055**.

Script dò **Python 3.13/3.12/3.11/3.14 64-bit** phù hợp, tự tạo `.venv_q24`, cài gói wheel tương thích với `scikit-learn==1.8.0` và thử cả 3 model trước khi chạy. Nếu chỉ có Python 3.15, cài thêm [Python 3.13 x64](https://www.python.org/downloads/), không cần xóa Python 3.15. Chi tiết: `HUONG_DAN_WINDOWS.txt`.

### Chạy thủ công từ Terminal (Windows)

Ở trong thư mục dự án, nếu đã cài Python 3.13:

```powershell
py -3.13 -m venv .venv_q24
.\.venv_q24\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.txt
.\.venv_q24\Scripts\python.exe app.py
```

macOS/Linux (Python 3.11–3.14):

```bash
python3 -m venv .venv_q24
.venv_q24/bin/python -m pip install -r requirements.txt
.venv_q24/bin/python app.py
```

## Giao diện và quy trình

- **01 — Thông tin chung:** Q1 (nhóm tuổi), Q2 (giới tính).
- **02 — Trải nghiệm:** Q15, Q16, Q17 (bạo lực và chấn thương), Q20, Q21 (bắt nạt).
- **03 — Cảm xúc & kết nối:** Q22 (cô đơn), Q23 (lo lắng ảnh hưởng giấc ngủ), Q27 (bạn thân).
- Chọn một trong ba quốc gia, trả lời 10 câu và bấm **Xem dự đoán Q24**.
- Trả về phân loại Q24 = 1 (*Có*) hoặc Q24 = 2 (*Không*), điểm mô hình và chỉ số F1/Recall/ROC-AUC từ tập kiểm tra riêng của quốc gia. Điểm mô hình **không phải xác suất lâm sàng**.
- Q20=0 ngày tự đồng bộ Q21=không bị bắt nạt; API độc lập cũng kiểm tra tính nhất quán.
- In / Lưu PDF bằng chức năng **In kết quả** của trình duyệt.
- Giao diện phản hồi, hoạt động trên điện thoại và máy tính, không dùng CDN hoặc cần Internet sau khi cài xong thư viện.

## Câu trả lời sẽ lưu ở đâu?

**Mặc định: KHÔNG lưu.** API chỉ nhận câu trả lời và trả dự đoán, không ghi xuống đĩa, không dùng cookie hay localStorage.

Nếu chọn hộp **“Tôi đồng ý lưu…”** ở cuối bước 3, server lưu đúng một bản ghi vào **`database/q24_responses.sqlite3`** trên máy chủ chạy ứng dụng (không phải máy của người truy cập nếu đưa server lên mạng). Nội dung: 10 mã trả lời, quốc gia, Q24 được dự đoán, điểm mô hình và thời điểm tạo. Không lưu tên, số điện thoại, email, IP hoặc user-agent. Sau khi lưu thành công, hệ thống cấp **mã biên nhận bí mật** để tra cứu/xóa bản ghi. DB chỉ lưu SHA-256 của mã biên nhận. Bản ghi quá 30 ngày được xóa khi có thao tác truy cập DB lần tiếp theo. Nếu máy ngừng sử dụng, nên xóa file DB thủ công. Không thể khôi phục bản ghi nếu mất mã biên nhận qua giao diện công khai.

**Quan trọng:** SQLite không mã hóa khi lưu trên ổ đĩa. Phiên bản này **chỉ nên chạy nội bộ tại 127.0.0.1 trên máy riêng** cho mục đích nghiên cứu/đồ án; **không đưa nguyên trạng lên hosting công khai** hoặc sử dụng để thu thập dữ liệu nhạy cảm từ người thật. Nếu triển khai trực tuyến, cần thiết kế thêm bảo mật, xác thực/quyền truy cập, mã hóa, chính sách bảo vệ dữ liệu, đánh giá đạo đức và thủ tục đồng ý phù hợp.

## Cấu trúc mã nguồn

```text
MindScope_Q24_GiaoDien_DaSua/
├── app.py                     # FastAPI: giao diện + API + đồng ý lưu/tra cứu/xóa
├── prediction_service.py      # Nội dung câu hỏi, kiểm tra đầu vào và suy luận
├── response_store.py          # SQLite, thời hạn lưu 30 ngày, mã biên nhận
├── train_predictor.py         # Huấn luyện lại 3 model khi cần
├── CHAY_Q24_WINDOWS.bat       # Chạy trên Windows
├── open_browser.py            # Chờ server mở rồi mới mở Chrome
├── HUONG_DAN_WINDOWS.txt
├── requirements.txt
├── requirements-dev.txt
├── models/                    # 3 Random Forest joblib và metadata.json
├── data/                      # 3 CSV và data/quy_uoc/ (mã hóa câu hỏi gốc)
├── database/README.txt        # Nơi lưu SQLite nếu đồng ý
├── static/css/style.css
├── static/js/app.js
├── static/favicon.svg
├── templates/index.html
├── docs/THUYET_MINH_KY_THUAT.md # Giải thích code khi bảo vệ đồ án
└── tests/test_app.py
```

## Quy trình Machine Learning

Nguồn: 3 file CSV GSHS 2016. **Biến mục tiêu Q24** được mã 1=“Có” và 2=“Không” trong tài liệu quy ước của dữ liệu. Input gồm `Q1, Q2, Q15, Q16, Q17, Q20, Q21, Q22, Q23, Q27`. Không đưa `Q24/Q25/Q26` vào biến đầu vào nhằm tránh rò rỉ nhãn từ các câu hỏi có liên quan trực tiếp.

`train_predictor.py` thực hiện: đọc CSV → xử lý mã trả lời không hợp lệ thành thiếu → lọc những bản ghi có nhãn Q24 hợp lệ → chia train 80% / test 20% có phân tầng → fit tiền xử lý trong pipeline chỉ trên train → `OneHotEncoder` các biến khảo sát → `RandomForestClassifier(class_weight='balanced_subsample')` → đánh giá tập test (Accuracy, Precision, Recall, F1, ROC-AUC) → lưu model `.joblib` và metadata. **Dự đoán trên website không tự cập nhật model; chỉ `train_predictor.py` mới tạo lại model.** Cài scikit-learn 1.8.0 để đọc model đã huấn luyện bằng phiên bản này. Chỉ tải model cục bộ tin cậy; joblib chứa pickle có thể thực thi code nếu lấy từ nơi không tin cậy.

Kết quả kiểm tra sẵn có trong `models/metadata.json`:

| Quốc gia | F1 | Recall | ROC-AUC | Số bản ghi kiểm tra |
|---|---:|---:|---:|---:|
| Bhutan | 0.308 | 0.436 | 0.700 | 1,498 |
| Morocco | 0.414 | 0.510 | 0.738 | 1,286 |
| UAE | 0.471 | 0.582 | 0.798 | 674 |

Chất lượng này chưa đủ để suy luận sức khỏe tâm thần của cá nhân, và có thể không khái quát cho người dùng website hiện tại (khác thời gian/quốc gia/nhóm tuổi khảo sát).

## API

- `GET /` — trang khảo sát Q24 duy nhất.
- `GET /api/questions` — câu hỏi và mã lựa chọn.
- `GET /api/model-info?country=Bhutan` — thống kê đánh giá model đã chọn.
- `POST /api/predict` — dự đoán với `{ "country": "Bhutan", "answers": { ... }, "save_response": false }`.
- `POST /api/records/lookup` — `{ "receipt": "..." }`, tra cứu khi có mã bí mật.
- `POST /api/records/delete` — `{ "receipt": "..." }`, xóa khi có mã bí mật.
- `GET /api/health` — kiểm tra máy chủ.

## Kiểm thử

```powershell
.\.venv_q24\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv_q24\Scripts\python.exe -m pytest -q
```

**Giới hạn đồ án:** dữ liệu GSHS 2016 chỉ là dữ liệu khảo sát cắt ngang, không chứng minh quan hệ nguyên nhân-kết quả. Không sử dụng dự đoán Q24 như một công cụ đo bệnh lý tâm thần.
