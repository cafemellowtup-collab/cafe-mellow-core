Param(
  [string]$ApiBase = "http://127.0.0.1:8000",
  [string]$Start = "2025-12-01",
  [string]$End = "2026-01-23",
  [int]$TimeoutSec = 120
)

$ErrorActionPreference = "Stop"

function Fail($msg) {
  Write-Host "FAIL: $msg" -ForegroundColor Red
  exit 1
}

function Pass($msg) {
  Write-Host "PASS: $msg" -ForegroundColor Green
}

function GetJson($path) {
  $url = "$ApiBase$path"
  try {
    return Invoke-RestMethod -Method Get -Uri $url -TimeoutSec $TimeoutSec
  } catch {
    Fail("Request failed: $url | $($_.Exception.Message)")
  }
}

function Assert($cond, $msg) {
  if (-not $cond) { Fail($msg) }
}

Write-Host "Operations Smoke Test" -ForegroundColor Cyan
Write-Host "API: $ApiBase" -ForegroundColor DarkGray
Write-Host "Range: $Start -> $End" -ForegroundColor DarkGray

# 1) Health
$h = GetJson "/health"
Assert ($h.ok -eq $true) "/health ok != true"
Assert ($h.bq_connected -eq $true) "/health bq_connected != true (BigQuery not connected)"
Assert ([string]$h.project_id) "/health project_id missing"
Assert ([string]$h.dataset_id) "/health dataset_id missing"
Pass "/health"

# 2) Expenses filters
$ef = GetJson "/ops/expenses/filters"
Assert ($ef.ok -eq $true) "/ops/expenses/filters ok != true"
Assert ($null -ne $ef.ledgers) "expenses filters missing ledgers"
Assert ($null -ne $ef.main_categories) "expenses filters missing main_categories"
Assert ($null -ne $ef.categories) "expenses filters missing categories"
Pass "/ops/expenses/filters"

# 3) Expenses list
$exp = GetJson "/ops/expenses?start=$Start&end=$End&limit=5"
Assert ($exp.ok -eq $true) "/ops/expenses ok != true"
Assert ($null -ne $exp.summary) "expenses response missing summary"
Assert ($null -ne $exp.summary.total_amount) "expenses summary missing total_amount"
Assert ($null -ne $exp.summary.row_count) "expenses summary missing row_count"
Assert ($null -ne $exp.items) "expenses response missing items"
Assert ($exp.items.Count -ge 1) "expenses items empty (range may have no data)"
Pass "/ops/expenses"

# 4) Sales filters
$sf = GetJson "/ops/sales/filters"
Assert ($sf.ok -eq $true) "/ops/sales/filters ok != true"
Assert ([string]$sf.table) "sales filters missing table"
Assert ($null -ne $sf.order_types) "sales filters missing order_types"
Assert ($null -ne $sf.delivery_partners) "sales filters missing delivery_partners"
Pass "/ops/sales/filters"

# 5) Sales channels
$sc = GetJson "/ops/sales/channels?start=$Start&end=$End"
Assert ($sc.ok -eq $true) "/ops/sales/channels ok != true"
Assert ($null -ne $sc.order_types) "sales channels missing order_types"
Assert ($null -ne $sc.delivery_partners) "sales channels missing delivery_partners"
Pass "/ops/sales/channels"

# 6) Top items
$ti = GetJson "/ops/sales/top-items?start=$Start&end=$End&limit=5"
Assert ($ti.ok -eq $true) "/ops/sales/top-items ok != true"
Assert ($null -ne $ti.items) "top-items missing items"
Assert ($ti.items.Count -ge 1) "top-items empty (range may have no data)"
Pass "/ops/sales/top-items"

# 7) Daily ops brief
$b = GetJson "/ops/brief/today"
Assert ($b.ok -eq $true) "/ops/brief/today ok != true"
Assert ([string]$b.brief_date) "ops brief missing brief_date"
Assert ($null -ne $b.kpis) "ops brief missing kpis"
Assert ($null -ne $b.kpis.revenue) "ops brief missing kpis.revenue"
Assert ($null -ne $b.kpis.expenses) "ops brief missing kpis.expenses"
Assert ($null -ne $b.kpis.net) "ops brief missing kpis.net"
Pass "/ops/brief/today"

# 8) Recent briefs
$rb = GetJson "/ops/brief/recent?days=7"
Assert ($rb.ok -eq $true) "/ops/brief/recent ok != true"
Assert ($null -ne $rb.items) "ops brief recent missing items"
Pass "/ops/brief/recent"

# 9) Task generation (dry run)
$tg = GetJson "/tasks/generate?dry_run=true&brief_date=$End"
Assert ($tg.ok -eq $true) "/tasks/generate ok != true"
Assert ($null -ne $tg.count) "/tasks/generate missing count"
Assert ($null -ne $tg.tasks) "/tasks/generate missing tasks"
Pass "/tasks/generate"

# 10) Pending tasks
$tp = GetJson "/tasks/pending?limit=5"
Assert ($tp.ok -eq $true) "/tasks/pending ok != true"
Assert ($null -ne $tp.items) "/tasks/pending missing items"
Pass "/tasks/pending"

Write-Host "ALL CHECKS PASSED" -ForegroundColor Green
