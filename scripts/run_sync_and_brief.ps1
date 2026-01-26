Param(
  [string]$ApiBase = "http://127.0.0.1:8000",
  [string]$BriefDate = "",
  [int]$TimeoutSec = 180
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

$syncRaw = Join-Path $root "01_Data_Sync\sync_sales_raw.py"
$parser = Join-Path $root "01_Data_Sync\titan_sales_parser.py"

if (-not (Test-Path $syncRaw)) { Fail("Missing: $syncRaw") }
if (-not (Test-Path $parser)) { Fail("Missing: $parser") }

Write-Host "Running TITAN: Sync -> Parse -> Generate Ops Brief" -ForegroundColor Cyan

# 1) Data sync
Write-Host "1/3 Syncing sales raw..." -ForegroundColor Cyan
& python $syncRaw
if ($LASTEXITCODE -ne 0) { Fail("sync_sales_raw.py failed") }
Pass "sync_sales_raw.py"

# 2) Parse
Write-Host "2/3 Parsing sales..." -ForegroundColor Cyan
& python $parser
if ($LASTEXITCODE -ne 0) { Fail("titan_sales_parser.py failed") }
Pass "titan_sales_parser.py"

# 3) Generate brief
if (-not $BriefDate) {
  $BriefDate = (Get-Date).AddDays(-1).ToString("yyyy-MM-dd")
}

$genUrl = "$ApiBase/ops/brief/generate?brief_date=$BriefDate"
Write-Host "3/3 Generating Ops Brief: $genUrl" -ForegroundColor Cyan

try {
  $resp = Invoke-RestMethod -Method Post -Uri $genUrl -TimeoutSec $TimeoutSec
} catch {
  Fail("Brief generation failed: $($_.Exception.Message)")
}

if (-not $resp -or ($resp.ok -ne $true)) {
  Fail("Brief generation returned not ok")
}

Pass "Ops brief generated"
Write-Host "Brief date: $($resp.brief_date)" -ForegroundColor DarkGray
Write-Host "Tip: open $ApiBase/ops/brief/today" -ForegroundColor DarkGray
