$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) {
  Write-Host 'Python was not found on PATH.' -ForegroundColor Red
  exit 1
}

$Port = if ($env:ISLAND_DASHBOARD_PORT) { $env:ISLAND_DASHBOARD_PORT } else { '8000' }
Write-Host "Starting ISLAND Scanner Dashboard on http://127.0.0.1:$Port/" -ForegroundColor Cyan

Start-Process -FilePath $Python.Source -ArgumentList 'scanner_backend.py' -WorkingDirectory $Root -WindowStyle Hidden
Start-Sleep -Seconds 2
Start-Process "http://127.0.0.1:$Port/"
