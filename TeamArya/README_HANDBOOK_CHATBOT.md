 🤖 Handbook Chatbot - Chatbot Sổ tay Sinh viên PTIT

## 📋 Mô tả

Chatbot sử dụng AI để trả lời các câu hỏi về sổ tay sinh viên PTIT dựa trên file `handbook_summary.txt`. Hệ thống sử dụng:

- **Sentence Transformers**: Model đa ngôn ngữ để tạo embeddings
- **FAISS**: Thư viện tìm kiếm vector hiệu suất cao
- **Rasa**: Framework chatbot (tùy chọn)

## 🚀 Cài đặt nhanh

### 1. Cài đặt dependencies

```bash
pip install -r requirements_chatbot.txt
```

### 2. Chạy setup tự động

```bash
python setup_handbook_chatbot.py
```

### 3. Chạy chatbot

```bash
python chatbot_with_model.py
```

## 📁 Cấu trúc file

```
TeamArya/
├── chatbot_with_model.py          # Chatbot chính
├── handbook_action_server.py      # Action server cho Rasa
├── setup_handbook_chatbot.py      # Script setup
├── requirements_chatbot.txt       # Dependencies
├── handbook_summary.txt           # Dữ liệu sổ tay
└── knowledge_base/                # Index và metadata (tự tạo)
    ├── handbook_index.idx
    └── handbook_metadata.json
```

## 🔧 Cách sử dụng

### Chạy chatbot độc lập

```bash
python chatbot_with_model.py
```

Chatbot sẽ:
1. Tải model Sentence Transformers
2. Tạo hoặc tải index từ file handbook
3. Sẵn sàng trả lời câu hỏi

### Tích hợp với Rasa

1. **Chạy action server:**
```bash
cd RasaData
python -m rasa run actions --port 5055
```

2. **Chạy Rasa server:**
```bash
cd RasaData
python -m rasa run --enable-api --cors '*' --port 5002
```

3. **Chạy web interface:**
```bash
python main.py
```

## 💡 Ví dụ sử dụng

### Câu hỏi mẫu:

- "Học viện PTIT có lịch sử như thế nào?"
- "Các ngành đào tạo tại PTIT là gì?"
- "Thông tin về ký túc xá?"
- "Quy định về học phí?"
- "Các khoa đào tạo tại cơ sở TP.HCM?"

### Cách chatbot hoạt động:

1. **Phân tích câu hỏi**: Chuyển câu hỏi thành vector embedding
2. **Tìm kiếm**: So sánh với các chunk trong handbook
3. **Trả lời**: Trả về thông tin liên quan nhất với độ tin cậy

## ⚙️ Cấu hình

### Thay đổi model

Trong `chatbot_with_model.py`, thay đổi:

```python
chatbot = HandbookChatbot(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
```

Các model khác:
- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (nhỏ, nhanh)
- `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` (lớn, chính xác hơn)

### Điều chỉnh ngưỡng tương đồng

```python
# Trong hàm answer_question()
if score > 0.3:  # Tăng để chặt chẽ hơn, giảm để linh hoạt hơn
```

## 🔍 Tính năng

### 1. Tìm kiếm thông minh
- Sử dụng semantic search
- Tìm kiếm theo ngữ nghĩa, không chỉ từ khóa

### 2. Phân tích cấu trúc
- Tự động nhận diện tiêu đề
- Chia nội dung thành chunks có ý nghĩa

### 3. Độ tin cậy
- Hiển thị điểm số tương đồng
- Lọc kết quả có độ tin cậy thấp

### 4. Lưu trữ index
- Tự động lưu/tải index
- Không cần tạo lại mỗi lần chạy

## 🛠️ Troubleshooting

### Lỗi cài đặt dependencies

```bash
# Cài đặt từng package
pip install sentence-transformers
pip install faiss-cpu
pip install torch
```

### Lỗi tải model

```bash
# Xóa cache và tải lại
rm -rf ~/.cache/torch
rm -rf ~/.cache/huggingface
```

### Lỗi memory

```bash
# Sử dụng model nhỏ hơn
model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
```

## 📊 Hiệu suất

- **Thời gian khởi động**: ~30 giây (lần đầu), ~5 giây (các lần sau)
- **Thời gian trả lời**: ~1-3 giây
- **Độ chính xác**: ~85-90% với câu hỏi rõ ràng
- **Memory usage**: ~500MB-1GB

## 🔄 Cập nhật dữ liệu

Khi cập nhật `handbook_summary.txt`:

1. Xóa thư mục `knowledge_base/`
2. Chạy lại chatbot (sẽ tự tạo index mới)

Hoặc:

```python
from chatbot_with_model import HandbookChatbot

chatbot = HandbookChatbot()
chatbot.load_model()
chunks = chatbot.parse_handbook("handbook_summary.txt")
chatbot.create_embeddings(chunks)
chatbot.save_index()
```

## 📞 Hỗ trợ

Nếu gặp vấn đề:
1. Kiểm tra file `handbook_summary.txt` có đúng format
2. Đảm bảo đã cài đặt đầy đủ dependencies
3. Kiểm tra log để xem lỗi chi tiết

## 🎯 Roadmap

- [ ] Thêm tính năng tìm kiếm nâng cao
- [ ] Tích hợp với database
- [ ] Thêm giao diện web đẹp hơn
- [ ] Hỗ trợ đa ngôn ngữ
- [ ] Thêm tính năng học từ phản hồi người dùng 