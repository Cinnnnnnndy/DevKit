[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
  & bun run verify:packages
  if ($LASTEXITCODE -ne 0) { throw "verify:packages failed with exit code $LASTEXITCODE" }
} finally {
  Pop-Location
}
