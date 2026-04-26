# 📚 Chatbot Sổ tay Sinh viên - Team Arya

## 🎯 Mô tả dự án

Chatbot thông minh hỗ trợ sinh viên tìm kiếm thông tin từ sổ tay sinh viên. Bot sử dụng:
- **Rasa** cho xử lý ngôn ngữ tự nhiên
- **Sentence Transformers** cho tìm kiếm semantic
- **FAISS** cho tìm kiếm vector nhanh
- **Flask** cho web interface
- **React** cho frontend hiện đại

## 🚀 Tính năng chính

- ✅ Tìm kiếm thông tin từ PDF sổ tay sinh viên
- ✅ Trả lời câu hỏi về đăng ký học phần, lịch học, thi cử
- ✅ Hỗ trợ tìm kiếm học bổng, thư viện, ký túc xá
- ✅ Giao diện web đẹp và dễ sử dụng
- ✅ Tìm kiếm semantic thông minh
- ✅ Gợi ý chủ đề liên quan

## 📋 Yêu cầu hệ thống

- Python 3.8+ 
- pip (Python package manager)
- Git (để clone dự án)

## 🚀 Cách chạy dự án

### Bước 0: Chuẩn bị dữ liệu
```bash
# Đặt file PDF sổ tay sinh viên vào thư mục gốc
# Ví dụ: student_handbook.pdf, handbook.pdf, etc.
```

### Bước 1: Setup tự động (Khuyến nghị)
```bash
# Chạy script setup tự động
python setup_handbook_chatbot.py
```

### Bước 2: Setup thủ công

```bash
# Cài đặt Rasa
pip install rasa

# Cài đặt Flask
pip install flask

# Cài đặt requests (cho API calls)
pip install requests

# Cài đặt các dependencies khác
pip install rasa-sdk
```

### Bước 2: Xử lý PDF và tạo knowledge base

```bash
# Xử lý file PDF sổ tay sinh viên
python data_processor.py

# Kiểm tra knowledge base đã được tạo
ls knowledge_base/
```

### Bước 3: Train model Rasa

```bash
# Di chuyển vào thư mục RasaData
cd RasaData

# Train model
rasa train

# Kiểm tra model đã train
rasa test
```

### Bước 4: Chạy các services

#### Cách 1: Chạy tự động (Khuyến nghị)
```bash
# Windows - Sử dụng batch file
start_all.bat

# Windows - Sử dụng PowerShell
.\start_all.ps1
```

#### Cách 2: Chạy thủ công
**Terminal 1 - Rasa Action Server:**
```bash
cd RasaData
rasa run actions
```

**Terminal 2 - Rasa Server:**
```bash
cd RasaData
rasa run --enable-api --cors "*" --port 5002
```

**Terminal 3 - Flask Web App:**
```bash
cd TeamArya
python main.py
```

### Bước 5: Truy cập ứng dụng

- **Web Interface (Flask)**: http://localhost:8080
- **React Frontend**: http://localhost:3000 (chạy riêng)
- **Rasa API**: http://localhost:5002
- **Action Server**: http://localhost:5055

### Bước 6: Chạy React Frontend (Tùy chọn)
```bash
cd ../chatbot-arya
npm start
```

## 📁 Cấu trúc thư mục

```
TeamArya/
├── main.py                 # Flask web app
├── templates/
│   └── index.html         # Chat interface
├── models/                # Trained models
└── RasaData/             # Rasa project
    ├── actions/          # Custom actions
    ├── data/            # Training data
    ├── models/          # Trained models
    └── config files     # Configuration
```

## 🔧 Cấu hình

### API Keys
- **OpenWeatherMap API**: Đã có sẵn trong `actions.py`
- **Rasa API**: Không cần key

### Ports
- **Flask App**: 8080
- **Rasa Server**: 5002  
- **Action Server**: 5055

## 🎯 Tính năng

- ✅ Tìm kiếm thông tin từ PDF sổ tay sinh viên
- ✅ Trả lời câu hỏi về đăng ký học phần, lịch học, thi cử
- ✅ Hỗ trợ tìm kiếm học bổng, thư viện, ký túc xá
- ✅ Giao diện web đẹp và dễ sử dụng
- ✅ Tìm kiếm semantic thông minh
- ✅ Gợi ý chủ đề liên quan

## 🐛 Troubleshooting

### Lỗi thường gặp:

1. **Port đã được sử dụng**
   ```bash
   # Kiểm tra port đang sử dụng
   netstat -ano | findstr :8080
   # Hoặc thay đổi port trong main.py
   ```

2. **Model chưa được train**
   ```bash
   cd RasaData
   rasa train
   ```

3. **Dependencies thiếu**
   ```bash
   pip install -r requirements.txt
   ```

## 📝 Lệnh hữu ích

```bash
# Train model
rasa train

# Test model
rasa test

# Shell để test chatbot
rasa shell

# Xem logs
rasa run --log-level DEBUG

# Interactive training
rasa interactive
```

## 🎉 Chúc mừng!

Sau khi chạy thành công, bạn có thể:
- Chat với bot tại http://localhost:8080
- Hỏi về đăng ký học phần: "Đăng ký học phần như thế nào?"
- Tìm thông tin lịch học: "Lịch học như thế nào?"
- Hỏi về thi cử: "Thông tin về thi cử"
- Tìm hiểu học bổng: "Thông tin học bổng"
- Và nhiều câu hỏi khác về sinh viên!

## 📚 Ví dụ câu hỏi

- "Đăng ký học phần như thế nào?"
- "Lịch học của tôi"
- "Thông tin về thi cử"
- "Điều kiện tốt nghiệp"
- "Cách xin học bổng"
- "Giờ mở cửa thư viện"
- "Thông tin ký túc xá"
- "Quy định sinh viên" 