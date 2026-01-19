Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "Stopping and removing containers + volumes..."
docker compose down -v

Write-Host "Done."
