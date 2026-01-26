Param(
  [string]$ApiBase = "http://127.0.0.1:8000",
  [string]$Start = "2025-12-01",
  [string]$End = "2026-01-23",
  [int]$WaitSeconds = 45
)

$ErrorActionPreference = "Stop"

function Fail($msg) {
  Write-Host "FAIL: $msg" -ForegroundColor Red
  exit 1
}

function Pass($msg) {
  Write-Host "PASS: $msg" -ForegroundColor Green
}

Write-Host "Starting dev stack + running Operations smoke test..." -ForegroundColor Cyan

$root = Split-Path -Parent $PSScriptRoot
$startScript = Join-Path $root "scripts\start_dev.ps1"
$smokeScript = Join-Path $root "scripts\smoke_ops.ps1"

if (-not (Test-Path $startScript)) { Fail("Missing: $startScript") }
if (-not (Test-Path $smokeScript)) { Fail("Missing: $smokeScript") }

# 1) Start dev stack (this opens 2 PowerShell windows: API + Web)
& $startScript

# 2) Wait for API to be ready
$deadline = (Get-Date).AddSeconds($WaitSeconds)
$healthUrl = "$ApiBase/health"
Write-Host "Waiting for API health: $healthUrl (timeout ${WaitSeconds}s)" -ForegroundColor DarkGray

while ((Get-Date) -lt $deadline) {
  try {
    $h = Invoke-RestMethod -Method Get -Uri $healthUrl -TimeoutSec 5
    if ($h -and ($h.ok -eq $true)) {
      Pass("API is up")
      break
    }
  } catch {
    Start-Sleep -Seconds 2
  }
}

try {
  $h2 = Invoke-RestMethod -Method Get -Uri $healthUrl -TimeoutSec 5
  if (-not ($h2 -and ($h2.ok -eq $true))) { Fail("API did not become ready in time") }
} catch {
  Fail("API did not become ready in time: $($_.Exception.Message)")
}

# 3) Run the smoke test
Write-Host "Running smoke test..." -ForegroundColor Cyan
& powershell -ExecutionPolicy Bypass -File $smokeScript -ApiBase $ApiBase -Start $Start -End $End
if ($LASTEXITCODE -ne 0) { Fail("Smoke test failed") }
