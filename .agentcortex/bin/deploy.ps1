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

    # Prefer real Git Bash over PATH bash. On Windows, PATH may expose
    # WindowsApps\bash.exe, which is only a WSL placeholder when no distro is
    # installed.
    $gitCmd = Get-Command git -ErrorAction SilentlyContinue
    if ($gitCmd) {
        $gitDir = Split-Path -Parent $gitCmd.Source
        $gitRoot = Split-Path -Parent $gitDir
        if ($gitRoot) {
            $candidates += @(
                (Join-Path $gitRoot 'bin\bash.exe'),
                (Join-Path $gitRoot 'usr\bin\bash.exe')
            )
        }
    }

    $candidates += @(
        'C:\Program Files\Git\bin\bash.exe',
        'C:\Program Files\Git\usr\bin\bash.exe',
        'C:\Program Files (x86)\Git\bin\bash.exe'
    )

    $bashCmd = Get-Command bash -ErrorAction SilentlyContinue
    if ($bashCmd) { $candidates += $bashCmd.Source }

    # `bash --version` proves only that a bash binary exists, not that it can run
    # deploy.sh. A bare <git>\usr\bin\bash.exe answers --version with exit 0 while
    # carrying no /usr/bin on PATH, so the script dies at `dirname` (line 4) with
    # exit 127 and never writes a manifest. Probe the utilities deploy.sh actually
    # needs so an unusable candidate falls through to the next one.
    $probe = 'command -v dirname >/dev/null 2>&1 && command -v mktemp >/dev/null 2>&1'

    foreach ($candidate in $candidates | Select-Object -Unique) {
        if (-not (Test-Path -Path $candidate -PathType Leaf)) {
            continue
        }
        if ($candidate -like '*\WindowsApps\bash.exe') {
            continue
        }
        $usable = $false
        try {
            & $candidate -c $probe *> $null
            $usable = ($LASTEXITCODE -eq 0)
        } catch {
            # A broken app-execution alias can fail at process start. Skip this
            # candidate instead of aborting the whole search.
            $usable = $false
        }
        if ($usable) {
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
    Write-Host 'A bash that cannot resolve dirname/mktemp is skipped on purpose:'
    Write-Host 'the script needs a Git Bash tool environment, not just a bash binary.'
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
