param(
    [string]$TargetProjectPath = ".",

    [string]$RepoUrl = "https://github.com/dvgmdvgm/rlm_by_5.3Codex_VSCode.git",
    [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"

function Test-CommandAvailable($name) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        throw "Required command '$name' was not found in PATH."
    }
}

Test-CommandAvailable git

function Invoke-GitChecked {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Args
    )

    & git @Args
    if ($LASTEXITCODE -ne 0) {
        throw "git command failed: git $($Args -join ' ')"
    }
}

if ([string]::IsNullOrWhiteSpace($TargetProjectPath)) {
    $TargetProjectPath = "."
}

if (-not (Test-Path -LiteralPath $TargetProjectPath)) {
    New-Item -ItemType Directory -Path $TargetProjectPath -Force | Out-Null
}
$target = (Resolve-Path -LiteralPath $TargetProjectPath).Path

$tempRoot = Join-Path $env:TEMP ("rlm_bootstrap_" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tempRoot | Out-Null

try {
    Invoke-GitChecked -Args @("clone", "--depth", "1", "--filter=blob:none", "--sparse", "--branch", $Branch, $RepoUrl, $tempRoot)

    Push-Location $tempRoot
    try {
        $sparsePaths = @(
            "/.github",
            "/.vscode/mcp.json",
            "/scripts/generate_rlm_memory_from_code.py"
        )
        Invoke-GitChecked -Args (@("sparse-checkout", "set", "--no-cone") + $sparsePaths)
    }
    finally {
        Pop-Location
    }

    $copyPaths = @(
        ".github",
        ".vscode/mcp.json",
        "scripts/generate_rlm_memory_from_code.py"
    )

    foreach ($rel in $copyPaths) {
        $src = Join-Path $tempRoot $rel
        if (-not (Test-Path -LiteralPath $src)) {
            continue
        }
        $dst = Join-Path $target $rel

        if ((Get-Item -LiteralPath $src).PSIsContainer) {
            New-Item -ItemType Directory -Path $dst -Force | Out-Null
            Copy-Item -LiteralPath (Join-Path $src "*") -Destination $dst -Recurse -Force
        }
        else {
            $dstDir = Split-Path -Parent $dst
            if ($dstDir) {
                New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
            }
            Copy-Item -LiteralPath $src -Destination $dst -Force
        }
    }

    Write-Output "Bootstrap assets installed to: $target"
    Write-Output "Included: .github (all Copilot workflows), .vscode/mcp.json, scripts/generate_rlm_memory_from_code.py"
    Write-Output "Excluded from install: src/, memory/, backups/, examples/, docs/, prompts/, README.md, .venv/"
}
finally {
    if (Test-Path -LiteralPath $tempRoot) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force
    }
}
