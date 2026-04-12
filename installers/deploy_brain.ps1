param(
    [string]$Target = '.',
    [string]$Source = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Normalize-PathString {
    param([string]$Path)
    if ($Path -and $Path.StartsWith('\\?\')) { return $Path.Substring(4) }
    return $Path
}

function Resolve-BashLauncher {
    $bashCmd = Get-Command bash -ErrorAction SilentlyContinue
    if ($bashCmd) { return $bashCmd.Source }

    foreach ($candidate in @(
        'C:\Program Files\Git\bin\bash.exe',
        'C:\Program Files\Git\usr\bin\bash.exe',
        'C:\Program Files (x86)\Git\bin\bash.exe'
    )) {
        if (Test-Path -Path $candidate -PathType Leaf) {
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
    Write-Error 'bash is not installed. Install Git Bash or WSL, then rerun deploy_brain.ps1.'
    exit 1
}

# Build argument list
$bashArgs = @()
if ($Source) { $bashArgs += '--source'; $bashArgs += $Source }
$bashArgs += $Target

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
