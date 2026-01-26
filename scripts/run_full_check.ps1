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

$root = Split-Path -Parent $PSScriptRoot
$opsCheck = Join-Path $root "scripts\run_ops_check.ps1"
$webDir = Join-Path $root "web"
$webPkg = Join-Path $webDir "package.json"

if (-not (Test-Path $opsCheck)) { Fail("Missing: $opsCheck") }
if (-not (Test-Path $webPkg)) { Fail("Missing: $webPkg") }

Write-Host "1/2 Running API + Operations checks..." -ForegroundColor Cyan
& powershell -ExecutionPolicy Bypass -File $opsCheck -ApiBase $ApiBase -Start $Start -End $End -WaitSeconds $WaitSeconds
if ($LASTEXITCODE -ne 0) { Fail("Operations checks failed") }
Pass "Operations API smoke checks"

Write-Host "2/2 Running frontend checks (lint + build)..." -ForegroundColor Cyan

Push-Location $webDir
try {
  # These do not start a server; they only validate code quality and build correctness.
  & npm run lint
  if ($LASTEXITCODE -ne 0) { Fail("Frontend lint failed") }

  & npm run build
  if ($LASTEXITCODE -ne 0) { Fail("Frontend build failed") }

  Pass "Frontend lint + build"
} catch {
  Fail("Frontend checks failed: $($_.Exception.Message)")
} finally {
  Pop-Location
}

Write-Host "ALL CHECKS PASSED (OPS + FRONTEND)" -ForegroundColor Green
