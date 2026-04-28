# Recover Hermes Agent in ubuntu24 — Windows entrypoint.
# Usage:
#   .\infra\hermes\recover.ps1
#
# Prerequisites: ubuntu24 container running, Hermes binary installed inside.

$ErrorActionPreference = "Stop"

Write-Host "Recovering Hermes config in ubuntu24..." -ForegroundColor Cyan

# Ensure container is running
$status = docker inspect -f "{{.State.Status}}" ubuntu24 2>$null
if ($status -ne "running") {
    Write-Error "Container 'ubuntu24' is not running (status=$status). Start it first."
}

# Verify hermes binary
$hermesBinary = docker exec ubuntu24 which hermes 2>$null
if (-not $hermesBinary) {
    Write-Error "Hermes is not installed in the container. Install it first, then re-run."
}

# Convert script to LF and execute
docker exec ubuntu24 bash -lc "sed -i 's/\r`$//' /workspace/infra/hermes/recover.sh; bash /workspace/infra/hermes/recover.sh"
