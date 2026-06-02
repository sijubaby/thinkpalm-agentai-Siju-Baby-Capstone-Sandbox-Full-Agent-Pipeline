# Run UI without activating venv (avoids ExecutionPolicy issues)
Set-Location $PSScriptRoot\..

Write-Host "Maritime QA Agent -> http://127.0.0.1:8770"
& ".\.venv\Scripts\qa-agent.exe" ui
