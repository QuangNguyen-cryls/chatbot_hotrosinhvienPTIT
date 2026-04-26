# 📚 Hướng dẫn cài đặt Chatbot Sổ tay Sinh viên

## 🎯 Yêu cầu hệ thống

- **Python**: 3.8 hoặc cao hơn
- **RAM**: Tối thiểu 4GB (khuyến nghị 8GB)
- **Disk**: 2GB trống
- **OS**: Windows 10/11, macOS, Linux

## 🚀 Cài đặt từng bước

### Bước 1: Chuẩn bị môi trường

```bash
# Tạo virtual environment
python -m venv venv

# Kích hoạt virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### Bước 2: Cài đặt dependencies

```bash
# Cài đặt các thư viện cần thiết
pip install -r requirements.txt

# Kiểm tra cài đặt
python -c "import rasa, flask, PyPDF2, sentence_transformers, faiss; print('✅ Tất cả dependencies đã được cài đặt!')"
```

### Bước 3: Chuẩn bị dữ liệu

```bash
# Đặt file PDF sổ tay sinh viên vào thư mục gốc
# Ví dụ: student_handbook.pdf, handbook.pdf, etc.

# Kiểm tra file PDF
ls *.pdf
```

### Bước 4: Setup tự động (Khuyến nghị)

```bash
# Chạy script setup tự động
python setup_handbook_chatbot.py
```

### Bước 5: Setup thủ công (Nếu cần)

```bash
# Xử lý PDF và tạo knowledge base
python data_processor.py

# Train Rasa model
cd RasaData
rasa train
cd ..
```

## 🔧 Chạy chatbot

### Cách 1: Chạy tự động (Khuyến nghị)

```bash
# Windows
start_all.bat

# PowerShell
.\start_all.ps1
```

### Cách 2: Chạy thủ công

**Terminal 1 - Action Server:**
```bash
cd RasaData
rasa run actions
```

**Terminal 2 - Rasa Server:**
```bash
cd RasaData
rasa run --enable-api --cors "*" --port 5002
```

**Terminal 3 - Flask App:**
```bash
python main.py
```

## 🌐 Truy cập ứng dụng

- **Flask Web Interface**: http://localhost:8080
- **React Frontend**: http://localhost:3000 (tùy chọn)
- **Rasa API**: http://localhost:5002
- **Action Server**: http://localhost:5055

## 🐛 Troubleshooting

### Lỗi thường gặp:

#### 1. **Import errors**
```bash
# Lỗi: Import "PyPDF2" could not be resolved
# Giải pháp: Cài đặt lại dependencies
pip install -r requirements.txt --force-reinstall
```

#### 2. **Port đã được sử dụng**
```bash
# Kiểm tra port đang sử dụng
netstat -ano | findstr :8080
netstat -ano | findstr :5002
netstat -ano | findstr :5055

# Tắt process đang sử dụng port
taskkill /PID <PID> /F
```

#### 3. **Knowledge base không được tạo**
```bash
# Kiểm tra file PDF
ls *.pdf

# Chạy lại data processor
python data_processor.py

# Kiểm tra knowledge base
ls knowledge_base/
```

#### 4. **Rasa model chưa được train**
```bash
cd RasaData
rasa train --force
cd ..
```

#### 5. **Memory errors**
```bash
# Giảm chunk size trong data_processor.py
# Thay đổi chunk_size từ 500 xuống 300
```

## 📋 Kiểm tra hoạt động

### 1. Kiểm tra knowledge base
```bash
ls knowledge_base/
# Kết quả mong đợi:
# - chunks.json
# - embeddings.npy
# - faiss_index.idx
```

### 2. Kiểm tra Rasa model
```bash
cd RasaData
rasa test
cd ..
```

### 3. Test chatbot
```bash
# Mở http://localhost:8080
# Thử các câu hỏi:
# - "Đăng ký học phần như thế nào?"
# - "Lịch học như thế nào?"
# - "Thông tin về thi cử"
```

## 🎉 Hoàn thành!

Sau khi hoàn thành tất cả các bước, chatbot sẽ:
- ✅ Trả lời câu hỏi từ sổ tay sinh viên
- ✅ Tìm kiếm thông tin semantic
- ✅ Gợi ý chủ đề liên quan
- ✅ Giao diện web đẹp và dễ sử dụng

## 📞 Hỗ trợ

Nếu gặp vấn đề, vui lòng:
1. Kiểm tra logs trong terminal
2. Đảm bảo tất cả dependencies đã được cài đặt
3. Kiểm tra file PDF có đúng định dạng
4. Restart tất cả services 