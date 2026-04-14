param(
    [string]$Target = '.'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Normalize-PathString {
    param([string]$Path)
    if ($Path -and $Path.StartsWith('\\?\')) { return $Path.Substring(4) }
    return $Path
}

function Resolve-BashLauncher {
    $candidates = @()
    $bashCmd = Get-Command bash -ErrorAction SilentlyContinue
    if ($bashCmd) { $candidates += $bashCmd.Source }

    $candidates += @(
        'C:\Program Files\Git\bin\bash.exe',
        'C:\Program Files\Git\usr\bin\bash.exe',
        'C:\Program Files (x86)\Git\bin\bash.exe'
    )

    foreach ($candidate in $candidates) {
        if (-not (Test-Path -Path $candidate -PathType Leaf)) {
            continue
        }
        & $candidate --version *> $null
        if ($LASTEXITCODE -eq 0) {
            return $candidate
        }
    }

    return $null
}

$scriptDir = $PSScriptRoot
if (-not $scriptDir) { $scriptDir = Split-Path -Parent $PSCommandPath }
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }
$scriptDir = Normalize-PathString $scriptDir
$bashScript = [System.IO.Path]::Combine($scriptDir, 'deploy.sh')

if (-not (Test-Path -Path $bashScript -PathType Leaf)) {
    Write-Error "cannot find canonical deploy script: $bashScript"
    exit 1
}

$bashLauncher = Resolve-BashLauncher
if (-not $bashLauncher) {
    Write-Host ''
    Write-Host '[ERROR] Bash is required for deployment.' -ForegroundColor Red
    Write-Host ''
    Write-Host 'Agentic OS deploy uses a bash script under the hood.'
    Write-Host 'Install one of the following to get bash on Windows:'
    Write-Host ''
    Write-Host '  1. Git for Windows (recommended): https://gitforwindows.org/'
    Write-Host '     Includes Git Bash which provides bash automatically.'
    Write-Host ''
    Write-Host '  2. WSL (Windows Subsystem for Linux): wsl --install'
    Write-Host ''
    Write-Host 'After installing, rerun this script.'
    exit 1
}

& $bashLauncher $bashScript "$Target"
exit $LASTEXITCODE
