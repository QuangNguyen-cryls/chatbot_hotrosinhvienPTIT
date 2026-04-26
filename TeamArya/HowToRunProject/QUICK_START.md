# ⚡ QUICK START - Chatbot Team Arya

## 🚀 Cách chạy nhanh nhất:

### Phương pháp 1: Dùng script tự động (Khuyến nghị)
```bash
# Windows Batch
run_chatbot.bat

# Hoặc PowerShell
.\run_chatbot.ps1
```

### Phương pháp 2: Chạy thủ công

**Bước 1: Cài đặt**
```bash
pip install -r requirements.txt
```

**Bước 2: Train model**
```bash
cd RasaData
rasa train
```

**Bước 3: Chạy 3 terminal song song**

Terminal 1:
```bash
cd RasaData
rasa run actions
```

Terminal 2:
```bash
cd RasaData  
rasa run --enable-api --cors "*" --port 5002
```

Terminal 3:
```bash
cd TeamArya
python main.py
```

## 🌐 Truy cập:
- **Web Chat**: http://localhost:8080
- **Rasa API**: http://localhost:5002

## 💬 Test ngay:
- "Xin chào"
- "Thời tiết Hà Nội hôm nay thế nào?"
- "Cảm ơn"

## ⚠️ Lưu ý:
- Đảm bảo Python 3.8+ đã cài đặt
- Cần internet để lấy dữ liệu thời tiết
- Đóng tất cả terminal khi muốn dừng 