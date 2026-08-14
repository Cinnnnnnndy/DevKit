[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
  & bun run package:all
  if ($LASTEXITCODE -ne 0) { throw "package:all failed with exit code $LASTEXITCODE" }
} finally {
  Pop-Location
}
