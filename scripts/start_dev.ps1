$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$venvActivate = Join-Path $root ".venv\Scripts\Activate.ps1"

Write-Host "Starting TITAN dev stack..." -ForegroundColor Cyan
Write-Host "Root: $root" -ForegroundColor DarkGray

if (-not (Test-Path $venvActivate)) {
  throw "Virtualenv not found at $venvActivate. Create it first (.venv)."
}

$apiCmd = (
  '& "{0}"; ' +
  'python -m pip -q show uvicorn | Out-Null; ' +
  'if ($LASTEXITCODE -ne 0) {{ python -m pip install -r "{1}\requirements.txt" }}; ' +
  'python -m uvicorn api.main:app --host 127.0.0.1 --port 8000'
) -f $venvActivate, $root

$webDir = Join-Path $root "web"
$webPkg = Join-Path $webDir "package.json"
if (-not (Test-Path $webPkg)) {
  throw "Next.js app not found at $webDir. Expected package.json." 
}

$webCmd = "npm run dev"

Write-Host "Launching API (FastAPI) on http://127.0.0.1:8000 ..." -ForegroundColor Green
Start-Process powershell -WorkingDirectory $root -ArgumentList @(
  "-NoExit",
  "-Command",
  $apiCmd
)

Write-Host "Launching Web (Next.js) on http://localhost:3000 ..." -ForegroundColor Green
Start-Process powershell -WorkingDirectory $webDir -ArgumentList @(
  "-NoExit",
  "-Command",
  $webCmd
)

Write-Host "Done. Open:" -ForegroundColor Cyan
Write-Host "- http://localhost:3000/chat" -ForegroundColor White
Write-Host "- http://localhost:3000/settings" -ForegroundColor White
Write-Host "- http://127.0.0.1:8000/config" -ForegroundColor White
