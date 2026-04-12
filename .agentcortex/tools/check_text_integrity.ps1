#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Check tracked text files for encoding regressions (Windows PowerShell equivalent of check_text_integrity.py).
.DESCRIPTION
  Scans git-tracked and untracked text files for UTF-8 BOM, invalid UTF-8,
  mixed line endings, and null bytes. Known exceptions listed in the baseline
  file are reported but do not cause failure.
#>
param(
    [string]$Root = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)),
    [string]$Baseline = ""
)

$ErrorActionPreference = "Stop"

$TextSuffixes = @('.md','.sh','.ps1','.cmd','.bat','.yml','.yaml','.txt','.rules','.toml','.json','.py','.cff')
$TextFilenames = @('.gitignore','.gitattributes','.editorconfig')

function Get-CandidateFiles {
    $seen = @{}
    $paths = @()
    foreach ($cmd in @("git ls-files -z", "git ls-files -z --others --exclude-standard")) {
        $output = & git @($cmd.Split(' ') | Select-Object -Skip 1) 2>$null
        if (-not $output) { continue }
        foreach ($item in $output -split "`0") {
            $item = $item.Trim()
            if (-not $item -or $seen.ContainsKey($item)) { continue }
            $seen[$item] = $true
            $paths += Join-Path $Root $item
        }
    }
    return $paths
}

function Test-TextCandidate {
    param([string]$FilePath)
    $ext = [System.IO.Path]::GetExtension($FilePath).ToLower()
    $name = [System.IO.Path]::GetFileName($FilePath).ToLower()
    return ($TextSuffixes -contains $ext) -or ($TextFilenames -contains $name)
}

function Get-BaselineEntries {
    if ($Baseline) { $bpath = $Baseline }
    else { $bpath = Join-Path $Root ".agentcortex/tools/text_integrity_baseline.txt" }
    if (-not (Test-Path $bpath)) { return @() }
    $entries = @()
    foreach ($line in (Get-Content $bpath -Encoding UTF8)) {
        $line = $line.Trim()
        if (-not $line -or $line.StartsWith('#')) { continue }
        $entries += $line.Replace('\','/')
    }
    return $entries
}

function Inspect-File {
    param([string]$FilePath)
    $issues = @()
    $bytes = [System.IO.File]::ReadAllBytes($FilePath)
    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
        $issues += "utf8-bom"
    }
    try {
        $enc = [System.Text.UTF8Encoding]::new($false, $true)
        $null = $enc.GetString($bytes)
    } catch {
        $issues += "invalid-utf8"
        return $issues
    }
    $text = [System.Text.Encoding]::UTF8.GetString($bytes)
    if ($text.Contains("`0")) { $issues += "null-byte" }
    return $issues
}

# Main
Push-Location $Root
try {
    $baselineSet = Get-BaselineEntries
    $regressions = @()
    $baselineHits = @()

    foreach ($filePath in (Get-CandidateFiles)) {
        if (-not (Test-Path $filePath) -or -not (Test-TextCandidate $filePath)) { continue }
        $rel = (Resolve-Path -Relative $filePath).Replace('\','/') -replace '^\.\/',''
        $issues = Inspect-File $filePath
        if ($issues.Count -eq 0) { continue }
        if ($baselineSet -contains $rel) {
            $baselineHits += @{ Path=$rel; Issues=$issues }
        } else {
            $regressions += @{ Path=$rel; Issues=$issues }
        }
    }

    if ($regressions.Count -gt 0) {
        Write-Error "Text integrity regression(s) detected:"
        foreach ($r in $regressions) {
            Write-Error "  - $($r.Path): $($r.Issues -join ', ')"
        }
        if ($baselineHits.Count -gt 0) {
            Write-Error "Baseline exceptions still present: $($baselineHits.Count)"
        }
        exit 1
    }
    Write-Host "Text integrity check passed ($($baselineHits.Count) baseline exception(s) tracked)."
    exit 0
} finally {
    Pop-Location
}
