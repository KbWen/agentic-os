#!/usr/bin/env pwsh
# No-python credential pre-screen FLOOR (ADR-008) - PowerShell parity of credential_floor.sh.
#
# A deliberately NARROW, FP-free SUBSET (AKIA / PEM / ghp_) for hosts without Python.
# Scans the STAGED content of each staged file, prints REDACTED `path:line: name`
# (NEVER the value); exit 1 on hit / 0 clean / 3 on git failure (fail-closed).
# Binds `-Staged` (NOT `--staged`) per the [cross-platform-cli] lesson; staged scan is
# the default. Uses case-SENSITIVE `-cmatch` to mirror `grep -E` exactly (sh<->ps1 parity).
[CmdletBinding()]
param([switch]$Staged)

$patterns = @(
    @{ name = 'aws-access-key-id'; re = 'AKIA[0-9A-Z]{16}' }
    @{ name = 'pem-private-key';   re = '-----BEGIN[ A-Z]*PRIVATE KEY-----' }
    @{ name = 'github-token';      re = 'ghp_[0-9A-Za-z]{36}' }
)
$allow = 'pragma: allowlist secret'

$files = & git diff --cached --name-only 2>$null
if ($LASTEXITCODE -ne 0) { exit 3 }          # fail-closed: never a silent 'clean'
if (-not $files) { exit 0 }

$hit = 0
foreach ($f in $files) {
    if ([string]::IsNullOrEmpty($f)) { continue }
    $content = & git show ":$f" 2>$null
    if ($LASTEXITCODE -ne 0) { continue }    # staged deletion -> nothing to scan
    $lineno = 0
    foreach ($line in @($content)) {
        $lineno++
        if (-not [string]::IsNullOrEmpty($line) -and $line.Contains($allow)) { continue }
        foreach ($p in $patterns) {
            if ($line -cmatch $p.re) {
                [Console]::Error.WriteLine(('{0}:{1}: {2}' -f $f, $lineno, $p.name))
                $hit = 1
            }
        }
    }
}
if ($hit -ne 0) {
    [Console]::Error.WriteLine('ACX credential floor: high-confidence secret shape in staged content (redacted above). Rotate/remove it, then re-commit. (narrow no-python floor; a full scan needs the python scanner or CI secret scanning)')
}
exit $hit
