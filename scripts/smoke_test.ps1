Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$apiPort = $env:API_PORT
if (-not $apiPort) { $apiPort = "8000" }

$healthUrl = "http://localhost:$apiPort/health"
Write-Host "Calling $healthUrl"

try {
    $resp = Invoke-RestMethod -Uri $healthUrl -Method GET -TimeoutSec 10
    $resp | ConvertTo-Json -Depth 10
}
catch {
    Write-Host "Smoke test failed:" -ForegroundColor Red
    Write-Host $_
    exit 1
}
