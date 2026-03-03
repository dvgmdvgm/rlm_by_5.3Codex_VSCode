# Run: powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\rlm\check_cloud_payload_mode.ps1 -ProjectRoot "D:\art_network_antigravity"
[CmdletBinding()]
param(
    [string]$ProjectRoot = "",
    [switch]$FailOnWarnings
)

$ErrorActionPreference = "Stop"

function Resolve-TargetProjectRoot {
    param([string]$ProjectRoot)
    if ($ProjectRoot) {
        return (Resolve-Path $ProjectRoot).Path
    }
    return (Resolve-Path (Join-Path (Split-Path -Parent $PSCommandPath) "..\..")).Path
}

function Last-MarkerLine {
    param(
        [string[]]$Lines,
        [string]$Marker
    )
    for ($i = $Lines.Count - 1; $i -ge 0; $i--) {
        if ($Lines[$i] -eq $Marker) {
            return $i
        }
    }
    return -1
}

$root = Resolve-TargetProjectRoot -ProjectRoot $ProjectRoot
$logsDir = Join-Path $root "memory\logs"
$auditPath = Join-Path $logsDir "cloud_payload_audit.md"
$currentPath = Join-Path $logsDir "cloud_payload_current.md"

Write-Host "[check-cloud-payload] project_root=$root"

if (-not (Test-Path $auditPath)) {
    throw "Missing file: $auditPath"
}
if (-not (Test-Path $currentPath)) {
    throw "Missing file: $currentPath"
}

$auditLines = Get-Content $auditPath -Encoding UTF8
$currentLines = Get-Content $currentPath -Encoding UTF8

$auditLastPreview = Last-MarkerLine -Lines $auditLines -Marker "payload_preview:"
$auditLastFull = Last-MarkerLine -Lines $auditLines -Marker "payload_full:"
$currentLastPreview = Last-MarkerLine -Lines $currentLines -Marker "payload_preview:"
$currentLastFull = Last-MarkerLine -Lines $currentLines -Marker "payload_full:"

$auditHasPreview = $auditLastPreview -ge 0
$auditHasFull = $auditLastFull -ge 0
$currentHasFull = $currentLastFull -ge 0
$currentHasPreview = $currentLastPreview -ge 0

$okAuditCompact = $auditHasPreview -and -not $auditHasFull
$okCurrentFull = $currentHasFull -and -not $currentHasPreview
$okLatest = ($auditLastPreview -ge 0) -and ($currentLastFull -ge 0)

Write-Host "[check-cloud-payload] audit_has_preview=$auditHasPreview"
Write-Host "[check-cloud-payload] audit_has_full=$auditHasFull"
Write-Host "[check-cloud-payload] current_has_full=$currentHasFull"
Write-Host "[check-cloud-payload] current_has_preview=$currentHasPreview"
Write-Host "[check-cloud-payload] audit_last_preview_line=$auditLastPreview"
Write-Host "[check-cloud-payload] current_last_full_line=$currentLastFull"

if ($okAuditCompact -and $okCurrentFull -and $okLatest) {
    Write-Host "[check-cloud-payload] RESULT=OK" -ForegroundColor Green
    exit 0
}

Write-Host "[check-cloud-payload] RESULT=FAIL" -ForegroundColor Red
Write-Host "Expected: audit uses payload_preview only; current uses payload_full only."

if ($FailOnWarnings) {
    exit 2
}

exit 1
