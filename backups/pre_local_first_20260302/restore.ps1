$ErrorActionPreference = 'Stop'

$backupRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $backupRoot "..\..")

Copy-Item -LiteralPath (Join-Path $backupRoot "src\rlm_mcp\server.py.bak") -Destination (Join-Path $projectRoot "src\rlm_mcp\server.py") -Force
Copy-Item -LiteralPath (Join-Path $backupRoot "README.md") -Destination (Join-Path $projectRoot "README.md") -Force
Copy-Item -LiteralPath (Join-Path $backupRoot ".github\copilot-instructions.md") -Destination (Join-Path $projectRoot ".github\copilot-instructions.md") -Force

Write-Host "Rollback completed from backup: $backupRoot"
Write-Host "Restart MCP server to apply restored behavior."
