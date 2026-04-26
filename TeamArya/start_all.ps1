Write-Host "Starting Team Arya Chatbot..." -ForegroundColor Green
Write-Host ""

Write-Host "[1/4] Starting Rasa Action Server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd RasaData; rasa run actions" -WindowStyle Normal

Write-Host "[2/4] Waiting 5 seconds for Action Server to start..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

Write-Host "[3/4] Starting Rasa Server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd RasaData; rasa run --enable-api --cors '*' --port 5002" -WindowStyle Normal

Write-Host "[4/4] Waiting 5 seconds for Rasa Server to start..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

Write-Host "[5/5] Starting Flask Web App..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python main.py" -WindowStyle Normal

Write-Host ""
Write-Host "All services started!" -ForegroundColor Green
Write-Host "- Web Interface: http://localhost:8080" -ForegroundColor White
Write-Host "- Rasa API: http://localhost:5002" -ForegroundColor White
Write-Host "- Action Server: http://localhost:5055" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 