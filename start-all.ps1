# Starts the API (port 8000) and the Angular dev server (port 4200) in two windows.
$root = $PSScriptRoot
Start-Process powershell -ArgumentList "-NoExit", "-Command",
  "Set-Location '$root\tracker-api'; .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command",
  "Set-Location '$root\tracker-frontend'; npm start"
Write-Host "API: http://localhost:8000/docs   App: http://localhost:4200"
