#!/usr/bin/env pwsh
# demo/run.ps1 - Windows/PowerShell twin of demo/run.sh.
#
# Runs Agentic OS's real credential scanner
# (.agentcortex/tools/scan_credentials.py) against a file an agent is "about to
# commit". The leaked key is generated at runtime, so this script never stores a
# real-looking secret of its own. Nothing is staged or committed; a temp dir is
# used and cleaned up.
#
# Reproduce anytime:  pwsh demo/run.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path $PSScriptRoot -Parent
$scanner  = Join-Path $repoRoot '.agentcortex/tools/scan_credentials.py'

$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $py) { Write-Host 'This demo needs Python 3.9+ (the scanner is Python).'; exit 2 }
if (-not (Test-Path -LiteralPath $scanner)) { Write-Host "Scanner not found at $scanner"; exit 2 }

$work = Join-Path ([System.IO.Path]::GetTempPath()) ([System.IO.Path]::GetRandomFileName())
New-Item -ItemType Directory -Path $work | Out-Null
try {
    # Built at runtime so this repo's own scanner never flags the demo itself.
    $key = 'AKIA' + 'IOSFODNN7EXAMPLE'
    $cfg = Join-Path $work 'config.env'
    Set-Content -LiteralPath $cfg -Encoding ascii -Value @('DB_HOST=prod.internal', "aws_access_key_id = $key")

    Write-Host ''
    Write-Host '  An AI agent wrote this file and reported: "Done - config added."'
    Write-Host '  ----------------------------------------------------------------'
    foreach ($line in Get-Content -LiteralPath $cfg) {
        Write-Host ('    ' + ($line -replace [regex]::Escape($key), 'AKIA****************'))
    }
    Write-Host '  ----------------------------------------------------------------'
    Write-Host ''
    Write-Host '  Without a gate, that commit lands and the key is in git history forever.'
    Write-Host '  Agentic OS runs this before the commit is allowed:'
    Write-Host ''
    Write-Host '    $ scan_credentials.py config.env'
    Write-Host ''

    # Native non-zero exit (a block) must not throw; guard the PS7.3+ behavior.
    $hadNative = Test-Path variable:PSNativeCommandUseErrorActionPreference
    if ($hadNative) { $prevNative = $PSNativeCommandUseErrorActionPreference; $PSNativeCommandUseErrorActionPreference = $false }
    Push-Location $work
    try { & $py.Source $scanner 'config.env' } finally {
        Pop-Location
        if ($hadNative) { $PSNativeCommandUseErrorActionPreference = $prevNative }
    }
    $code = $LASTEXITCODE

    if ($code -eq 0) {
        Write-Host ''
        Write-Host '  [!] Demo problem: the scanner did not flag the key. Please open an issue.'
        exit 1
    }
    Write-Host ''
    Write-Host '  Commit BLOCKED. The agent said "done"; the machine said no - and it'
    Write-Host '  redacted the value instead of echoing your secret back at you.'
    Write-Host ''
    Write-Host '  This is one machine-enforced check of several (CI runs your real tests;'
    Write-Host '  validators check the work trail). Reproduce anytime: pwsh demo/run.ps1'
    Write-Host ''
}
finally {
    Remove-Item -Recurse -Force -LiteralPath $work -ErrorAction SilentlyContinue
}
