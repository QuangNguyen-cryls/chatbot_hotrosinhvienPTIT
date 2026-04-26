# Script chạy Handbook Chatbot
# PowerShell script để khởi động chatbot sổ tay sinh viên

Write-Host "🤖 Handbook Chatbot - PTIT Student Handbook" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Kiểm tra Python
Write-Host "🔍 Kiểm tra Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python không được tìm thấy. Vui lòng cài đặt Python trước." -ForegroundColor Red
    exit 1
}

# Kiểm tra file handbook
Write-Host "📄 Kiểm tra file handbook..." -ForegroundColor Yellow
if (-not (Test-Path "handbook_summary.txt")) {
    Write-Host "❌ Không tìm thấy file handbook_summary.txt" -ForegroundColor Red
    Write-Host "Vui lòng đảm bảo file này tồn tại trong thư mục hiện tại." -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ File handbook_summary.txt đã tìm thấy" -ForegroundColor Green

# Kiểm tra và cài đặt dependencies
Write-Host "📦 Kiểm tra dependencies..." -ForegroundColor Yellow
try {
    python -c "import sentence_transformers, faiss, torch" 2>$null
    Write-Host "✅ Dependencies đã được cài đặt" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Một số dependencies chưa được cài đặt" -ForegroundColor Yellow
    Write-Host "Đang cài đặt dependencies..." -ForegroundColor Yellow
    
    try {
        pip install -r requirements_chatbot.txt
        Write-Host "✅ Cài đặt dependencies thành công" -ForegroundColor Green
    } catch {
        Write-Host "❌ Lỗi khi cài đặt dependencies" -ForegroundColor Red
        Write-Host "Vui lòng chạy: pip install -r requirements_chatbot.txt" -ForegroundColor Yellow
        exit 1
    }
}

# Menu chọn chế độ chạy
Write-Host "`n🎯 Chọn chế độ chạy:" -ForegroundColor Cyan
Write-Host "1. Chatbot độc lập (Command line)" -ForegroundColor White
Write-Host "2. Action Server cho Rasa" -ForegroundColor White
Write-Host "3. Setup và test chatbot" -ForegroundColor White
Write-Host "4. Thoát" -ForegroundColor White

$choice = Read-Host "`nNhập lựa chọn (1-4)"

switch ($choice) {
    "1" {
        Write-Host "`n🚀 Khởi động chatbot độc lập..." -ForegroundColor Green
        Write-Host "Gõ 'quit' để thoát" -ForegroundColor Yellow
        Write-Host "=" * 50 -ForegroundColor Gray
        
        try {
            python chatbot_with_model.py
        } catch {
            Write-Host "❌ Lỗi khi chạy chatbot: $_" -ForegroundColor Red
        }
    }
    
    "2" {
        Write-Host "`n🚀 Khởi động Action Server cho Rasa..." -ForegroundColor Green
        Write-Host "Server sẽ chạy trên port 5055" -ForegroundColor Yellow
        Write-Host "Nhấn Ctrl+C để dừng" -ForegroundColor Yellow
        
        try {
            Set-Location "RasaData"
            python -m rasa run actions --port 5055
        } catch {
            Write-Host "❌ Lỗi khi chạy action server: $_" -ForegroundColor Red
        }
    }
    
    "3" {
        Write-Host "`n🔧 Chạy setup và test..." -ForegroundColor Green
        
        try {
            python setup_handbook_chatbot.py
        } catch {
            Write-Host "❌ Lỗi khi setup: $_" -ForegroundColor Red
        }
    }
    
    "4" {
        Write-Host "👋 Tạm biệt!" -ForegroundColor Green
        exit 0
    }
    
    default {
        Write-Host "❌ Lựa chọn không hợp lệ!" -ForegroundColor Red
    }
}

Write-Host "`n✅ Hoàn thành!" -ForegroundColor Green 