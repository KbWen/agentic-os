param(
    [string]$Target = '.',
    [string]$Source = '',
    [switch]$DryRun,
    [switch]$NoPython
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
$canonical = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine($scriptDir, '.agentcortex', 'bin', 'deploy.sh'))

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

# Build argument list
$bashArgs = @()
if ($DryRun) { $bashArgs += '--dry-run' }
if ($Source) { $bashArgs += '--source'; $bashArgs += $Source }
$bashArgs += "$Target"

if (Test-Path -Path $canonical -PathType Leaf) {
    # Normal path: canonical deploy exists locally
    & $bashLauncher $canonical @bashArgs
} else {
    # Bootstrap path: delegate to wrapper which handles fetch
    $wrapperSh = [System.IO.Path]::Combine($scriptDir, 'deploy_brain.sh')
    if (-not (Test-Path -Path $wrapperSh -PathType Leaf)) {
        Write-Error "Neither canonical deploy nor deploy_brain.sh wrapper found."
        exit 1
    }
    & $bashLauncher $wrapperSh @bashArgs
}

$exitCode = if (Get-Variable LASTEXITCODE -ErrorAction SilentlyContinue) { $LASTEXITCODE } else { 0 }
exit $exitCode
