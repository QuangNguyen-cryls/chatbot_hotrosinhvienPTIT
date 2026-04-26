Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   CHATBOT TEAM ARYA - STARTUP SCRIPT" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/4] Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "[2/4] Training Rasa model..." -ForegroundColor Yellow
Set-Location RasaData
rasa train
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to train model" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "[3/4] Starting Rasa Action Server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "rasa run actions" -WindowStyle Normal

Write-Host ""
Write-Host "[4/4] Starting Rasa Server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "rasa run --enable-api --cors `"*`" --port 5002" -WindowStyle Normal

Write-Host ""
Write-Host "[5/5] Starting Flask Web App..." -ForegroundColor Yellow
Set-Location ..
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python main.py" -WindowStyle Normal

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   ALL SERVICES STARTED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Web Interface: http://localhost:8080" -ForegroundColor Cyan
Write-Host "🤖 Rasa API: http://localhost:5002" -ForegroundColor Cyan
Write-Host "⚡ Action Server: http://localhost:5055" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to exit" 