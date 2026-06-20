param(
    [switch]$NoPython
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Normalize-PathString {
    param([Parameter(Mandatory = $true)][string]$Path)
    # Strip Windows long-path prefix (\\?\) before any further normalization.
    if ($Path.StartsWith('\\?\')) { $Path = $Path.Substring(4) }
    # Unify mixed separators to backslash so string-based comparisons are stable on Windows.
    return $Path -replace '/', '\'
}

function Join-NormalPath {
    param(
        [Parameter(Mandatory = $true)][string]$Base,
        [Parameter(Mandatory = $true)][string]$Child
    )
    return Normalize-PathString ([System.IO.Path]::Combine((Normalize-PathString $Base), $Child))
}

function Add-Result {
    param(
        [Parameter(Mandatory = $true)][string]$Level,
        [Parameter(Mandatory = $true)][string]$Message
    )

    Write-Output "[$Level] $Message"
    switch ($Level) {
        'PASS' { $script:PassCount++ }
        'WARN' { $script:WarnCount++ }
        'FAIL' { $script:FailCount++ }
        'SKIP' { $script:SkipCount++ }
    }
}

function Show-IndentedOutput {
    param([string]$Text)
    if (-not $Text) { return }
    foreach ($line in ($Text -split "`r?`n")) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        Write-Output "  $line"
    }
}

function Test-FileGroup {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string[]]$Paths
    )
    $missing = @($Paths | Where-Object { -not (Test-Path -Path $_ -PathType Leaf) })
    if ($missing.Count -gt 0) {
        Add-Result -Level 'FAIL' -Message $Label
        foreach ($path in $missing) {
            Write-Output "  missing: $path"
        }
        return
    }
    Add-Result -Level 'PASS' -Message $Label
}

function Test-OptionalFileGroup {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string[]]$Paths
    )
    $missing = @($Paths | Where-Object { -not (Test-Path -Path $_ -PathType Leaf) })
    if ($missing.Count -gt 0) {
        Add-Result -Level 'WARN' -Message $Label
        foreach ($path in $missing) {
            Write-Output "  missing (optional): $path"
        }
        return
    }
    Add-Result -Level 'PASS' -Message $Label
}

function Test-DirGroup {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string[]]$Paths
    )
    $missing = @($Paths | Where-Object { -not (Test-Path -Path $_ -PathType Container) })
    if ($missing.Count -gt 0) {
        Add-Result -Level 'FAIL' -Message $Label
        foreach ($path in $missing) {
            Write-Output "  missing: $path"
        }
        return
    }
    Add-Result -Level 'PASS' -Message $Label
}

function Test-ContainsLiteral {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Pattern,
        [Parameter(Mandatory = $true)][string]$SuccessMessage,
        [Parameter(Mandatory = $true)][string]$FailureMessage
    )
    if (-not (Test-Path -Path $Path -PathType Leaf)) {
        Add-Result -Level 'FAIL' -Message $FailureMessage
        return
    }
    $content = Get-Content -Raw -Encoding utf8 -Path $Path
    if ($content.Contains($Pattern)) {
        Add-Result -Level 'PASS' -Message $SuccessMessage
    }
    else {
        Add-Result -Level 'FAIL' -Message $FailureMessage
    }
}

function Get-NormalizedContent {
    # Read file content and normalize line endings to LF.
    # .NET regex anchors ($) in (?m) mode match only before \n, not \r\n,
    # so CRLF files silently fail patterns like ^status:\s*living$.
    # Prefer this over Get-Content -Raw for any check that uses multiline regex.
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [string]$Encoding = 'utf8'
    )
    $raw = Get-Content -Path $Path -Raw -Encoding $Encoding -ErrorAction SilentlyContinue
    if ($null -eq $raw) { return $null }
    return $raw -replace "`r`n", "`n" -replace "`r", "`n"
}

function Test-ContainsRegex {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Pattern,
        [Parameter(Mandatory = $true)][string]$SuccessMessage,
        [Parameter(Mandatory = $true)][string]$FailureMessage
    )
    if (-not (Test-Path -Path $Path -PathType Leaf)) {
        Add-Result -Level 'FAIL' -Message $FailureMessage
        return
    }
    $content = Get-NormalizedContent -Path $Path
    if ($content -match $Pattern) {
        Add-Result -Level 'PASS' -Message $SuccessMessage
    }
    else {
        Add-Result -Level 'FAIL' -Message $FailureMessage
    }
}

function Invoke-PythonCheck {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string]$MissingPythonLevel,
        [Parameter(Mandatory = $true)][string]$ScriptPath,
        [string[]]$Arguments = @()
    )

    if (-not (Test-Path -Path $ScriptPath -PathType Leaf)) {
        Add-Result -Level 'SKIP' -Message "$Label -- tool not present"
        return
    }
    if (-not $script:PythonCommand) {
        if ($NoPython) {
            Add-Result -Level 'SKIP' -Message "$Label -- python checks disabled (--NoPython)"
        } else {
            Add-Result -Level 'WARN' -Message "$Label -- python unavailable (install Python 3.9+ for full validation)"
        }
        return
    }

    $previousErrorActionPreference = $ErrorActionPreference
    $hadNativePreference = Test-Path variable:PSNativeCommandUseErrorActionPreference
    if ($hadNativePreference) {
        $previousNativePreference = $PSNativeCommandUseErrorActionPreference
        $PSNativeCommandUseErrorActionPreference = $false
    }
    $ErrorActionPreference = 'Continue'
    try {
        $output = & $script:PythonCommand.Source $ScriptPath @Arguments 2>&1 | Out-String
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
        if ($hadNativePreference) {
            $PSNativeCommandUseErrorActionPreference = $previousNativePreference
        }
    }
    $exitCode = if (Get-Variable LASTEXITCODE -ErrorAction SilentlyContinue) { $LASTEXITCODE } else { 0 }
    if ($exitCode -eq 0) {
        Add-Result -Level 'PASS' -Message $Label
    }
    else {
        Add-Result -Level 'FAIL' -Message $Label
    }
    Show-IndentedOutput -Text $output
}

$script:PassCount = 0
$script:WarnCount = 0
$script:FailCount = 0
$script:SkipCount = 0
if ($NoPython) {
    $script:PythonCommand = $null
} else {
    $script:PythonCommand = Get-Command python3 -ErrorAction SilentlyContinue
    if (-not $script:PythonCommand) {
        $script:PythonCommand = Get-Command python -ErrorAction SilentlyContinue
    }
}

$scriptDir = Normalize-PathString ($PSScriptRoot)
if (-not $scriptDir) { $scriptDir = Normalize-PathString (Split-Path -Parent $PSCommandPath) }
if (-not $scriptDir) { $scriptDir = Normalize-PathString ((Get-Location).Path) }
$root = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine($scriptDir, '..', '..'))

$platformDoc = Join-NormalPath $root '.agentcortex/docs/CODEX_PLATFORM_GUIDE.md'
$claudePlatformDoc = Join-NormalPath $root '.agentcortex/docs/CLAUDE_PLATFORM_GUIDE.md'
$examplesDoc = Join-NormalPath $root '.agentcortex/docs/PROJECT_EXAMPLES.md'
$projectAgentsFile = Join-NormalPath $root 'AGENTS.md'
$projectClaudeFile = Join-NormalPath $root 'CLAUDE.md'
$workflowsDir = Join-NormalPath $root '.agent/workflows'
$claudeCommandsDir = Join-NormalPath $root '.claude/commands'
$codexInstall = Join-NormalPath $root '.codex/INSTALL.md'
$codexRules = Join-NormalPath $root '.codex/rules/default.rules'
$rootDeploySh = Join-NormalPath $root 'installers/deploy_brain.sh'
$rootDeployPs1 = Join-NormalPath $root 'installers/deploy_brain.ps1'
$rootDeployCmd = Join-NormalPath $root 'installers/deploy_brain.cmd'
$canonicalDeploySh = Join-NormalPath $root '.agentcortex/bin/deploy.sh'
$canonicalDeployPs1 = Join-NormalPath $root '.agentcortex/bin/deploy.ps1'
$canonicalValidateSh = Join-NormalPath $root '.agentcortex/bin/validate.sh'
$canonicalValidatePs1 = Join-NormalPath $root '.agentcortex/bin/validate.ps1'
$textIntegrityCheckPy = Join-NormalPath $root '.agentcortex/tools/check_text_integrity.py'
$textIntegrityCheckPs1 = Join-NormalPath $root '.agentcortex/tools/check_text_integrity.ps1'
$textIntegrityBaseline = Join-NormalPath $root '.agentcortex/tools/text_integrity_baseline.txt'
$triggerMetadataValidator = Join-NormalPath $root '.agentcortex/tools/validate_trigger_metadata.py'
$triggerCompactIndexGenerator = Join-NormalPath $root '.agentcortex/tools/generate_compact_index.py'
$guardContextWrite = Join-NormalPath $root '.agentcortex/tools/guard_context_write.py'
$guardedWritesLint = Join-NormalPath $root '.agentcortex/tools/lint_governed_writes.py'
$lifecycleFrontmatterCheck = Join-NormalPath $root '.agentcortex/tools/check_lifecycle_frontmatter.py'
$auditChainCheck = Join-NormalPath $root '.agentcortex/tools/check_audit_chain.py'
$archiveIndexJsonl = Join-NormalPath $root '.agentcortex/context/archive/INDEX.jsonl'
$lessonChainCheck = Join-NormalPath $root '.agentcortex/tools/check_lesson_chain.py'
$ssotCurrentState = Join-NormalPath $root '.agentcortex/context/current_state.md'
$commandSyncCheck = Join-NormalPath $root '.agentcortex/tools/check_command_sync.py'
$skillProvenanceCheck = Join-NormalPath $root '.agentcortex/tools/check_skill_provenance.py'
$triggerRegistry = Join-NormalPath $root '.agentcortex/metadata/trigger-registry.yaml'
$triggerCompactIndex = Join-NormalPath $root '.agentcortex/metadata/trigger-compact-index.json'
$lifecycleScenarios = Join-NormalPath $root '.agentcortex/metadata/lifecycle-scenarios.json'
$skillConflictMatrix = Join-NormalPath $root '.agent/rules/skill_conflict_matrix.md'
$agentConfigYaml = Join-NormalPath $root '.agent/config.yaml'
$optionalGuardHook = Join-NormalPath $root '.githooks/pre-commit.guard-ssot.sample'

$requiredFiles = @(
    (Join-NormalPath $workflowsDir 'hotfix.md'),
    (Join-NormalPath $workflowsDir 'worktree-first.md'),
    (Join-NormalPath $workflowsDir 'govern-docs.md'),
    (Join-NormalPath $workflowsDir 'handoff.md'),
    (Join-NormalPath $workflowsDir 'bootstrap.md'),
    (Join-NormalPath $workflowsDir 'plan.md'),
    (Join-NormalPath $workflowsDir 'implement.md'),
    (Join-NormalPath $workflowsDir 'review.md'),
    (Join-NormalPath $workflowsDir 'help.md'),
    (Join-NormalPath $workflowsDir 'test-skeleton.md'),
    (Join-NormalPath $workflowsDir 'commands.md'),
    (Join-NormalPath $workflowsDir 'routing.md'),
    (Join-NormalPath $workflowsDir 'test.md'),
    (Join-NormalPath $workflowsDir 'ship.md'),
    (Join-NormalPath $workflowsDir 'decide.md'),
    (Join-NormalPath $workflowsDir 'test-classify.md'),
    (Join-NormalPath $workflowsDir 'spec-intake.md'),
    (Join-NormalPath $workflowsDir 'adr.md'),
    (Join-NormalPath $workflowsDir 'audit.md'),
    (Join-NormalPath $workflowsDir 'brainstorm.md'),
    (Join-NormalPath $workflowsDir 'research.md'),
    (Join-NormalPath $workflowsDir 'retro.md'),
    (Join-NormalPath $workflowsDir 'spec.md'),
    (Join-NormalPath $workflowsDir 'sync-docs.md'),
    $skillConflictMatrix,
    $agentConfigYaml,
    $platformDoc,
    $claudePlatformDoc,
    $examplesDoc,
    $projectAgentsFile,
    $projectClaudeFile,
    $rootDeploySh,
    $rootDeployPs1,
    $rootDeployCmd,
    $canonicalDeploySh,
    $canonicalDeployPs1,
    $canonicalValidateSh,
    $canonicalValidatePs1,
    $commandSyncCheck,
    $textIntegrityCheckPy,
    $textIntegrityCheckPs1,
    $textIntegrityBaseline
)

$claudeRequiredFiles = @(
    (Join-NormalPath $claudeCommandsDir 'spec-intake.md'),
    (Join-NormalPath $claudeCommandsDir 'bootstrap.md'),
    (Join-NormalPath $claudeCommandsDir 'plan.md'),
    (Join-NormalPath $claudeCommandsDir 'implement.md'),
    (Join-NormalPath $claudeCommandsDir 'review.md'),
    (Join-NormalPath $claudeCommandsDir 'test.md'),
    (Join-NormalPath $claudeCommandsDir 'handoff.md'),
    (Join-NormalPath $claudeCommandsDir 'ship.md'),
    (Join-NormalPath $claudeCommandsDir 'decide.md'),
    (Join-NormalPath $claudeCommandsDir 'test-classify.md'),
    (Join-NormalPath $claudeCommandsDir 'claude-cli.md'),
    (Join-NormalPath $root '.claude/agents/acx-implementer.md'),
    (Join-NormalPath $root '.claude/agents/acx-reviewer.md'),
    (Join-NormalPath $root '.claude/agents/acx-tester.md'),
    (Join-NormalPath $root '.claude/agents/acx-handoff.md'),
    (Join-NormalPath $root '.claude/agents/acx-shipper.md')
)

$requiredDirs = @(
    $workflowsDir,
    $claudeCommandsDir,
    (Join-NormalPath $root '.agents/skills'),
    (Join-NormalPath $root '.agent/skills')
)

# Source-repo detection: the source repo has the canonical deploy script
# but no .agentcortex-manifest (which is generated during deploy to downstream).
# In source-repo mode, adapter-surface checks are skipped because those
# directories are created by deploy in downstream repos.
$isSourceRepo = (Test-Path -Path $canonicalDeploySh -PathType Leaf) -and
                (-not (Test-Path -Path (Join-NormalPath $root '.agentcortex-manifest') -PathType Leaf))

# Both source and downstream repos keep deploy_brain.* under installers/.
# No path redefinition needed — $rootDeploySh/Ps1/Cmd already point to installers/.

$optionalModuleFiles = @(
    (Join-NormalPath $workflowsDir 'ask-openrouter.md'),
    (Join-NormalPath $workflowsDir 'codex-cli.md'),
    (Join-NormalPath $workflowsDir 'claude-cli.md')
)

$deprecatedWorkflowFiles = @(
    (Join-NormalPath $workflowsDir 'new-feature.md'),
    (Join-NormalPath $workflowsDir 'medium-feature.md'),
    (Join-NormalPath $workflowsDir 'small-fix.md')
)
# Emit FAIL-on-present / PASS-on-absent to match validate.sh exactly (F4 parity:
# the bash side records a PASS when none are present, so without this else the
# two validators differed by one PASS).
$deprecatedFound = @()
foreach ($df in $deprecatedWorkflowFiles) {
    if (Test-Path -Path $df -PathType Leaf) { $deprecatedFound += (Split-Path -Leaf $df) }
}
if ($deprecatedFound.Count -gt 0) {
    Add-Result -Level 'FAIL' -Message "deprecated workflow files still present (remove them): $($deprecatedFound -join ', ')"
} else {
    Add-Result -Level 'PASS' -Message 'deprecated workflow files absent (new-feature, medium-feature, small-fix)'
}

if ($isSourceRepo) {
    Add-Result -Level 'SKIP' -Message 'claude adapter files -- source repo (created by deploy in downstream)'
    Test-FileGroup -Label 'required framework files present' -Paths $requiredFiles
    Test-OptionalFileGroup -Label 'optional module workflow files present' -Paths $optionalModuleFiles
    $sourceDirs = @(
        $workflowsDir,
        (Join-NormalPath $root '.agents/skills'),
        (Join-NormalPath $root '.agent/skills')
    )
    Test-DirGroup -Label 'required framework directories present' -Paths $sourceDirs
}
else {
    Test-FileGroup -Label 'required framework files present' -Paths $requiredFiles
    Test-OptionalFileGroup -Label 'optional module workflow files present' -Paths $optionalModuleFiles
    Test-FileGroup -Label 'claude adapter files present' -Paths $claudeRequiredFiles
    Test-DirGroup -Label 'required framework directories present' -Paths $requiredDirs
}

Invoke-PythonCheck -Label 'text integrity check' -MissingPythonLevel 'FAIL' -ScriptPath $textIntegrityCheckPy -Arguments @('--root', $root, '--baseline', $textIntegrityBaseline)

if (Test-Path -Path $triggerRegistry -PathType Leaf) {
    if (Test-Path -Path $triggerCompactIndex -PathType Leaf) {
        Add-Result -Level 'PASS' -Message 'metadata runtime artifacts present'
    }
    else {
        Add-Result -Level 'FAIL' -Message 'metadata runtime incomplete -- missing trigger-compact-index.json'
        Write-Host '  fix: re-run deploy to restore metadata, or regenerate with .agentcortex/tools/generate_compact_index.py'
    }

    if (Test-Path -Path $triggerMetadataValidator -PathType Leaf) {
        if (Test-Path -Path $lifecycleScenarios -PathType Leaf) {
            Invoke-PythonCheck -Label 'metadata deep validation' -MissingPythonLevel 'FAIL' -ScriptPath $triggerMetadataValidator -Arguments @('--root', $root)
        }
        else {
            Add-Result -Level 'FAIL' -Message 'metadata deep validation unavailable -- lifecycle scenarios missing'
            Write-Host '  fix: re-run deploy to restore .agentcortex/metadata/lifecycle-scenarios.json'
        }
    }
    else {
        Add-Result -Level 'SKIP' -Message 'metadata deep checks -- CI-only validator not deployed (safe to ignore downstream)'
    }

    if (Test-Path -Path $triggerCompactIndexGenerator -PathType Leaf) {
        Invoke-PythonCheck -Label 'compact index freshness' -MissingPythonLevel 'FAIL' -ScriptPath $triggerCompactIndexGenerator -Arguments @('--root', $root, '--check')
    }
    else {
        Add-Result -Level 'SKIP' -Message 'compact index freshness -- CI-only generator not deployed (safe to ignore downstream)'
    }
}
elseif (Test-Path -Path $triggerCompactIndex -PathType Leaf) {
    Add-Result -Level 'FAIL' -Message 'metadata runtime incomplete -- compact index present without trigger registry'
    Write-Host '  fix: re-run deploy to restore .agentcortex/metadata/trigger-registry.yaml'
}
else {
    Add-Result -Level 'SKIP' -Message 'metadata checks -- no trigger registry found (safe to ignore if not using skill metadata)'
}

Invoke-PythonCheck -Label 'command sync check' -MissingPythonLevel 'FAIL' -ScriptPath $commandSyncCheck -Arguments @('--root', $root)

# Guarded-write lint mirror of validate.sh integration.
Invoke-PythonCheck -Label 'guarded-write lint (governance paths)' -MissingPythonLevel 'FAIL' -ScriptPath $guardedWritesLint -Arguments @('--root', $root)

# Lifecycle frontmatter check mirror of validate.sh integration.
Invoke-PythonCheck -Label 'lifecycle frontmatter (governance docs)' -MissingPythonLevel 'FAIL' -ScriptPath $lifecycleFrontmatterCheck -Arguments @('--root', $root)

# Skill provenance + compatibility floor (backlog #80/#81) -- mirror of validate.sh.
# Source-repo only; absent downstream (not in deploy runtime_tools) -> graceful SKIP.
Invoke-PythonCheck -Label 'skill provenance + compatibility floor' -MissingPythonLevel 'FAIL' -ScriptPath $skillProvenanceCheck -Arguments @('--root', $root)

# Verify the hash chain on the archive INDEX.jsonl.
if (Test-Path -Path $archiveIndexJsonl -PathType Leaf) {
    Invoke-PythonCheck -Label 'audit chain integrity (INDEX.jsonl)' -MissingPythonLevel 'FAIL' -ScriptPath $auditChainCheck -Arguments @('--path', $archiveIndexJsonl, '--quiet')
} else {
    Add-Result -Level 'SKIP' -Message 'audit chain integrity -- archive INDEX.jsonl not present'
}

# C1: git append-only WITNESS for INDEX.jsonl (ADR-003 amendment; spec
# audit-chain-tamper-evidence AC-4/5/6). Mirror of validate.sh. The back-linked
# chain cannot detect TAIL-TRUNCATION; git's merge-base with origin/main is used
# as an EXTERNAL append-only witness (committed baseline must be a line-prefix of
# the working copy). Tamper-EVIDENCE, not prevention. Degrades to WARN (never
# silent PASS) when git / origin/main / baseline is unavailable. Use cmd.exe
# redirection for the git blob so Windows PowerShell 5.1 cannot mis-decode UTF-8
# JSONL through its native pipeline.
$indexRel = '.agentcortex/context/archive/INDEX.jsonl'
if (Test-Path -Path $archiveIndexJsonl -PathType Leaf) {
    $gitPresent = [bool](Get-Command git -ErrorAction SilentlyContinue)
    $isRepo = $false
    if ($gitPresent) { git -C $root rev-parse --git-dir *> $null; $isRepo = ($LASTEXITCODE -eq 0) }
    if (-not $gitPresent -or -not $isRepo) {
        Add-Result -Level 'WARN' -Message 'INDEX.jsonl append-only witness -- git unavailable or not a git repo'
    } else {
        git -C $root rev-parse --verify -q origin/main *> $null
        if ($LASTEXITCODE -ne 0) { git -C $root fetch -q --depth=1 origin main *> $null }
        $witnessBase = (git -C $root merge-base origin/main HEAD 2>$null | Select-Object -First 1)
        if (-not $witnessBase) {
            Add-Result -Level 'WARN' -Message 'INDEX.jsonl append-only witness -- no merge-base with origin/main (offline, no remote, or unrelated history)'
        } else {
            git -C $root cat-file -e "${witnessBase}:$indexRel" 2>$null
            if ($LASTEXITCODE -ne 0) {
                Add-Result -Level 'WARN' -Message 'INDEX.jsonl append-only witness -- not present at merge-base (new log surface)'
            } else {
                $baseTmp = New-TemporaryFile
                try {
                    $objectName = "${witnessBase}:$indexRel"
                    & cmd.exe /c "git -C `"$root`" show `"$objectName`" > `"$($baseTmp.FullName)`""
                    if ($LASTEXITCODE -ne 0) {
                        Add-Result -Level 'WARN' -Message 'INDEX.jsonl append-only witness -- unable to read baseline blob'
                    } else {
                        $baseLines = @(Get-Content -LiteralPath $baseTmp.FullName -Encoding UTF8 | Where-Object { $_ -ne '' })
                        $localLines = @(Get-Content -LiteralPath $archiveIndexJsonl -Encoding UTF8 | Where-Object { $_ -ne '' })
                        if ($localLines.Count -lt $baseLines.Count) {
                            Add-Result -Level 'FAIL' -Message "INDEX.jsonl append-only witness -- local has $($localLines.Count) entries, fewer than baseline $($baseLines.Count) at merge-base (tail-truncation?)"
                        } else {
                            $prefixOk = $true
                            for ($i = 0; $i -lt $baseLines.Count; $i++) {
                                if ($localLines[$i] -ne $baseLines[$i]) { $prefixOk = $false; break }
                            }
                            if (-not $prefixOk) {
                                Add-Result -Level 'FAIL' -Message 'INDEX.jsonl append-only witness -- committed baseline is not a prefix of local (a previously-published audit entry was edited or deleted)'
                            } else {
                                Add-Result -Level 'PASS' -Message 'INDEX.jsonl append-only witness -- baseline is a prefix of local (append-only invariant holds)'
                            }
                        }
                    }
                } finally {
                    Remove-Item -LiteralPath $baseTmp.FullName -Force -ErrorAction SilentlyContinue
                }
            }
        }
    }
}

# Global Lessons chain (mirror of validate.sh integration).
if (Test-Path -Path $ssotCurrentState -PathType Leaf) {
    Invoke-PythonCheck -Label 'lesson chain integrity (Global Lessons)' -MissingPythonLevel 'FAIL' -ScriptPath $lessonChainCheck -Arguments @('--path', $ssotCurrentState, '--quiet')
} else {
    Add-Result -Level 'SKIP' -Message 'lesson chain integrity -- current_state.md not present'
}

# Token lifecycle drift advisory (backlog #51 / issue #157): mirror of the
# validate.sh block. WARN when any scenario/aggregate GREW beyond slack (advisory,
# never FAIL); baseline absent -> WARN to seed; shrink is intentionally not flagged.
# Teeth live in tests/ci/test_lifecycle_baseline_drift.py.
$lifecycleBaseline = Join-Path $root '.agentcortex/metadata/lifecycle-baseline.json'
$lifecycleUpdater = Join-Path $root '.agentcortex/tools/update_lifecycle_baseline.py'
if (-not (Test-Path -Path $lifecycleBaseline -PathType Leaf)) {
    Add-Result -Level 'WARN' -Message 'token lifecycle baseline absent (.agentcortex/metadata/lifecycle-baseline.json); seed with update_lifecycle_baseline.py --init'
} elseif (-not $script:PythonCommand) {
    Add-Result -Level 'SKIP' -Message 'token lifecycle drift -- python unavailable or disabled (--NoPython)'
} elseif (-not (Test-Path -Path $lifecycleUpdater -PathType Leaf)) {
    Add-Result -Level 'SKIP' -Message 'token lifecycle drift -- updater not present (update_lifecycle_baseline.py missing)'
} else {
    $prevEap = $ErrorActionPreference
    $hadNative = Test-Path variable:PSNativeCommandUseErrorActionPreference
    if ($hadNative) { $prevNative = $PSNativeCommandUseErrorActionPreference; $PSNativeCommandUseErrorActionPreference = $false }
    $ErrorActionPreference = 'Continue'
    try {
        $driftOut = & $script:PythonCommand.Source $lifecycleUpdater '--root' $root '--dry-run' 2>&1 | Out-String
    } finally {
        $ErrorActionPreference = $prevEap
        if ($hadNative) { $PSNativeCommandUseErrorActionPreference = $prevNative }
    }
    $driftExit = if (Get-Variable LASTEXITCODE -ErrorAction SilentlyContinue) { $LASTEXITCODE } else { 0 }
    if ($driftExit -eq 0) {
        Add-Result -Level 'PASS' -Message 'token lifecycle drift: within slack'
    } else {
        Add-Result -Level 'WARN' -Message 'token lifecycle drift or detector error (advisory, never FAIL); see output. If drift is intended, re-baseline: update_lifecycle_baseline.py --apply'
        Show-IndentedOutput -Text $driftOut
    }
}

# Unresolved merge-conflict markers in tracked files (mirror of validate.sh).
# See validate.sh for rationale. Matches only the unambiguous "<<<<<<< " /
# ">>>>>>> " opening/closing forms; bare "=======" is excluded (markdown setext
# H2 collision). git grep -I skips binary; the verdict is byte-identical to the
# bash check. The validator pair self-excludes.
$gitPresentMarkers = [bool](Get-Command git -ErrorAction SilentlyContinue)
$isRepoMarkers = $false
if ($gitPresentMarkers) { git -C $root rev-parse --git-dir *> $null; $isRepoMarkers = ($LASTEXITCODE -eq 0) }
if (-not $gitPresentMarkers -or -not $isRepoMarkers) {
    Add-Result -Level 'WARN' -Message 'merge-conflict marker scan -- git unavailable or not a git repo'
} else {
    $conflictMarkerHits = git -C $root grep -I -n -E '^(<<<<<<< |>>>>>>> )' -- . ':(exclude).agentcortex/bin/validate.sh' ':(exclude).agentcortex/bin/validate.ps1' ':(exclude)tests/guard/test_conflict_markers.py' 2>$null
    if ($conflictMarkerHits) {
        Add-Result -Level 'FAIL' -Message 'unresolved merge-conflict markers in tracked files'
        Show-IndentedOutput -Text ($conflictMarkerHits | Out-String)
    } else {
        Add-Result -Level 'PASS' -Message 'no unresolved merge-conflict markers in tracked files'
    }
}

$legacyAuditHelper = Join-NormalPath $root 'tools/audit_ai_paths.sh'
if (Test-Path -Path $legacyAuditHelper -PathType Leaf) {
    Add-Result -Level 'FAIL' -Message "legacy audit helper should move under .agentcortex/tools/: $legacyAuditHelper"
}
else {
    Add-Result -Level 'PASS' -Message 'legacy audit helper not present at tools/audit_ai_paths.sh'
}

$skillErrors = 0
Get-ChildItem -Path (Join-NormalPath $root '.agent/skills') -File | ForEach-Object {
    if ($_.Name -eq '.gitkeep') { return }
    if ($_.Length -le 0) {
        Write-Output "  empty skill metadata: $($_.FullName)"
        $skillErrors++
    }
    $codexSkillPath = Join-NormalPath (Join-NormalPath $root '.agents/skills') $_.Name
    if (-not (Test-Path -Path $codexSkillPath -PathType Container)) {
        Write-Output "  missing codex skill dir: $codexSkillPath"
        $skillErrors++
    }
    elseif (-not (Test-Path -Path (Join-NormalPath $codexSkillPath 'SKILL.md') -PathType Leaf)) {
        Write-Output "  missing skill definition: $(Join-NormalPath $codexSkillPath 'SKILL.md')"
        $skillErrors++
    }
}
if ($skillErrors -gt 0) {
    Add-Result -Level 'FAIL' -Message 'skill metadata mirrors out of sync'
}
else {
    Add-Result -Level 'PASS' -Message 'skill metadata mirrors are consistent'
}

if (-not $isSourceRepo) {
    Test-FileGroup -Label 'legacy rule surfaces present' -Paths @(
        (Join-NormalPath $root '.antigravity/rules.md'),
        (Join-NormalPath $root '.agent/rules/rules.md'),
        $codexInstall
    )
    Test-ContainsRegex -Path (Join-NormalPath $root '.agent/rules/rules.md') -Pattern '\.antigravity/rules\.md' -SuccessMessage 'legacy rules redirect to canonical antigravity rules' -FailureMessage 'legacy rules missing canonical redirect'
    Test-ContainsLiteral -Path (Join-NormalPath $root '.agent/rules/rules.md') -Pattern 'legacy compatibility' -SuccessMessage 'legacy rules include compatibility marker' -FailureMessage 'legacy rules missing compatibility marker'
    Test-ContainsLiteral -Path (Join-NormalPath $root '.antigravity/rules.md') -Pattern 'docker system prune -a' -SuccessMessage 'antigravity rules include docker system prune guard' -FailureMessage 'antigravity rules missing docker system prune guard'
    Test-ContainsLiteral -Path (Join-NormalPath $root '.antigravity/rules.md') -Pattern 'chown -R' -SuccessMessage 'antigravity rules include chown -R guard' -FailureMessage 'antigravity rules missing chown -R guard'
    Test-ContainsLiteral -Path (Join-NormalPath $root '.antigravity/rules.md') -Pattern 'rollback' -SuccessMessage 'antigravity rules include rollback reminder' -FailureMessage 'antigravity rules missing rollback reminder'
} else {
    Add-Result -Level 'SKIP' -Message 'legacy rule surfaces -- source repo (adapter surfaces created by deploy)'
}

$activeCodexRules = Join-NormalPath $root 'codex/rules/default.rules'
if (-not (Test-Path -Path $activeCodexRules -PathType Leaf)) { $activeCodexRules = $codexRules }
Test-ContainsRegex -Path $activeCodexRules -Pattern 'prefix_rule\(' -SuccessMessage 'codex rules include prefix_rule()' -FailureMessage 'codex rules missing prefix_rule()'
Test-ContainsLiteral -Path $activeCodexRules -Pattern 'docker system prune -a' -SuccessMessage 'codex rules include docker system prune guard' -FailureMessage 'codex rules missing docker system prune guard'
Test-ContainsLiteral -Path $activeCodexRules -Pattern 'chown -R' -SuccessMessage 'codex rules include chown -R guard' -FailureMessage 'codex rules missing chown -R guard'

Test-ContainsLiteral -Path $rootDeploySh -Pattern '.agentcortex/bin/deploy.sh' -SuccessMessage 'deploy_brain.sh references canonical deploy script' -FailureMessage 'deploy_brain.sh missing canonical deploy reference'
Test-ContainsLiteral -Path $rootDeployPs1 -Pattern "'.agentcortex', 'bin', 'deploy.sh'" -SuccessMessage 'deploy_brain.ps1 references canonical deploy script' -FailureMessage 'deploy_brain.ps1 missing canonical deploy reference'
Test-ContainsLiteral -Path $rootDeployCmd -Pattern 'deploy_brain.ps1' -SuccessMessage 'deploy_brain.cmd delegates to sibling wrapper' -FailureMessage 'deploy_brain.cmd missing sibling-wrapper delegation'

$worklogContractFiles = @(
    (Join-NormalPath $root 'AGENTS.md'),
    (Join-NormalPath $root '.agent/rules/engineering_guardrails.md'),
    (Join-NormalPath $root '.agent/rules/security_guardrails.md'),
    (Join-NormalPath $root '.agent/rules/state_machine.md'),
    (Join-NormalPath $root '.agent/workflows/bootstrap.md'),
    (Join-NormalPath $root '.agent/workflows/plan.md'),
    (Join-NormalPath $root '.agent/workflows/handoff.md'),
    (Join-NormalPath $root '.agent/workflows/ship.md'),
    $platformDoc,
    (Join-NormalPath $root '.agentcortex/docs/NONLINEAR_SCENARIOS.md'),
    (Join-NormalPath $root '.agentcortex/docs/guides/antigravity-v5-runtime.md')
)
$worklogContractErrors = 0
foreach ($file in $worklogContractFiles) {
    if (-not (Test-Path -Path $file -PathType Leaf)) {
        Write-Output "  worklog contract file not found: $file"
        $worklogContractErrors++
        continue
    }
    $content = Get-Content -Raw -Encoding utf8 -Path $file
    if (-not $content.Contains('<worklog-key>')) {
        Write-Output "  worklog contract missing normalized key reference: $file"
        $worklogContractErrors++
    }
    if ($content.Contains('docs/context/work/<branch-name>.md')) {
        Write-Output "  stale branch-name worklog path contract: $file"
        $worklogContractErrors++
    }
    if ($content.Contains('docs/context/work/<branch>.md')) {
        Write-Output "  stale raw branch worklog path contract: $file"
        $worklogContractErrors++
    }
}
if ($worklogContractErrors -gt 0) {
    Add-Result -Level 'FAIL' -Message 'work log contract references are stale'
}
else {
    Add-Result -Level 'PASS' -Message 'work log contract references use normalized keys'
}

$archiveContractFiles = @(
    (Join-NormalPath $root '.agent/workflows/handoff.md'),
    (Join-NormalPath $root '.agentcortex/docs/guides/token-governance.md'),
    (Join-NormalPath $root '.agentcortex/docs/guides/portable-minimal-kit.md')
)
$archiveContractErrors = 0
foreach ($file in $archiveContractFiles) {
    if (-not (Test-Path -Path $file -PathType Leaf)) {
        Write-Output "  archive contract file not found: $file"
        $archiveContractErrors++
        continue
    }
    $content = Get-Content -Raw -Encoding utf8 -Path $file
    if (-not $content.Contains('<worklog-key>-<YYYYMMDD>')) {
        Write-Output "  archive contract missing normalized key reference: $file"
        $archiveContractErrors++
    }
    if ($content.Contains('docs/context/archive/work/<branch>-<YYYYMMDD>.md')) {
        Write-Output "  stale archive branch worklog path contract: $file"
        $archiveContractErrors++
    }
}
if ($archiveContractErrors -gt 0) {
    Add-Result -Level 'FAIL' -Message 'archive contract references are stale'
}
else {
    Add-Result -Level 'PASS' -Message 'archive contract references use normalized keys'
}

Test-ContainsLiteral -Path (Join-NormalPath $workflowsDir 'bootstrap.md') -Pattern 'Recommended Skills' -SuccessMessage 'bootstrap includes Recommended Skills contract' -FailureMessage 'bootstrap missing Recommended Skills contract'
# ADR-004: bootstrap MUST ship the override-layer load step (structural enforcement only; per-agent compliance is honor-system, not falsely test-enforced).
Test-ContainsLiteral -Path (Join-NormalPath $workflowsDir 'bootstrap.md') -Pattern 'Load Override Layer' -SuccessMessage 'bootstrap ships override-layer load step (ADR-004 §1a)' -FailureMessage 'bootstrap missing override-layer load step (ADR-004 §1a)'
# ADR-007: bootstrap MUST ship the downstream-capabilities load step (§1b).
Test-ContainsLiteral -Path (Join-NormalPath $workflowsDir 'bootstrap.md') -Pattern 'Load Downstream Capabilities' -SuccessMessage 'bootstrap ships downstream-capabilities load step (ADR-007 §1b)' -FailureMessage 'bootstrap missing downstream-capabilities load step (ADR-007 §1b)'
# ADR-009: bootstrap MUST ship the kb-consult scope-detected row (§3.6 / §1b knowledge_sources). Structural only; consult quality is honor-system.
Test-ContainsLiteral -Path (Join-NormalPath $workflowsDir 'bootstrap.md') -Pattern 'kb-consult' -SuccessMessage 'bootstrap ships KB-consult scope-detected row (ADR-009)' -FailureMessage 'bootstrap missing KB-consult scope-detected row (ADR-009)'
# ADR-007: a present downstream-capabilities.yaml MUST be schema gate-safe (rejected, not clamped).
$capValidator = Join-NormalPath $root '.agentcortex/tools/validate_downstream_capabilities.py'
$capFile = Join-NormalPath $root '.agentcortex/context/private/downstream-capabilities.yaml'
if (Test-Path $capValidator) {
    # python-present + gate-unsafe -> FAIL (CI always has python); no-python -> WARN
    # (advisory; bootstrap §1b agent-discipline is the runtime guarantee there).
    Invoke-PythonCheck -Label 'downstream-capabilities gate-safety' -MissingPythonLevel 'WARN' -ScriptPath $capValidator -Arguments @($capFile)
} else {
    Add-Result -Level 'SKIP' -Message 'downstream-capabilities gate-safety -- validator not deployed (safe to ignore)'
}
# ADR-008: the committed safety nucleus MUST match the AGENTS.md fenced span (CR-normalized).
$safetyNucleusGen = Join-NormalPath $root '.agentcortex/tools/generate_safety_nucleus.py'
if (Test-Path $safetyNucleusGen) {
    Invoke-PythonCheck -Label 'safety nucleus freshness' -MissingPythonLevel 'WARN' -ScriptPath $safetyNucleusGen -Arguments @('--check')
} else {
    Add-Result -Level 'SKIP' -Message 'safety nucleus freshness -- generator not deployed (safe to ignore)'
}
$phaseSkillFiles = @(
    (Join-NormalPath $workflowsDir 'plan.md'),
    (Join-NormalPath $workflowsDir 'implement.md'),
    (Join-NormalPath $workflowsDir 'review.md'),
    (Join-NormalPath $workflowsDir 'test.md'),
    (Join-NormalPath $workflowsDir 'handoff.md'),
    (Join-NormalPath $workflowsDir 'ship.md')
)
$phaseSkillErrors = 0
foreach ($file in $phaseSkillFiles) {
    if (-not (Test-Path -Path $file -PathType Leaf)) {
        Write-Output "  phase skill file not found: $file"
        $phaseSkillErrors++
        continue
    }
    $content = Get-Content -Raw -Encoding utf8 -Path $file
    if (-not $content.Contains('Recommended Skills')) {
        Write-Output "  missing Recommended Skills phase hook: $file"
        $phaseSkillErrors++
    }
}
if ($phaseSkillErrors -gt 0) {
    Add-Result -Level 'FAIL' -Message 'phase workflows missing Recommended Skills hooks'
}
else {
    Add-Result -Level 'PASS' -Message 'phase workflows include Recommended Skills hooks'
}
Test-ContainsLiteral -Path (Join-NormalPath $workflowsDir 'ship.md') -Pattern '## Ship Checklist' -SuccessMessage 'ship workflow includes mandatory ship checklist' -FailureMessage 'ship workflow missing mandatory ship checklist'
Test-ContainsLiteral -Path (Join-NormalPath $workflowsDir 'ship.md') -Pattern 'Active Work Log archived to `.agentcortex/context/archive/`' -SuccessMessage 'ship workflow checklist includes archive step' -FailureMessage 'ship workflow checklist missing archive step'

# Phase verification contract
$phaseVerifyFiles = @('plan.md','implement.md','review.md','test.md','handoff.md','ship.md')
$phaseVerifyErrors = 0
foreach ($pvf in $phaseVerifyFiles) {
    $pvPath = Join-NormalPath $workflowsDir $pvf
    if (Test-Path -Path $pvPath -PathType Leaf) {
        $pvContent = Get-Content -Path $pvPath -Raw -ErrorAction SilentlyContinue
        if ($pvContent -and ($pvContent -notmatch '(?i)Phase Verification')) {
            Write-Output "  missing Phase Verification section: $pvf"
            $phaseVerifyErrors++
        }
    }
}
if ($phaseVerifyErrors -gt 0) {
    Add-Result -Level 'FAIL' -Message 'phase workflows missing Phase Verification sections'
} else {
    Add-Result -Level 'PASS' -Message 'phase workflows include Phase Verification sections'
}

# Gate evidence contract
Test-ContainsLiteral -Path (Join-NormalPath $workflowsDir 'bootstrap.md') -Pattern '## Gate Evidence' -SuccessMessage 'bootstrap template includes Gate Evidence section' -FailureMessage 'bootstrap template missing Gate Evidence section'
Test-ContainsLiteral -Path (Join-NormalPath $workflowsDir 'app-init.md') -Pattern 'merge-safe retrofit guidance' -SuccessMessage 'app-init includes merge-safe docs retrofit guidance' -FailureMessage 'app-init missing merge-safe docs retrofit guidance'
Test-ContainsLiteral -Path (Join-NormalPath $workflowsDir 'bootstrap.md') -Pattern 'Partial adoption advisory' -SuccessMessage 'bootstrap includes bounded partial adoption advisory' -FailureMessage 'bootstrap missing bounded partial adoption advisory'
Test-ContainsLiteral -Path (Join-NormalPath $workflowsDir 'bootstrap.md') -Pattern 'status: living' -SuccessMessage 'bootstrap requires status: living before L1 authority reads' -FailureMessage 'bootstrap missing L1 status: living gate'
Test-ContainsLiteral -Path (Join-NormalPath $workflowsDir 'bootstrap.md') -Pattern 'BOTH `status: living` and `domain:`' -SuccessMessage 'bootstrap requires full L1 contract before authority reads' -FailureMessage 'bootstrap missing full L1 contract gate'
Test-ContainsLiteral -Path (Join-NormalPath $workflowsDir 'bootstrap.md') -Pattern 'External authority rule' -SuccessMessage 'bootstrap forces external specs through spec-intake' -FailureMessage 'bootstrap missing external authority routing rule'
Test-ContainsLiteral -Path (Join-NormalPath $workflowsDir 'bootstrap.md') -Pattern 'background context' -SuccessMessage 'bootstrap treats substantial background material as spec-intake input' -FailureMessage 'bootstrap missing substantial-background intake rule'
Test-ContainsLiteral -Path (Join-NormalPath $workflowsDir 'bootstrap.md') -Pattern 'Primary Domain Snapshot' -SuccessMessage 'bootstrap records primary_domain snapshot' -FailureMessage 'bootstrap missing primary_domain snapshot contract'
Test-ContainsLiteral -Path (Join-NormalPath $workflowsDir 'spec-intake.md') -Pattern 'Domain Doc L1 conflict check' -SuccessMessage 'spec-intake includes L1 conflict check for external specs' -FailureMessage 'spec-intake missing L1 conflict check for external specs'
Test-ContainsLiteral -Path (Join-NormalPath $workflowsDir 'ship.md') -Pattern 'structured `routing_actions` blocks' -SuccessMessage 'ship workflow scopes routing_actions to structured blocks' -FailureMessage 'ship workflow missing structured routing_actions wording'
Test-ContainsLiteral -Path (Join-NormalPath $workflowsDir 'ship.md') -Pattern 'Generic skip text is invalid' -SuccessMessage 'ship workflow hardens primary_domain skip justification' -FailureMessage 'ship workflow missing primary_domain skip-hardening wording'
Test-ContainsLiteral -Path (Join-NormalPath $workflowsDir 'ship.md') -Pattern 'Primary Domain Snapshot' -SuccessMessage 'ship workflow cross-checks bootstrap primary_domain snapshot' -FailureMessage 'ship workflow missing primary_domain snapshot cross-check'
Test-ContainsLiteral -Path (Join-NormalPath $workflowsDir 'ship.md') -Pattern 'Acceptable examples:' -SuccessMessage 'ship workflow gives acceptable skip examples' -FailureMessage 'ship workflow missing acceptable skip examples'
$docsReadmeTemplate = Join-NormalPath $root '.agentcortex/templates/docs-readme.md'
if (Test-Path -Path $docsReadmeTemplate -PathType Leaf) {
    Test-ContainsLiteral -Path $docsReadmeTemplate -Pattern '## Retrofit Note' -SuccessMessage 'docs README template includes retrofit note' -FailureMessage 'docs README template missing retrofit note'
}
else {
    Add-Result -Level 'SKIP' -Message 'docs README template retrofit note -- template not deployed'
}

$documentGovernanceSpecErrors = 0
$documentGovernancePartialWarn = 0
$domainDocFrontmatterWarn = 0
$specDir = Join-NormalPath $root 'docs/specs'
if (Test-Path -Path $specDir -PathType Container) {
    foreach ($spec in Get-ChildItem -Path $specDir -Filter *.md -File -ErrorAction SilentlyContinue) {
        $specContent = Get-Content -Path $spec.FullName -Raw -Encoding utf8
        if ($specContent -match '(?m)^primary_domain:\s*\S+') {
            if ($specContent -notmatch '(?m)^## Domain Decisions') {
                Write-Output "  spec with primary_domain missing Domain Decisions: $($spec.FullName)"
                $documentGovernanceSpecErrors++
            }
            if (-not (Test-Path -Path (Join-NormalPath $root 'docs/architecture') -PathType Container)) {
                Write-Output "  partial document-governance adoption: $($spec.FullName) declares primary_domain but docs/architecture/ is missing"
                $documentGovernancePartialWarn++
            }
        }
    }
}
if ($documentGovernanceSpecErrors -gt 0) {
    Add-Result -Level 'FAIL' -Message 'document-governance spec contract violations detected'
}
else {
    Add-Result -Level 'PASS' -Message 'document-governance specs preserve primary_domain and Domain Decisions contract'
}
if ($documentGovernancePartialWarn -gt 0) {
    Add-Result -Level 'WARN' -Message "partial document-governance adoption advisories detected: $documentGovernancePartialWarn"
}

$architectureDir = Join-NormalPath $root 'docs/architecture'
if (Test-Path -Path $architectureDir -PathType Container) {
    foreach ($domainDoc in Get-ChildItem -Path $architectureDir -Filter *.md -File -ErrorAction SilentlyContinue) {
        if ($domainDoc.Name -like '*.log.md') {
            continue
        }
        $domainDocContent = Get-NormalizedContent -Path $domainDoc.FullName
        if ($domainDocContent -notmatch '(?m)^status:\s*living$' -or $domainDocContent -notmatch '(?m)^domain:\s*\S+\s*$') {
            Write-Output "  domain doc candidate missing full L1 contract (status: living + domain:): $($domainDoc.FullName)"
            $domainDocFrontmatterWarn++
        }
    }
}
if ($domainDocFrontmatterWarn -gt 0) {
    Add-Result -Level 'WARN' -Message "legacy domain doc candidates were skipped as L1 authority (missing full L1 contract: status: living + domain:): $domainDocFrontmatterWarn. Do not add frontmatter directly; use /govern-docs when promoting them."
}
else {
    Add-Result -Level 'PASS' -Message 'domain doc candidates declare the full L1 contract when present'
}

$routingActionErrors = 0
$routingActionWarnings = 0
$reviewDir = Join-NormalPath $root 'docs/reviews'
if (Test-Path -Path $reviewDir -PathType Container) {
    foreach ($review in Get-ChildItem -Path $reviewDir -Filter *.md -File -ErrorAction SilentlyContinue) {
        $reviewContent = Get-Content -Path $review.FullName -Raw -Encoding utf8
        if ($reviewContent -match 'routing_actions:') {
            foreach ($required in @('finding:', 'target_doc:', 'status:', 'owner:')) {
                if ($reviewContent -notmatch [regex]::Escape($required)) {
                    Write-Output "  review snapshot missing routing_actions field $required`: $($review.FullName)"
                    $routingActionErrors++
                }
            }

            $targetMatches = [regex]::Matches($reviewContent, '(?m)^[ \t]*target_doc:\s*"?(?<path>[^"\r\n]+)"?\s*$')
            foreach ($match in $targetMatches) {
                $target = $match.Groups['path'].Value.Trim()
                if ($target -notmatch '^docs/(architecture|specs)/.+\.md$') {
                    Write-Output "  routing_actions target_doc must point to docs/architecture/*.md or docs/specs/*.md: $($review.FullName) ($target)"
                    $routingActionErrors++
                }
                elseif (-not (Test-Path -Path (Join-NormalPath $root $target) -PathType Leaf)) {
                    Write-Output "  routing_actions target_doc does not exist yet: $($review.FullName) ($target)"
                    $routingActionWarnings++
                }
            }

            $statusMatches = [regex]::Matches($reviewContent, '(?m)^[ \t]*status:\s*(?<status>[a-z]+)\s*$')
            foreach ($match in $statusMatches) {
                $status = $match.Groups['status'].Value.Trim()
                if ($status -notin @('pending', 'merged', 'rejected')) {
                    Write-Output "  routing_actions status must be pending, merged, or rejected: $($review.FullName) ($status)"
                    $routingActionErrors++
                }
            }
        }
    }
}
if ($routingActionErrors -gt 0) {
    Add-Result -Level 'FAIL' -Message 'routing_actions contract violations detected'
}
else {
    Add-Result -Level 'PASS' -Message 'routing_actions contract is structurally valid when present'
}
if ($routingActionWarnings -gt 0) {
    Add-Result -Level 'WARN' -Message "routing_actions target docs need follow-up: $routingActionWarnings"
}

Test-ContainsLiteral -Path $canonicalDeploySh -Pattern 'LEGACY_IGNORE_START="# AI Brain OS - Agent System & Local Context"' -SuccessMessage 'deploy script supports legacy ignore marker migration' -FailureMessage 'deploy script missing legacy ignore marker support'
Test-ContainsLiteral -Path $canonicalDeploySh -Pattern 'strip_managed_ignore_blocks() {' -SuccessMessage 'deploy script includes managed ignore block replacement helper' -FailureMessage 'deploy script missing managed ignore replacement helper'
Test-ContainsLiteral -Path $canonicalDeploySh -Pattern '.agentcortex/bin/' -SuccessMessage 'deploy script targets canonical .agentcortex/bin namespace' -FailureMessage 'deploy script missing canonical namespace deployment path'

$deployBlock = New-Object System.Collections.Generic.List[string]
$capturing = $false
foreach ($line in Get-Content -Path $canonicalDeploySh) {
    if ($line -eq '# Agentic OS Template - Downstream Ignore Defaults') { $capturing = $true }
    if ($capturing) { $deployBlock.Add($line) }
    if ($capturing -and $line -eq '# End Agentic OS Template - Downstream Ignore Defaults') { break }
}
if ($deployBlock.Count -eq 0) {
    Add-Result -Level 'FAIL' -Message 'deploy ignore block missing from deploy script'
}
else {
    $deployBlockErrors = 0
    foreach ($pattern in @(
        '# Agentic OS Template - Downstream Ignore Defaults',
        '.agentcortex/context/work/*.md',
        '.agentcortex/context/private/',
        '.agentcortex/context/.guard_receipt.json',
        '.agentcortex/context/.guard_locks/',
        '.agent/private/',
        '.agentcortex-src/',
        '*.acx-incoming',
        '.openrouter/',
        '.claude-chat/',
        '.cursor/',
        '.antigravity/scratch/',
        '# End Agentic OS Template - Downstream Ignore Defaults'
    )) {
        if ($deployBlock -notcontains $pattern) {
            Write-Output "  deploy ignore block missing required pattern: $pattern"
            $deployBlockErrors++
        }
    }
    if (-not ($deployBlock | Where-Object { $_ -eq '!.agentcortex/context/work/.gitkeep.md' })) {
        Write-Output '  deploy ignore block missing .gitkeep.md negation pattern'
        $deployBlockErrors++
    }
    foreach ($forbidden in @(
        '.agentcortex/context/current_state.md',
        '.agentcortex/context/archive/',
        'deploy_brain.sh',
        'deploy_brain.ps1',
        'deploy_brain.cmd',
        '.agentcortex-manifest'
    )) {
        if ($deployBlock -contains $forbidden) {
            Write-Output "  deploy ignore block must not include tracked file: $forbidden"
            $deployBlockErrors++
        }
    }
    if ($deployBlockErrors -gt 0) {
        Add-Result -Level 'FAIL' -Message 'deploy ignore block contents are invalid'
    }
    else {
        Add-Result -Level 'PASS' -Message 'deploy ignore block contents are valid'
    }
}

if ($isSourceRepo) {
    $readmeZhTw = Join-NormalPath $root 'docs/README_zh-TW.md'
    if (Test-Path -Path $readmeZhTw -PathType Leaf) {
        Test-ContainsLiteral -Path $readmeZhTw -Pattern '用工作流程、交付閘門與工程護欄' -SuccessMessage 'README_zh-TW.md encoding looks healthy' -FailureMessage 'README_zh-TW.md appears mojibaked or re-encoded'
    }
    $readmeEn = Join-NormalPath $root 'README.md'
    if (Test-Path -Path $readmeEn -PathType Leaf) {
        $params = @{
            Path = $readmeEn
            Pattern = 'governance-first layer for AI coding agents'
            SuccessMessage = 'README.md encoding looks healthy'
            FailureMessage = 'README.md appears mojibaked or re-encoded'
        }
        Test-ContainsLiteral @params
    }
}

$testingProtocolZhTw = Join-NormalPath $root '.agentcortex/docs/TESTING_PROTOCOL_zh-TW.md'
if (Test-Path -Path $testingProtocolZhTw -PathType Leaf) {
    Test-ContainsLiteral -Path $testingProtocolZhTw -Pattern '測試教戰守則' -SuccessMessage 'TESTING_PROTOCOL_zh-TW.md encoding looks healthy' -FailureMessage 'TESTING_PROTOCOL_zh-TW.md appears mojibaked or re-encoded'
}

$auditGuardrailsEn = Join-NormalPath $root '.agentcortex/docs/guides/audit-guardrails.md'
if (Test-Path -Path $auditGuardrailsEn -PathType Leaf) {
    $params = @{
        Path = $auditGuardrailsEn
        Pattern = 'Test 1: Invisible Assistant Check (.gitignore Automation)'
        SuccessMessage = 'audit-guardrails.md encoding looks healthy'
        FailureMessage = 'audit-guardrails.md appears mojibaked or re-encoded'
    }
    Test-ContainsLiteral @params
}

$auditGuardrailsZhTw = Join-NormalPath $root '.agentcortex/docs/guides/audit-guardrails_zh-TW.md'
if (Test-Path -Path $auditGuardrailsZhTw -PathType Leaf) {
    Test-ContainsLiteral -Path $auditGuardrailsZhTw -Pattern '為什麼不寫成自動化 Shell Script？' -SuccessMessage 'audit-guardrails_zh-TW.md encoding looks healthy' -FailureMessage 'audit-guardrails_zh-TW.md appears mojibaked or re-encoded'
}

$worklogMaxLines = if ($env:WORKLOG_MAX_LINES) { [int]$env:WORKLOG_MAX_LINES } else { 300 }
$worklogMaxKb = if ($env:WORKLOG_MAX_KB) { [int]$env:WORKLOG_MAX_KB } else { 12 }
$activeWorklogWarnThreshold = if ($env:ACTIVE_WORKLOG_WARN_THRESHOLD) { [int]$env:ACTIVE_WORKLOG_WARN_THRESHOLD } else { 8 }
$activeWorklogFailThreshold = if ($env:ACTIVE_WORKLOG_FAIL_THRESHOLD) { [int]$env:ACTIVE_WORKLOG_FAIL_THRESHOLD } else { 12 }
$archiveSizeWarnKb = if ($env:ARCHIVE_SIZE_WARN_KB) { [int]$env:ARCHIVE_SIZE_WARN_KB } else { 10240 }
$legacyGateEvidenceCutoff = if ($env:WORKLOG_GATE_EVIDENCE_LEGACY_CUTOFF) { $env:WORKLOG_GATE_EVIDENCE_LEGACY_CUTOFF } else { '2026-03-25' }
$worklogDir = Join-NormalPath $root '.agentcortex/context/work'
if (Test-Path -Path $worklogDir -PathType Container) {
    $worklogs = @(Get-ChildItem -Path $worklogDir -Filter *.md -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -notlike '.*' })
    $oversizedLogs = @()
    foreach ($wl in $worklogs) {
        $lineCount = @(Get-Content -Path $wl.FullName).Count
        $kb = [math]::Floor($wl.Length / 1024)
        if ($lineCount -gt $worklogMaxLines -or $kb -gt $worklogMaxKb) {
            Write-Output "  work log needs compaction: $($wl.Name) ($lineCount lines, ${kb}KB)"
            $oversizedLogs += $wl
        }
    }
    if ($oversizedLogs.Count -gt 0) {
        Add-Result -Level 'FAIL' -Message 'work log compaction warnings detected'
    }
    else {
        Add-Result -Level 'PASS' -Message 'active work log sizes are within compaction thresholds'
    }

    if ($worklogs.Count -gt $activeWorklogFailThreshold) {
        Add-Result -Level 'WARN' -Message "active work log count over hygiene hard-limit ($($worklogs.Count) > $activeWorklogFailThreshold); archive completed branches via /handoff or rm — advisory only (work logs are gitignored, CI-invisible)"
    }
    elseif ($worklogs.Count -gt $activeWorklogWarnThreshold) {
        Add-Result -Level 'WARN' -Message "active work log count exceeds hygiene threshold ($($worklogs.Count) > $activeWorklogWarnThreshold; hard limit $activeWorklogFailThreshold)"
    }
    else {
        Add-Result -Level 'PASS' -Message 'active work log count is within hygiene threshold'
    }
    # Archive directory size — surface unbounded growth before ingestion hazard. WARN-only.
    $archiveDir = Join-NormalPath $root '.agentcortex/context/archive'
    if ((Test-Path -Path $archiveDir -PathType Container) -and ($archiveSizeWarnKb -gt 0)) {
        # Under Set-StrictMode -Version Latest, an empty pipeline through Measure-Object
        # yields an object whose Sum property strict-mode treats as missing — guard via
        # explicit array materialization so empty archives report 0 KB cleanly.
        $archiveFiles = @(Get-ChildItem -Path $archiveDir -Recurse -File -ErrorAction SilentlyContinue)
        if ($archiveFiles.Count -gt 0) {
            $archiveKb = [int](($archiveFiles | Measure-Object -Property Length -Sum).Sum / 1024)
        }
        else {
            $archiveKb = 0
        }
        if ($archiveKb -gt $archiveSizeWarnKb) {
            Add-Result -Level 'WARN' -Message "archive size ${archiveKb}KB exceeds threshold ${archiveSizeWarnKb}KB; consider /retro-driven cold-tier rotation"
        }
        else {
            Add-Result -Level 'PASS' -Message "archive size within threshold (${archiveKb}KB / ${archiveSizeWarnKb}KB)"
        }
    }
    # Work Log integrity marker check — detect truncated writes from interrupted sessions
    $worklogTruncated = 0
    foreach ($wl in $worklogs) {
        $wlContent = Get-Content -Path $wl.FullName -Raw -ErrorAction SilentlyContinue
        if (-not $wlContent) { continue }
        # A well-formed work log must have at least a Branch header and one ## section.
        # Accept list form ("- Branch:" or "- **Branch**:") AND table form
        # ("| Branch | ... |") — the canonical template uses a table for readability.
        $hasBranchHeader = $wlContent -match '(?m)(^- (\*\*Branch\*\*|Branch):|^\| (\*\*Branch\*\*|Branch) +\|)'
        $hasSectionHeader = $wlContent -match '(?m)^## '
        if (-not $hasBranchHeader -or -not $hasSectionHeader) {
            Write-Output "  possibly truncated work log: $($wl.Name)"
            $worklogTruncated++
        }
    }
    if ($worklogTruncated -gt 0) {
        Add-Result -Level 'WARN' -Message "possibly truncated work logs detected: $worklogTruncated"
    }
    else {
        Add-Result -Level 'PASS' -Message 'active work logs pass structural integrity check'
    }
    # Work Log evidence chain check (per AGENTS.md Work Log Contract)
    $phaseFieldMissing = 0
    $checkpointMissing = 0
    $gateEvidenceMissing = 0
    $legacyGateEvidenceMissing = 0
    $gateProgressionIllegal = 0
    $phaseSummaryMissing = 0
    $sentinelMarkerMissing = 0
    $testGateResultsMissing = 0
    $currentPhaseIncoherent = 0
    $shippedNotArchived = 0
    $evidencePlaceholderOnly = 0
    $reviewPassWithUnproven = 0
    $reclassifyHeaderNotReset = 0
    $handoffResumeIncomplete = 0
    $hotfixShipNoEvidence = 0
    $adrCoverageUndocumented = 0
    # Legal phase transitions for gate evidence validation (classification-aware)
    # quick-win / unknown: implement can go directly to ship (fast path)
    $legalDefault = @{
        'bootstrap' = @('plan')
        'plan'      = @('implement')
        'implement' = @('review','test','ship')
        'review'    = @('implement','test','ship')
        'test'      = @('ship','implement')
        'handoff'   = @('ship','retro')
        'ship'      = @()
    }
    # feature / architecture-change: must go through review+test+handoff; no shortcuts
    $legalStrict = @{
        'bootstrap' = @('plan')
        'plan'      = @('implement')
        'implement' = @('review','test')
        'review'    = @('implement','test')
        'test'      = @('handoff','implement')
        'handoff'   = @('ship','retro')
        'ship'      = @()
    }
    # hotfix: must review+test but handoff is optional (goes test->ship directly)
    # plan is always required per engineering_guardrails.md §10.2 — no implement shortcut
    $legalHotfix = @{
        'bootstrap' = @('plan')
        'plan'      = @('implement')
        'implement' = @('review','test')
        'review'    = @('implement','test')
        'test'      = @('ship','implement')
        'ship'      = @()
    }
    foreach ($wl in $worklogs) {
        $content = Get-Content -Path $wl.FullName -Raw -Encoding utf8 -ErrorAction SilentlyContinue
        if (-not $content) { continue }
        # Select legal-transition dict based on classification (accept list and table form)
        $wlClassForGates = ''
        $wlClassForGatesMatch = [regex]::Match($content, '(?m)^-\s+(?:\*\*)?[Cc]lassification(?:\*\*)?\s*:\s+`?([a-zA-Z][\w-]*)`?')
        if (-not $wlClassForGatesMatch.Success) {
            $wlClassForGatesMatch = [regex]::Match($content, '(?m)^\|\s*(?:\*\*)?[Cc]lassification(?:\*\*)?\s*\|\s*`?([a-zA-Z][\w-]*)')
        }
        if ($wlClassForGatesMatch.Success) { $wlClassForGates = $wlClassForGatesMatch.Groups[1].Value.ToLower() }
        $legalTransitions = if ($wlClassForGates -in @('feature','architecture-change')) { $legalStrict }
                            elseif ($wlClassForGates -eq 'hotfix') { $legalHotfix }
                            elseif ($wlClassForGates -in @('quick-win','tiny-fix')) { $legalDefault }
                            else { $legalStrict }  # H1 fail-closed: unknown → strictest transitions
        $createdDate = ''
        $createdDateMatch = [regex]::Match($content, '(?m)^- \*\*Created Date\*\*:\s*(.+)$')
        if ($createdDateMatch.Success) {
            $createdDate = $createdDateMatch.Groups[1].Value.Trim()
        }
        $isLegacyGateEvidenceLog = $createdDate -and $createdDate -lt $legacyGateEvidenceCutoff
        # Accept list or table form for header fields (see .agentcortex/templates/worklog.md)
        if ($content -notmatch '(?m)(^- (`Current Phase`|Current Phase):|^\| (`Current Phase`|Current Phase) +\|)') { $phaseFieldMissing++ }
        if ($content -notmatch '(?m)(^- (`Checkpoint SHA`|Checkpoint SHA):|^\| (`Checkpoint SHA`|Checkpoint SHA) +\|)') { $checkpointMissing++ }
        if ($content -notmatch '(?m)^## Gate Evidence') {
            if ($isLegacyGateEvidenceLog) {
                $legacyGateEvidenceMissing++
            } else {
                $gateEvidenceMissing++
            }
        } elseif ($content -notmatch '(?mi)^(`?- )?gate:.*verdict:') {
            if ($isLegacyGateEvidenceLog) {
                $legacyGateEvidenceMissing++
            } else {
                $gateEvidenceMissing++
            }
        } else {
            # Parse gate receipts: only PASS verdicts are forward transitions;
            # NOT READY / FAIL receipts are reverse edges and must be excluded.
            # supporting workflows are out-of-band — exclude to avoid false illegal-transition flags.
            # H4: count STRUCTURED reclassification records in Drift Log (count-based, not position-based)
            # Requires: Reclassif* <sep> ... -> — rejects prose mentions like "considered but rejected"
            $reclassifyCount = 0
            $inDrift = $false
            foreach ($line in ($content -split "\r?\n")) {
                if ($line -match '^## Drift Log') { $inDrift = $true; continue }
                if ($inDrift -and $line -match '^## ') { break }
                if ($inDrift) {
                    $rm = [regex]::Match($line, '\bReclassif\w*\s*[:\-]\s*([\w-]+)\s*->\s*([\w-]+)')
                    if ($rm.Success -and $rm.Groups[1].Value.ToLower() -ne $rm.Groups[2].Value.ToLower()) { $reclassifyCount++ }
                }
            }
            $resetsUsed = 0
            # T48/T154/T175/T178/T241/T181/T242/T243: section-scoped gate parsing with full
            # fence/comment injection protection. T244: tracking runs on EVERY line.
            # T247: masked receipt tracking in main loop (replaces post-loop raw-rescan
            # which had false-positives on lone-## inside fences and multiple-section
            # ambiguity, and false-negatives on indented receipts inside fences).
            $receiptRe = '(?i)^(?:`?- )?gate:\s*\w+\s*\|'
            # Inside fences lines may be indented; allow leading whitespace for masked-receipt detection
            $maskedReceiptRe = '(?i)^\s*(?:`?- )?gate:\s*\w+\s*\|'
            $inGateEvidenceSection = $false
            $gateEvidenceSeen = $false
            $maskedReceiptInSection = $false  # T247
            $inCodeFence = $false
            $inHtmlComment = $false
            $gateLines = [System.Collections.Generic.List[string]]::new()
            foreach ($line in ($content -split "\r?\n")) {
                $wasInFence = $inCodeFence
                if ($line -match '^ {0,3}(`{3,}|~{3,})') { $inCodeFence = -not $inCodeFence }
                $wasInComment = $inHtmlComment
                foreach ($cm in [regex]::Matches($line, '<!--|-->')) { $inHtmlComment = ($cm.Value -eq '<!--') }
                $masked = ($wasInFence -or $inCodeFence) -or ($wasInComment -or $inHtmlComment)
                if ($line -match '^## Gate Evidence' -and -not $gateEvidenceSeen -and -not $inCodeFence -and -not $inHtmlComment) { $inGateEvidenceSection = $true; $gateEvidenceSeen = $true; continue }
                if ($inGateEvidenceSection -and $line -match '^## ' -and -not $masked) { $inGateEvidenceSection = $false; continue }
                if ($inGateEvidenceSection) {
                    if ($masked) {
                        if ($line -match $maskedReceiptRe) { $maskedReceiptInSection = $true }
                    } else {
                        $gateLines.Add($line)
                    }
                }
            }
            # T243: fail-closed if heading exists but was suppressed (fence/comment blocked recognition)
            if (-not $gateEvidenceSeen) {
                if (($content -split "\r?\n") | Where-Object { $_ -match '^## Gate Evidence' }) {
                    Write-Output 'incomplete:gate-evidence-suppressed (unclosed fence or HTML comment above ## Gate Evidence -- validate manually)'
                    $gateProgressionIllegal++; continue
                }
            }
            # T245: fail-closed if fence/comment left unclosed INSIDE Gate Evidence
            if ($inCodeFence -or $inHtmlComment) {
                Write-Output 'incomplete:unterminated-fence-or-comment (unclosed code fence or HTML comment in ## Gate Evidence -- validate manually)'
                $gateProgressionIllegal++; continue
            }
            # T247: no unmasked receipt but at least one was masked — targeted error
            $unmaskedReceipt = $gateLines | Where-Object { $_ -match $receiptRe } | Select-Object -First 1
            if ($gateEvidenceSeen -and -not $unmaskedReceipt -and $maskedReceiptInSection) {
                Write-Output 'incomplete:receipts-in-fence (Gate Evidence has receipt-format lines but all are inside code fences or HTML comments -- move receipts out of code blocks)'
                $gateProgressionIllegal++; continue
            }
            $gateList = [System.Collections.Generic.List[string]]::new()
            $hasShipReceipt = $false  # H3: track ANY ship receipt regardless of verdict
            $reviewNotReady = $false  # track pending re-review after NOT READY reverse edge
            foreach ($line in $gateLines) {
                $gm = [regex]::Match($line, '(?i)^(?:`?- )?gate:\s*(\w+)\s*\|')
                if ($gm.Success) {
                    $gPhase = $gm.Groups[1].Value.ToLower()
                    # H3: record ship presence BEFORE verdict filter
                    if ($gPhase -eq 'ship') { $hasShipReceipt = $true }
                    # supporting workflows are out-of-band
                    if ($gPhase -in @('retro','research','brainstorm','decide','audit')) { continue }
                    if ($line -match '(?i)\|[^|]*Verdict:\s*PASS(\s*\||$)') {
                        # PASS: clear pending re-review flag if this is review
                        if ($gPhase -eq 'review') { $reviewNotReady = $false }
                        # H4: Reclassification reset — one reset per structured drift record
                        if ($gPhase -eq 'bootstrap' -and $gateList.Count -gt 0 -and $reclassifyCount -gt $resetsUsed) {
                            $gateList.Clear()
                            $resetsUsed++
                        }
                        $gateList.Add($gPhase)
                    } else {
                        # NOT READY / FAIL review: discard preceding implement (reverse-edge pop)
                        if ($gPhase -eq 'review' -and $gateList.Count -gt 0 -and $gateList[$gateList.Count - 1] -eq 'implement') {
                            $gateList.RemoveAt($gateList.Count - 1)
                            $reviewNotReady = $true
                        }
                    }
                }
            }
            $gates = @($gateList)
            # Completeness check first — valid even with 1 gate (avoids early-return bypass)
            $gateSet = @{}
            foreach ($g in $gates) { $gateSet[$g] = $true }
            # H3: completeness triggers on ANY ship receipt, not just PASS ones
            if ($hasShipReceipt -or $gateSet.ContainsKey('ship')) {
                if ($wlClassForGates -in @('feature','architecture-change')) {
                    $requiredPhases = @('bootstrap','plan','implement','review','test','handoff')
                } elseif ($wlClassForGates -eq 'hotfix') {
                    $requiredPhases = @('bootstrap','plan','implement','review','test')
                } elseif ($wlClassForGates -eq 'quick-win') {
                    # H1: quick-win has real required phases — not an empty set
                    $requiredPhases = @('bootstrap','plan','implement')
                } elseif ($wlClassForGates -eq 'tiny-fix') {
                    # tiny-fix is exempt from gate ceremony (AGENTS.md §tiny-fix fast path)
                    $requiredPhases = @()
                } else {
                    # H1: fail-closed for unknown/misspelled classification — treat as feature
                    $requiredPhases = @('bootstrap','plan','implement','review','test','handoff')
                }
                $missingPhases = $requiredPhases | Where-Object { -not $gateSet.ContainsKey($_) }
                if ($missingPhases) {
                    Write-Output "  incomplete gate receipts in $($wl.Name): missing $($missingPhases -join ',')"
                    $gateProgressionIllegal++
                }
            }
            # NOT READY reverse-edge check: re-review was skipped after NOT READY
            if ($reviewNotReady -and ($gates | Where-Object { $_ -in @('test','handoff','ship') })) {
                $badNext = ($gates | Where-Object { $_ -in @('test','handoff','ship') } | Select-Object -First 1)
                Write-Output "  illegal gate progression in $($wl.Name): NOT_READY-review->$badNext (re-review skipped after NOT READY)"
                $gateProgressionIllegal++
            }
            # Progression check requires 2+ gates; tiny-fix has no required phase sequence
            if ($gates.Count -ge 2 -and $wlClassForGates -ne 'tiny-fix') {
                for ($i = 1; $i -lt $gates.Count; $i++) {
                    $prev = $gates[$i - 1]
                    $curr = $gates[$i]
                    $allowed = $legalTransitions[$prev]
                    if (($null -ne $allowed) -and ($curr -notin $allowed)) {
                        Write-Output "  illegal gate progression in $($wl.Name): ${prev}->${curr}"
                        $gateProgressionIllegal++
                        break
                    }
                }
            }
            # M10: stale-review — if most recent implement follows most recent review,
            # test/handoff/ship without re-review = governance gap (test.md §reverse-edge)
            # quick-win and tiny-fix treat review as optional — no re-review required.
            # Unknown/H1 fail-closed classifications follow feature rules, so M10 applies.
            if ($wlClassForGates -notin @('quick-win','tiny-fix')) {
                $lastReviewIdx = -1
                $lastImplIdx   = -1
                for ($i = 0; $i -lt $gates.Count; $i++) {
                    if ($gates[$i] -eq 'review')    { $lastReviewIdx = $i }
                    if ($gates[$i] -eq 'implement') { $lastImplIdx   = $i }
                }
                if ($lastReviewIdx -ge 0 -and $lastImplIdx -gt $lastReviewIdx) {
                    $postImpl = if ($lastImplIdx + 1 -lt $gates.Count) { $gates[($lastImplIdx + 1)..($gates.Count - 1)] } else { @() }
                    $badNext = $postImpl | Where-Object { $_ -in @('test','handoff','ship') } | Select-Object -First 1
                    if ($badNext) {
                        Write-Output "  illegal gate progression in $($wl.Name): implement-after-review->$badNext (stale review — re-review required)"
                        $gateProgressionIllegal++
                    }
                }
            }
        }
        if ($content -notmatch '(?m)^## Phase Summary') { $phaseSummaryMissing++ }
        # Sentinel marker discoverability — Work Log Phase Summary SHOULD carry
        # ⚡ ACX (or plain ACX) at least once for AGENTS.md Sentinel Check audit.
        # WARN-only — skip if Phase Summary itself is missing.
        if (($content -match '(?m)^## Phase Summary') `
            -and ($content -notmatch '(⚡\s?ACX|\sACX(\s|$))')) {
            $sentinelMarkerMissing++
        }
        # Test Gate Results — engineering_guardrails.md §12.2 requires evidence under
        # "Test Gate Results" for feature/architecture-change logs that reached implement.
        $wlClass = ''
        if ($content -match '(?m)^- \*?\*?Classification\*?\*?:\s*(.+?)\s*$') { $wlClass = $Matches[1].Trim() -replace '`', '' }
        if ([string]::IsNullOrEmpty($wlClass)) {
            if ($content -match '(?m)^\|\s*(?:\*\*)?[Cc]lassification(?:\*\*)?\s*\|\s*`?([a-zA-Z][\w-]*)') { $wlClass = $Matches[1].Trim() }
        }
        if (($wlClass -eq 'feature' -or $wlClass -eq 'architecture-change') `
            -and ($content -match '(?i)Gate:\s*implement') `
            -and ($content -notmatch '(?im)^#+\s+Test Gate Results')) {
            $testGateResultsMissing++
        }
        # MEDIUM-1 (review PASS with UNPROVEN rows)
        if ($content -match '(?i)Gate:\s*review\s*\|[^|\r\n]*Verdict:\s*PASS') {
            $unprovenLines = [regex]::Matches($content, '✗ UNPROVEN') | Where-Object { $_.Value -and ($content.Substring([Math]::Max(0,$_.Index-200), [Math]::Min(200,$_.Index)) + $content.Substring($_.Index, [Math]::Min(100,$content.Length-$_.Index))) -notmatch '\[NEEDS_HUMAN\]' }
            # Simpler: flag if any line has UNPROVEN but not NEEDS_HUMAN
            $unprovenUntagged = ($content -split "`n") | Where-Object { $_ -match '✗ UNPROVEN' -and $_ -notmatch '\[NEEDS_HUMAN\]' }
            if ($unprovenUntagged) { $reviewPassWithUnproven++ }
        }
        # Current Phase consistency (HIGH-2): if ship PASS receipt exists, Current Phase should be 'ship'
        if ($content -match '(?i)Gate:\s*ship\s*\|[^|\r\n]*Verdict:\s*PASS') {
            $cpM = [regex]::Match($content, '(?m)^-\s+\*?\*?Current Phase\*?\*?:\s*`?(\w[\w-]*)')
            if (-not $cpM.Success) { $cpM = [regex]::Match($content, '(?m)^\|\s*\*?\*?Current Phase\*?\*?\s*\|\s*`?(\w[\w-]*)') }
            if ($cpM.Success -and $cpM.Groups[1].Value.ToLower() -ne 'ship') { $currentPhaseIncoherent++ }
            # Archival check (Item 1): shipped log in active work/ means /ship step 3 (archival) was skipped
            if (-not $cpM.Success -or $cpM.Groups[1].Value.ToLower() -eq 'ship') { $shippedNotArchived++ }
            # MEDIUM-3 (M5): evidence non-empty check for shipped feature/arch-change/quick-win
            if ($wlClass -in @('feature','architecture-change','quick-win')) {
                $evidenceMatch = [regex]::Match($content, '(?ms)^## Evidence\r?\n(.*?)(?=^## |\z)')
                $evidenceBody = if ($evidenceMatch.Success) { $evidenceMatch.Groups[1].Value.Trim() } else { '' }
                if ([string]::IsNullOrWhiteSpace($evidenceBody) -or $evidenceBody -match 'Pending:\s*bootstrap only') {
                    $evidencePlaceholderOnly++
                }
            }
        }
        # Finding 9 (HIGH): Reclassification state inconsistency — Drift Log records
        # "Reclassification:" but Classification header was never reset to CLASSIFIED.
        if ($content -match '(?m)^## Drift Log' -and $content -match '(?im)^\s*-\s+Reclassif') {
            $clsHdrM = [regex]::Match($content, '(?m)^-\s*\*{0,2}Classification\*{0,2}\s*:\s*`?([A-Za-z][\w-]*)')
            if ($clsHdrM.Success -and $clsHdrM.Groups[1].Value.ToLower() -ne 'classified') {
                $reclassifyHeaderNotReset++
            }
        }
        # Finding 5 (MEDIUM): Handoff Resume Block completeness — warn when ## Resume
        # section exists but is missing required sub-sections (handoff.md §1a).
        if ($content -match '(?m)^## Resume') {
            $resumeM = [regex]::Match($content, '(?ms)^## Resume\r?\n(.*?)(?=^## |\z)')
            $resumeBody = if ($resumeM.Success) { $resumeM.Groups[1].Value } else { '' }
            $missingSubsections = 0
            foreach ($subsec in @('Read Map', 'Skip List', 'Context Snapshot')) {
                if ($resumeBody -notmatch "(?im)^###\s+$subsec") { $missingSubsections++ }
            }
            if ($missingSubsections -gt 0) { $handoffResumeIncomplete++ }
        }
        # Finding 13 (MEDIUM): hotfix fast-path evidence check — hotfix is exempt from
        # /handoff but MUST provide evidence per handoff.md §Trigger Conditions.
        if ($wlClass -eq 'hotfix' -and ($content -match '(?i)Gate:\s*ship\s*\|.*Verdict:\s*PASS')) {
            $hotfixEvidM = [regex]::Match($content, '(?ms)^## Evidence\r?\n(.*?)(?=^## |\z)')
            $hotfixEvid = if ($hotfixEvidM.Success) { $hotfixEvidM.Groups[1].Value.Trim() } else { '' }
            if ([string]::IsNullOrWhiteSpace($hotfixEvid) -or $hotfixEvid -match 'Pending:\s*bootstrap only') {
                $hotfixShipNoEvidence++
            }
        }
        # Finding 14 (MEDIUM): ADR Coverage gap — for feature/arch-change past plan phase,
        # bootstrap should have logged ADR Coverage Check result in ## Drift Log.
        if (($wlClass -eq 'feature' -or $wlClass -eq 'architecture-change') -and
            ($content -match '(?i)Gate:\s*(plan|implement)\s*\|')) {
            if ($content -notmatch '(?i)(ADR.*[Cc]overage|[Cc]overage.*ADR|adr.*check|no.*adr.*found)') {
                $adrCoverageUndocumented++
            }
        }
    }
    if ($phaseFieldMissing -gt 0) {
        Add-Result -Level 'WARN' -Message "work logs missing Current Phase field: $phaseFieldMissing"
    } elseif ($worklogs.Count -gt 0) {
        Add-Result -Level 'PASS' -Message 'all active work logs have Current Phase field'
    }
    if ($checkpointMissing -gt 0) {
        Add-Result -Level 'WARN' -Message "work logs missing Checkpoint SHA field: $checkpointMissing"
    } elseif ($worklogs.Count -gt 0) {
        Add-Result -Level 'PASS' -Message 'all active work logs have Checkpoint SHA field'
    }
    if ($gateEvidenceMissing -gt 0) {
        Add-Result -Level 'FAIL' -Message "work logs missing gate evidence receipts: $gateEvidenceMissing"
    } elseif ($worklogs.Count -gt 0 -and $legacyGateEvidenceMissing -eq 0) {
        Add-Result -Level 'PASS' -Message 'all active work logs have gate evidence receipts'
    }
    if ($legacyGateEvidenceMissing -gt 0) {
        Add-Result -Level 'WARN' -Message "legacy work logs missing gate evidence receipts: $legacyGateEvidenceMissing (created before $legacyGateEvidenceCutoff)"
    }
    if ($gateProgressionIllegal -gt 0) {
        Add-Result -Level 'FAIL' -Message "work logs with illegal gate phase progression: $gateProgressionIllegal"
    } elseif ($worklogs.Count -gt 0 -and $gateEvidenceMissing -eq 0 -and $legacyGateEvidenceMissing -eq 0) {
        Add-Result -Level 'PASS' -Message 'gate evidence phase progression is legal'
    }
    if ($phaseSummaryMissing -gt 0) {
        Add-Result -Level 'WARN' -Message "work logs missing Phase Summary section: $phaseSummaryMissing"
    } elseif ($worklogs.Count -gt 0) {
        Add-Result -Level 'PASS' -Message 'all active work logs have Phase Summary section'
    }
    if ($sentinelMarkerMissing -gt 0) {
        Add-Result -Level 'WARN' -Message "work logs missing sentinel marker (ACX) in Phase Summary: $sentinelMarkerMissing"
    } elseif ($worklogs.Count -gt 0 -and $phaseSummaryMissing -eq 0) {
        Add-Result -Level 'PASS' -Message 'all active work logs carry sentinel marker for audit trail'
    }
    if ($testGateResultsMissing -gt 0) {
        Add-Result -Level 'WARN' -Message "feature/architecture-change work logs missing Test Gate Results section (engineering_guardrails.md §12.2): $testGateResultsMissing"
    } elseif ($worklogs.Count -gt 0) {
        Add-Result -Level 'PASS' -Message 'test gate results evidence present in applicable work logs'
    }
    if ($currentPhaseIncoherent -gt 0) {
        Add-Result -Level 'WARN' -Message "work logs with ship PASS receipt but Current Phase != ship (header not updated): $currentPhaseIncoherent"
    } elseif ($worklogs.Count -gt 0) {
        Add-Result -Level 'PASS' -Message 'Current Phase field is consistent with last gate receipt in all work logs'
    }
    if ($shippedNotArchived -gt 0) {
        Add-Result -Level 'WARN' -Message "shipped work logs still in active work/ directory (archival incomplete — /ship step 3 skipped?): $shippedNotArchived"
    } elseif ($worklogs.Count -gt 0) {
        Add-Result -Level 'PASS' -Message 'no shipped work logs found in active work/ directory'
    }
    if ($evidencePlaceholderOnly -gt 0) {
        Add-Result -Level 'FAIL' -Message "feature/arch-change/quick-win shipped work logs with bootstrap-placeholder ## Evidence (NO EVIDENCE = NO SHIP per AGENTS.md §Delivery Gates): $evidencePlaceholderOnly"
    } elseif ($worklogs.Count -gt 0) {
        Add-Result -Level 'PASS' -Message 'shipped feature/arch-change/quick-win work logs have non-placeholder Evidence sections'
    }
    if ($reviewPassWithUnproven -gt 0) {
        Add-Result -Level 'WARN' -Message "work logs with review PASS receipt but unresolved UNPROVEN rows (should be NOT READY per review.md §Burden of Proof): $reviewPassWithUnproven"
    } elseif ($worklogs.Count -gt 0) {
        Add-Result -Level 'PASS' -Message 'no review PASS receipts with unresolved UNPROVEN rows detected'
    }
    if ($reclassifyHeaderNotReset -gt 0) {
        Add-Result -Level 'WARN' -Message "work logs with Reclassification in Drift Log but Classification header not reset to CLASSIFIED (implement.md §Mid-Execution Guard step c incomplete): $reclassifyHeaderNotReset"
    } elseif ($worklogs.Count -gt 0) {
        Add-Result -Level 'PASS' -Message 'no reclassification header inconsistency detected'
    }
    if ($handoffResumeIncomplete -gt 0) {
        Add-Result -Level 'WARN' -Message "work logs with ## Resume section missing required sub-sections (handoff.md §1a — Read Map, Skip List, Context Snapshot required): $handoffResumeIncomplete"
    } elseif ($worklogs.Count -gt 0) {
        Add-Result -Level 'PASS' -Message 'handoff Resume Blocks have required sub-sections where present'
    }
    if ($hotfixShipNoEvidence -gt 0) {
        Add-Result -Level 'WARN' -Message "hotfix work logs shipped without ## Evidence (hotfix fast-path still requires diff + behavior verification per handoff.md §Trigger Conditions): $hotfixShipNoEvidence"
    } elseif ($worklogs.Count -gt 0) {
        Add-Result -Level 'PASS' -Message 'hotfix shipped work logs carry evidence where present'
    }
    if ($adrCoverageUndocumented -gt 0) {
        Add-Result -Level 'WARN' -Message "feature/architecture-change work logs past plan phase with no ADR Coverage Check record in Drift Log (bootstrap.md §ADR Coverage Check result should be logged): $adrCoverageUndocumented"
    } elseif ($worklogs.Count -gt 0) {
        Add-Result -Level 'PASS' -Message 'ADR Coverage Check records present in applicable work logs'
    }

    # Gate receipt schema validation (§4.5 structural check) — parity with validate.sh.
    # Every pipe-format gate receipt in ## Gate Evidence must include Verdict: and
    # Classification: fields. WARN not FAIL (partial receipts are a process gap).
    $gateSchemaViolations = 0
    $gateSchemaViolationList = New-Object System.Collections.Generic.List[string]
    foreach ($wl in $worklogs) {
        $wlContent = Get-Content -Path $wl.FullName -Raw -Encoding utf8 -ErrorAction SilentlyContinue
        if (-not $wlContent) { continue }
        foreach ($receiptLine in ([regex]::Matches($wlContent, '(?im)^-\s+Gate\s*:.*$') | ForEach-Object { $_.Value })) {
            if ($receiptLine -notmatch '(?i)Verdict\s*:') {
                $gateSchemaViolations++
                $gateSchemaViolationList.Add("  malformed gate receipt (missing Verdict:) in $($wl.Name)")
                break
            }
            if ($receiptLine -notmatch '(?i)Classification\s*:') {
                $gateSchemaViolations++
                $gateSchemaViolationList.Add("  malformed gate receipt (missing Classification:) in $($wl.Name)")
                break
            }
        }
    }
    if ($gateSchemaViolations -gt 0) {
        Add-Result -Level 'WARN' -Message "active work log gate receipts missing required fields (Verdict/Classification): $gateSchemaViolations"
        foreach ($line in $gateSchemaViolationList) { Write-Output $line }
    } elseif ($worklogs.Count -gt 0) {
        Add-Result -Level 'PASS' -Message 'all active work log gate receipts have required fields (gate/verdict/classification)'
    }

    # Advisory lock staleness check — reads JSON fields per config.yaml §worklog_lock
    $staleLocks = 0
    $lockFiles = Get-ChildItem -Path $worklogDir -Filter '*.lock.json' -ErrorAction SilentlyContinue
    foreach ($lockf in $lockFiles) {
        try {
            $lockData = Get-Content -Path $lockf.FullName -Raw | ConvertFrom-Json
            $updatedAt = $lockData.updated_at
            $timeoutMin = if ($lockData.stale_timeout_minutes) { [int]$lockData.stale_timeout_minutes } else { 60 }
            if ($updatedAt) {
                $lockTime = [DateTimeOffset]::Parse($updatedAt)
                $ageMin = ((Get-Date) - $lockTime.LocalDateTime).TotalMinutes
                if ($ageMin -gt $timeoutMin) {
                    Write-Output "  stale advisory lock: $($lockf.Name) (timeout: ${timeoutMin}m)"
                    $staleLocks++
                }
            } else {
                Write-Output "  unreadable advisory lock (no valid updated_at): $($lockf.Name)"
                $staleLocks++
            }
        } catch {
            Write-Output "  unreadable advisory lock (invalid JSON): $($lockf.Name)"
            $staleLocks++
        }
    }
    if ($staleLocks -gt 0) {
        Add-Result -Level 'WARN' -Message "stale advisory work log locks detected: $staleLocks"
    }

    # Work Log lock owner/phase mismatch checks — WARN only, never FAIL.
    # Skips stale and unreadable locks (already covered above); skips orphan locks
    # (no matching Work Log .md).
    $ownerPhaseMismatches = 0
    foreach ($lockf in $lockFiles) {
        $lockData = $null
        try {
            $lockData = Get-Content -Path $lockf.FullName -Raw | ConvertFrom-Json
        } catch {
            continue  # unreadable — already covered
        }
        $updatedAt = $lockData.updated_at
        if (-not $updatedAt) { continue }  # unreadable — already covered
        $timeoutMin = if ($lockData.stale_timeout_minutes) { [int]$lockData.stale_timeout_minutes } else { 60 }
        try {
            $lockTime = [DateTimeOffset]::Parse($updatedAt)
            $ageMin = ((Get-Date) - $lockTime.LocalDateTime).TotalMinutes
            if ($ageMin -gt $timeoutMin) { continue }  # stale — already covered
        } catch {
            continue  # unparseable timestamp — already covered
        }
        $lockOwner = if ($lockData.owner) { $lockData.owner } else { '' }
        $lockPhase = if ($lockData.phase) { $lockData.phase } else { '' }
        # Derive Work Log path: strip .lock.json -> .md
        $wlName = $lockf.BaseName -replace '\.lock$', ''
        $wlPath = Join-NormalPath $worklogDir "$wlName.md"
        if (-not (Test-Path -Path $wlPath -PathType Leaf)) { continue }  # orphan lock
        $wlContent = Get-Content -Path $wlPath -Raw -Encoding utf8
        # Extract Owner: list form "- Owner: `x`" or table form "| Owner | x |"
        $wlOwner = ''
        if ($wlContent -match '(?m)^-\s+Owner\s*:\s*`?([^`\r\n]+)`?\s*$') {
            $wlOwner = $Matches[1].Trim().TrimStart('`').TrimEnd('`').Trim()
        } elseif ($wlContent -match '(?m)^\|\s*Owner\s*\|\s*([^|\r\n]+)\|') {
            $wlOwner = $Matches[1].Trim().TrimStart('`').TrimEnd('`').Trim()
        }
        # Extract Current Phase: list form or table form
        $wlPhase = ''
        if ($wlContent -match '(?m)^-\s+Current Phase\s*:\s*`?([^`\r\n]+)`?\s*$') {
            $wlPhase = $Matches[1].Trim().TrimStart('`').TrimEnd('`').Trim()
        } elseif ($wlContent -match '(?m)^\|\s*Current Phase\s*\|\s*([^|\r\n]+)\|') {
            $wlPhase = $Matches[1].Trim().TrimStart('`').TrimEnd('`').Trim()
        }
        if ($wlOwner -and $lockOwner -ne $wlOwner) {
            Write-Output "  worklog lock owner mismatch: $($lockf.Name) owner=$lockOwner worklog Owner=$wlOwner"
            $ownerPhaseMismatches++
        }
        if ($wlPhase -and $lockPhase -ne $wlPhase) {
            Write-Output "  worklog lock phase mismatch: $($lockf.Name) phase=$lockPhase worklog Current Phase=$wlPhase"
            $ownerPhaseMismatches++
        }
    }
    if ($ownerPhaseMismatches -gt 0) {
        Add-Result -Level 'WARN' -Message "work log lock owner/phase mismatches detected: $ownerPhaseMismatches"
    }
}
else {
    Add-Result -Level 'SKIP' -Message 'active work log directory not present'
}

if (Test-Path -Path $guardContextWrite -PathType Leaf) {
    Add-Result -Level 'PASS' -Message 'guarded write capability installed'
}
else {
    Add-Result -Level 'SKIP' -Message 'guard capability not installed'
}

$guardReceipt = Join-NormalPath $root '.agentcortex/context/.guard_receipt.json'
if (Test-Path -Path $guardReceipt -PathType Leaf) {
    Add-Result -Level 'PASS' -Message 'guard receipt present'
}
else {
    Add-Result -Level 'WARN' -Message "no guard receipt found at $guardReceipt; guarded writes remain advisory"
}

if (Test-Path -Path $optionalGuardHook -PathType Leaf) {
    Add-Result -Level 'PASS' -Message 'optional guard hook sample present'
}
else {
    Add-Result -Level 'WARN' -Message 'optional guard hook sample is not present; guarded-write checks remain advisory only'
}

# Work Log Phase Summary audit — pure PowerShell, no Python hooks.
# Sentinel (⚡ ACX) and PreCompact enforcement is model self-attestation per
# AGENTS.md. Audit happens here at validate-time on archived Work Logs:
# every archived non-tiny-fix Work Log MUST have a non-empty `## Phase
# Summary` section (replaces the runtime PreCompact hook intent).
$archiveDir = Join-NormalPath $root '.agentcortex/context/archive'
$phaseSummaryViolations = 0
$phaseSummaryViolationList = New-Object System.Collections.Generic.List[string]
if (Test-Path -Path $archiveDir -PathType Container) {
    # Exclude ship-history-*.md: compacted ship-history archives are not Work
    # Logs and have no '## Phase Summary' contract (#171).
    $archivedLogs = Get-ChildItem -Path $archiveDir -Filter '*.md' -File -Recurse -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -notlike '.gitkeep*' -and $_.Name -notlike 'ship-history-*' }
    foreach ($wl in $archivedLogs) {
        $content = Get-Content -Path $wl.FullName -Raw -Encoding utf8
        $classification = ''
        if ($content -match '(?m)^- \*\*Classification\*\*:\s*(.+?)\s*$') {
            $classification = $Matches[1].Trim()
        }
        if ($classification -eq 'tiny-fix') { continue }
        $summaryBody = ''
        if ($content -match '(?ms)^## Phase Summary\s*\r?\n(.*?)(?=\r?\n## |\z)') {
            $summaryBody = ($Matches[1] -replace '\s', '')
        }
        if ([string]::IsNullOrEmpty($summaryBody) -or $summaryBody -eq 'none') {
            $phaseSummaryViolations++
            $phaseSummaryViolationList.Add("  empty Phase Summary: $($wl.FullName.Substring($root.Length).TrimStart('/','\'))")
        }
    }
}
if ($phaseSummaryViolations -gt 0) {
    Add-Result -Level 'WARN' -Message "archived Work Logs with empty Phase Summary: $phaseSummaryViolations"
    foreach ($line in $phaseSummaryViolationList) { Write-Output $line }
}
else {
    Add-Result -Level 'PASS' -Message 'archived Work Logs have non-empty Phase Summary (or none archived yet)'
}

# M7: Gate completeness audit for archived Work Logs (WARN — historical records).
$archiveGateViolations = 0
$archiveGateViolationList = New-Object System.Collections.Generic.List[string]
if (Test-Path -Path $archiveDir -PathType Container) {
    $archivedLogsM7 = Get-ChildItem -Path $archiveDir -Filter '*.md' -File -Recurse -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -notlike '.gitkeep*' }
    foreach ($wl in $archivedLogsM7) {
        $arcContent = Get-Content -Path $wl.FullName -Raw -Encoding utf8 -ErrorAction SilentlyContinue
        if (-not $arcContent) { continue }
        $arcClassM = [regex]::Match($arcContent, '(?m)^- \*?\*?[Cc]lassification\*?\*?:\s*`?([a-zA-Z][\w-]*)`?')
        $arcClass = if ($arcClassM.Success) { $arcClassM.Groups[1].Value.ToLower() } else { '' }
        if ($arcClass -eq 'tiny-fix') { continue }
        if ($arcContent -match '(?i)Gate:\s*ship\s*\|[^|]*Verdict:\s*PASS') {
            $arcHasPlan = [regex]::Matches($arcContent, '(?i)Gate:\s*plan\s*\|[^|]*Verdict:\s*PASS').Count
            $arcHasImpl = [regex]::Matches($arcContent, '(?i)Gate:\s*implement\s*\|[^|]*Verdict:\s*PASS').Count
            if ($arcHasPlan -eq 0 -or $arcHasImpl -eq 0) {
                $archiveGateViolations++
                $archiveGateViolationList.Add("  archived gate bypass: $($wl.FullName.Substring($root.Length).TrimStart('/','\'))")
            }
        }
    }
}
if ($archiveGateViolations -gt 0) {
    Add-Result -Level 'WARN' -Message "archived Work Logs with ship receipt but missing plan/implement gates (historical governance gap): $archiveGateViolations"
    foreach ($line in $archiveGateViolationList) { Write-Output $line }
}
else {
    Add-Result -Level 'PASS' -Message 'archived Work Logs gate completeness ok (or none archived yet)'
}

# Gate receipt schema validation for archived Work Logs — parity with validate.sh.
# WARN only: archives are immutable historical records.
$archiveGateSchemaViolations = 0
$archiveGateSchemaViolationList = New-Object System.Collections.Generic.List[string]
if (Test-Path -Path $archiveDir -PathType Container) {
    $archivedLogsSchema = Get-ChildItem -Path $archiveDir -Filter '*.md' -File -Recurse -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -notlike '.gitkeep*' }
    foreach ($wl in $archivedLogsSchema) {
        $arcContent = Get-Content -Path $wl.FullName -Raw -Encoding utf8 -ErrorAction SilentlyContinue
        if (-not $arcContent) { continue }
        foreach ($receiptLine in ([regex]::Matches($arcContent, '(?im)^-\s+Gate\s*:.*$') | ForEach-Object { $_.Value })) {
            if ($receiptLine -notmatch '(?i)Verdict\s*:') {
                $archiveGateSchemaViolations++
                $archiveGateSchemaViolationList.Add("  malformed gate receipt (missing Verdict:) in $($wl.Name)")
                break
            }
            if ($receiptLine -notmatch '(?i)Classification\s*:') {
                $archiveGateSchemaViolations++
                $archiveGateSchemaViolationList.Add("  malformed gate receipt (missing Classification:) in $($wl.Name)")
                break
            }
        }
    }
}
if ($archiveGateSchemaViolations -gt 0) {
    Add-Result -Level 'WARN' -Message "archived Work Log gate receipts missing required fields (Verdict/Classification): $archiveGateSchemaViolations"
    foreach ($line in $archiveGateSchemaViolationList) { Write-Output $line }
}
else {
    Add-Result -Level 'PASS' -Message 'archived Work Log gate receipts have required fields (or none archived yet)'
}

# M8: Relative-link depth check for archived markdown files.
# Content copy-pasted from current_state.md (depth 2) into archive/ (depth 3)
# keeps original relative paths which silently break one level deeper.
if (-not $script:PythonCommand) {
    Add-Result -Level 'SKIP' -Message 'M8 archive relative-link check -- python unavailable'
} elseif (-not (Test-Path -Path $archiveDir -PathType Container)) {
    Add-Result -Level 'PASS' -Message 'archived markdown files: no archive directory yet (fresh deploy)'
} else {
    $archiveBrokenLinks = 0
    $archiveBrokenLinkList = New-Object System.Collections.Generic.List[string]
    $archiveMdFiles = Get-ChildItem -Path $archiveDir -Filter '*.md' -File -Recurse -Depth 1 -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -notlike '.gitkeep*' }
    foreach ($archMd in $archiveMdFiles) {
        $brokenOutput = & $script:PythonCommand.Source -c @"
import re, sys
from pathlib import Path
f = Path(r'$($archMd.FullName.Replace('\','/'))')
try:
    text = f.read_text(encoding='utf-8', errors='replace')
except Exception:
    print(0)
    sys.exit(0)
link_re = re.compile(r'\[(?:[^\]]*)\]\(([^)]+)\)')
count = 0
for m in link_re.finditer(text):
    tgt = m.group(1).strip()
    if tgt.startswith(('http://', 'https://')) or tgt.startswith('#'):
        continue
    path_part = tgt.split('#')[0]
    if not path_part:
        continue
    resolved = (f.parent / path_part).resolve()
    if not resolved.exists():
        print(f'  broken relative link in {str(f)}: {tgt}')
        count += 1
# Print count as last line so caller reads from stdout (exit-code wraps at 256)
print(count)
"@ 2>$null
        $lines = @($brokenOutput)
        $fileCount = 0
        if ($lines.Count -gt 0) {
            $lastLine = $lines[-1]
            if ($lastLine -match '^\d+$') { $fileCount = [int]$lastLine }
        }
        if ($fileCount -gt 0) {
            $archiveBrokenLinks += $fileCount
            foreach ($ln in $lines | Select-Object -SkipLast 1) { $archiveBrokenLinkList.Add($ln) }
        }
    }
    if ($archiveBrokenLinks -gt 0) {
        Add-Result -Level 'WARN' -Message "archived markdown files contain broken relative links (depth mismatch — strip or fix links when archiving from current_state.md): $archiveBrokenLinks"
        foreach ($line in $archiveBrokenLinkList) { Write-Output $line }
    }
    else {
        Add-Result -Level 'PASS' -Message 'archived markdown files: no broken relative links detected'
    }
}

$gitignore = Join-NormalPath $root '.gitignore'
if (Test-Path -Path $gitignore -PathType Leaf) {
    $gitignoreContent = Get-Content -Path $gitignore
    $gitignoreErrors = 0
    foreach ($mustTrack in @(
        '.agentcortex/context/current_state.md',
        '.agentcortex/context/archive/',
        '.agentcortex/specs/',
        '.agentcortex/adr/',
        'docs/specs/',
        'docs/adr/'
    )) {
        if ($gitignoreContent -contains $mustTrack) {
            Write-Output "  .gitignore must NOT ignore persistent SSoT artifact: $mustTrack"
            $gitignoreErrors++
        }
    }
    if ($gitignoreErrors -gt 0) {
        Add-Result -Level 'FAIL' -Message '.gitignore blocks persistent SSoT artifacts'
    }
    else {
        Add-Result -Level 'PASS' -Message '.gitignore preserves persistent SSoT artifacts'
    }
}
else {
    Add-Result -Level 'PASS' -Message '.gitignore absent -- no persistent SSoT artifacts are ignored'
}

# SSoT completeness checks — verify current_state.md indexes match disk reality
# Always run when current_state.md exists. Projects may legitimately have no ADRs
# (bootstrap allows skipping /app-init) but still own specs and backlog entries.
$currentStatePath = Join-NormalPath $root '.agentcortex/context/current_state.md'
if (Test-Path -Path $currentStatePath -PathType Leaf) {
    $csContent = Get-Content -Path $currentStatePath -Raw -Encoding utf8

    # ADR Index completeness
    $adrIndexSection = ''
    if ($csContent -match '(?ms)\*\*ADR Index\*\*:(.*?)(?=\n-\s*\*\*|\n##|\z)') {
        $adrIndexSection = $Matches[1]
    }
    $indexedAdrPaths = @([regex]::Matches($adrIndexSection, '(?m)^\s*-\s+(\S.*?\.md)') | ForEach-Object { $_.Groups[1].Value.Trim() })
    $diskAdrFiles = @()
    foreach ($adrGlob in @('docs/adr/ADR-*.md', '.agentcortex/adr/ADR-*.md')) {
        $adrDir = Join-NormalPath $root ($adrGlob -replace '/ADR-\*\.md', '')
        if (Test-Path -Path $adrDir -PathType Container) {
            $diskAdrFiles += @(Get-ChildItem -Path $adrDir -Filter 'ADR-*.md' -ErrorAction SilentlyContinue |
                ForEach-Object { ($_.FullName.Replace($root + [System.IO.Path]::DirectorySeparatorChar, '').Replace('\', '/')) })
        }
    }
    $adrMissing = @($diskAdrFiles | Where-Object { $_ -notin $indexedAdrPaths })
    $adrPhantom = @($indexedAdrPaths | Where-Object { $_ -and ($_ -notin $diskAdrFiles) })
    if ($adrMissing.Count -gt 0 -or $adrPhantom.Count -gt 0) {
        $adrMsg = @()
        if ($adrMissing.Count -gt 0) { $adrMsg += "$($adrMissing.Count) disk ADR(s) not in index" }
        if ($adrPhantom.Count -gt 0) { $adrMsg += "$($adrPhantom.Count) indexed ADR(s) not on disk" }
        Add-Result -Level 'FAIL' -Message "SSoT ADR Index completeness: $($adrMsg -join '; ')"
        foreach ($m in $adrMissing) { Write-Output "  not indexed: $m" }
        foreach ($m in $adrPhantom) { Write-Output "  phantom index entry: $m" }
        Write-Output "  fix: update ADR Index in .agentcortex/context/current_state.md via /ship"
    }
    else {
        Add-Result -Level 'PASS' -Message 'SSoT ADR Index completeness: all disk ADRs are indexed'
    }

    # Spec Index completeness
    $specIndexSection = ''
    if ($csContent -match '(?ms)\*\*Spec Index\*\*[^:]*:(.*?)(?=\n-\s*\*\*|\n##|\z)') {
        $specIndexSection = $Matches[1]
    }
    $diskSpecFiles = @()
    foreach ($specGlob in @('docs/specs', '.agentcortex/specs')) {
        $specDir = Join-NormalPath $root $specGlob
        if (Test-Path -Path $specDir -PathType Container) {
            $diskSpecFiles += @(Get-ChildItem -Path $specDir -Filter '*.md' -ErrorAction SilentlyContinue |
                Where-Object { $_.Name -notmatch '^[_.]' } |
                ForEach-Object {
                    $relPath = $_.FullName.Replace($root + [System.IO.Path]::DirectorySeparatorChar, '').Replace('\', '/')
                    $fileContent = Get-Content -Path $_.FullName -Raw -ErrorAction SilentlyContinue
                    if ($fileContent -and $fileContent -match '(?m)^status:\s*draft') { return }
                    $relPath
                })
        }
    }
    $specMissing = @($diskSpecFiles | Where-Object { $_ -and ($specIndexSection -notmatch [regex]::Escape($_)) })
    $indexedSpecPaths = @([regex]::Matches($specIndexSection, '(?m)\]\s+([\w./-]+\.md)\s') | ForEach-Object { $_.Groups[1].Value.Trim() })
    $specPhantom = @($indexedSpecPaths | Where-Object { $_ -and -not (Test-Path -Path (Join-NormalPath $root $_) -PathType Leaf) })
    if ($specMissing.Count -gt 0 -or $specPhantom.Count -gt 0) {
        $specMsg = @()
        if ($specMissing.Count -gt 0) { $specMsg += "$($specMissing.Count) non-draft spec(s) not in index" }
        if ($specPhantom.Count -gt 0) { $specMsg += "$($specPhantom.Count) indexed spec(s) not on disk" }
        Add-Result -Level 'FAIL' -Message "SSoT Spec Index completeness: $($specMsg -join '; ')"
        foreach ($m in $specMissing) { Write-Output "  not indexed: $m" }
        foreach ($m in $specPhantom) { Write-Output "  phantom index entry: $m" }
        Write-Output "  fix: update Spec Index in .agentcortex/context/current_state.md via /ship"
    }
    else {
        Add-Result -Level 'PASS' -Message 'SSoT Spec Index completeness: all non-draft specs are indexed'
    }

    # Active Backlog consistency
    $productBacklog = Join-NormalPath $root 'docs/specs/_product-backlog.md'
    if (Test-Path -Path $productBacklog -PathType Leaf) {
        if ($csContent -match '(?m)^- \*\*Active Backlog\*\*:\s*none') {
            Add-Result -Level 'FAIL' -Message 'SSoT Active Backlog consistency: _product-backlog.md exists but SSoT Active Backlog is "none"'
            Write-Output '  fix: set Active Backlog to `docs/specs/_product-backlog.md` in current_state.md via /ship'
        }
        else {
            # Path-value mismatch check: SSoT must reference docs/specs/_product-backlog.md
            if ($csContent -match '(?m)\*\*Active Backlog\*\*:\s*`([^`]+)`') {
                $backlogRef = $Matches[1]
                if ($backlogRef -ne 'docs/specs/_product-backlog.md') {
                    Add-Result -Level 'FAIL' -Message "SSoT Active Backlog consistency: SSoT Active Backlog references '$backlogRef' but actual backlog is at docs/specs/_product-backlog.md"
                    Write-Output "  fix: set Active Backlog to \`docs/specs/_product-backlog.md\` in current_state.md via /ship"
                }
                else {
                    Add-Result -Level 'PASS' -Message 'SSoT Active Backlog consistency: backlog file and SSoT are consistent'
                }
            }
            else {
                Add-Result -Level 'PASS' -Message 'SSoT Active Backlog consistency: backlog file and SSoT are consistent'
            }
        }
    }
    elseif ($csContent -match '(?m)\*\*Active Backlog\*\*:\s*`([^`]+)`') {
        $backlogRef = $Matches[1]
        if (-not (Test-Path -Path (Join-NormalPath $root $backlogRef) -PathType Leaf)) {
            Add-Result -Level 'FAIL' -Message "SSoT Active Backlog consistency: SSoT references '$backlogRef' but file does not exist"
            Write-Output "  fix: update Active Backlog in current_state.md via /ship or create the missing file"
        }
        else {
            Add-Result -Level 'PASS' -Message 'SSoT Active Backlog consistency: backlog file and SSoT are consistent'
        }
    }
    else {
        Add-Result -Level 'PASS' -Message 'SSoT Active Backlog consistency: no backlog file on disk'
    }
}
else {
    Add-Result -Level 'WARN' -Message 'SSoT completeness checks skipped: current_state.md not found'
}

# Ship History pending-SHA guard: commit references must be resolved SHAs.
# A "pending" placeholder is valid for at most the duration of the ship branch;
# after merge it must be replaced. Warn so CI surfaces unresolved references.
if (Test-Path -Path $currentStatePath -PathType Leaf) {
    $csRaw = Get-NormalizedContent -Path $currentStatePath
    $pendingCount = ([regex]::Matches($csRaw, '(?m)^- Commits: pending')).Count
    if ($pendingCount -gt 0) {
        Add-Result -Level 'WARN' -Message "Ship History has $pendingCount unresolved 'pending' commit reference(s) — replace with real SHAs after merge"
    }
    else {
        Add-Result -Level 'PASS' -Message 'Ship History commit references are all resolved'
    }
}

# Backlog Feature Inventory check (MEDIUM-2): spec-intake multi-feature decomposition gate
# requires a ## Feature Inventory section per AGENTS.md §Delivery Gates.
$backlogFile = Join-NormalPath $root 'docs/specs/_product-backlog.md'
if (Test-Path -Path $backlogFile -PathType Leaf) {
    $backlogRaw = Get-NormalizedContent -Path $backlogFile
    if ($backlogRaw -notmatch '(?im)^#+\s+Feature Inventory') {
        Add-Result -Level 'WARN' -Message "backlog missing Feature Inventory section: _product-backlog.md exists but has no '## Feature Inventory' heading -- spec-intake multi-feature decomposition gate may have been skipped"
    } else {
        Add-Result -Level 'PASS' -Message 'backlog Feature Inventory section present'
    }
}

# Backlog schema check: verify Kind/Labels/Priority columns present when backlog exists
if (Test-Path -Path $backlogFile -PathType Leaf) {
    $backlogLines = Get-Content -Path $backlogFile -Encoding utf8
    $backlogHeader = $backlogLines | Where-Object { $_ -match '\|.*Feature.*\|' } | Select-Object -First 1
    $missingCols = @()
    if ($backlogHeader -notmatch 'Kind')     { $missingCols += 'Kind' }
    if ($backlogHeader -notmatch 'Labels')   { $missingCols += 'Labels' }
    if ($backlogHeader -notmatch 'Priority') { $missingCols += 'Priority' }
    if ($missingCols.Count -eq 0) {
        Add-Result -Level 'PASS' -Message 'backlog schema: Kind/Labels/Priority columns present'

        $pendingRows = @($backlogLines | Where-Object { $_ -match '\| Pending' })
        $totalPending = $pendingRows.Count

        # L-1: P0 ratio lint — warn if >20% of pending items are P0
        if ($totalPending -gt 4) {
            $p0Pending = @($pendingRows | Where-Object { $_ -match '\| P0 \|' }).Count
            if ($p0Pending -gt 0) {
                $p0Ratio = [int]($p0Pending * 100 / $totalPending)
                if ($p0Ratio -gt 20) {
                    Add-Result -Level 'WARN' -Message "backlog P0 ratio: $p0Pending/$totalPending pending items are P0 ($p0Ratio% > 20% threshold — consider downgrading some)"
                }
                else {
                    Add-Result -Level 'PASS' -Message "backlog P0 ratio: $p0Pending/$totalPending pending items are P0 ($p0Ratio%)"
                }
            }
        }

        # L-3: Kind distribution sanity — warn if all non-— rows share one Kind value
        if ($totalPending -gt 9) {
            $kindValues = @($pendingRows | ForEach-Object {
                $cols = $_ -split '\|'
                if ($cols.Count -gt 3) { $cols[3].Trim() }
            } | Where-Object { $_ -ne '' -and $_ -ne '—' } | Sort-Object -Unique)
            $kindVariety = $kindValues.Count
            if ($kindVariety -eq 1) {
                Add-Result -Level 'WARN' -Message 'backlog Kind diversity: all assigned pending items share the same Kind value — review-finding and hotfix-spawn entries may not be reaching the backlog'
            }
            else {
                Add-Result -Level 'PASS' -Message "backlog Kind diversity: $kindVariety distinct Kind values in use"
            }
        }

        # L-3b: schema-zero guard — L-3 silently PASSes when ALL pending items have Kind=—
        # (kindVariety=0 ≠ 1, so falls to the PASS branch without surfacing the empty schema).
        if ($totalPending -gt 5) {
            $kindAssigned = @($pendingRows | ForEach-Object {
                $cols = $_ -split '\|'
                if ($cols.Count -gt 3) { $cols[3].Trim() }
            } | Where-Object { $_ -ne '' -and $_ -ne '—' }).Count
            if ($kindAssigned -eq 0) {
                Add-Result -Level 'WARN' -Message "backlog Kind schema-zero: all $totalPending pending items have Kind=— — populate Kind column to enable cluster routing and L-3 diversity checks"
            }
        }

        # L-2: label vocabulary drift — warn if distinct label count exceeds 15
        $distinctLabels = @($pendingRows | ForEach-Object {
            $cols = $_ -split '\|'
            if ($cols.Count -gt 4) {
                $cols[4] -split ',' | ForEach-Object { $_.Trim() }
            }
        } | Where-Object { $_ -ne '' -and $_ -ne '—' } | Sort-Object -Unique).Count
        if ($distinctLabels -gt 15) {
            Add-Result -Level 'WARN' -Message "backlog label vocabulary: $distinctLabels distinct labels (>15) — possible drift across sessions; review and consolidate via /spec-intake"
        }
        elseif ($distinctLabels -gt 0) {
            Add-Result -Level 'PASS' -Message "backlog label vocabulary: $distinctLabels distinct labels"
        }

        # L-4: cluster-declined marker GC — warn if too many suppressions accumulated
        $declinedCount = @($backlogLines | Where-Object { $_ -match 'cluster-declined:' }).Count
        if ($declinedCount -gt 5) {
            Add-Result -Level 'WARN' -Message "backlog cluster-declined: $declinedCount suppression markers (>5) — review expired/stale suppressions in _product-backlog.md ## Source Summary"
        }
        elseif ($declinedCount -gt 0) {
            Add-Result -Level 'PASS' -Message "backlog cluster-declined: $declinedCount suppression marker(s)"
        }
    }
    else {
        Add-Result -Level 'WARN' -Message "backlog schema: missing column(s): $($missingCols -join ', ')"
        Write-Output '  fix: run /spec-intake to trigger merge-guard backfill, or add columns manually'
        Write-Output '  manual fix: add columns to Feature Inventory header row and backfill existing rows with —'
    }
}

# Backlog structure validation (#18): frontmatter fields, structural columns, Status enum, spec links.
# Catches structural corruption that would break /spec-intake feature matching but is invisible
# to the existence-only checks above.
if (Test-Path -Path $backlogFile -PathType Leaf) {
    $backlogText = Get-NormalizedContent -Path $backlogFile
    $backlogStructLines = Get-Content -Path $backlogFile -Encoding utf8

    # (1) YAML frontmatter required fields: title, created, status
    $fmMissing = @()
    if ($backlogText -match '(?s)^---\s*\r?\n(.*?)\r?\n---\s*\r?\n') {
        $fm = $Matches[1]
        if ($fm -notmatch '(?m)^title:')   { $fmMissing += 'title' }
        if ($fm -notmatch '(?m)^created:') { $fmMissing += 'created' }
        if ($fm -notmatch '(?m)^status:')  { $fmMissing += 'status' }
    }
    else {
        $fmMissing = @('title', 'created', 'status')
    }
    if ($fmMissing.Count -eq 0) {
        Add-Result -Level 'PASS' -Message 'backlog frontmatter: required fields (title, created, status) present'
    }
    else {
        Add-Result -Level 'FAIL' -Message "backlog frontmatter: missing required field(s): $($fmMissing -join ', ')"
        Write-Output '  fix: add the missing field(s) to the YAML frontmatter of _product-backlog.md'
    }

    # (2) Feature Inventory structural columns: #, Status, Tier (complements Kind/Labels/Priority above)
    $structHeader = $backlogStructLines | Where-Object { $_ -match '\|.*Feature.*\|' } | Select-Object -First 1
    $structMissing = @()
    if ($structHeader -notmatch '\|\s*#\s*\|') { $structMissing += '#' }
    if ($structHeader -notmatch 'Status')      { $structMissing += 'Status' }
    if ($structHeader -notmatch 'Tier')        { $structMissing += 'Tier' }
    if ($structMissing.Count -eq 0) {
        Add-Result -Level 'PASS' -Message 'backlog structure: #/Status/Tier columns present'
    }
    else {
        Add-Result -Level 'WARN' -Message "backlog structure: missing column(s): $($structMissing -join ', ')"
    }

    # (3) Status enum compliance: every numbered Feature Inventory row uses a known Status value.
    # The enum token is matched as an isolated `| <status> |` cell anywhere in the row rather than
    # by fixed column index — safe because no other column holds a bare enum word as an isolated
    # cell (Dependencies use --/#N/dates, Spec File holds paths, Feature holds prose).
    $badStatus = @()
    foreach ($brow in $backlogStructLines) {
        if ($brow -notmatch '^\|\s*[0-9]+\s*\|') { continue }
        if ($brow -notmatch '\|\s*(Pending|In Progress|Shipped|Deferred|Cancelled)\s*\|') {
            $bnum = ([regex]'^\|\s*([0-9]+)').Match($brow).Groups[1].Value
            $badStatus += "#$bnum"
        }
    }
    if ($badStatus.Count -gt 0) {
        Add-Result -Level 'FAIL' -Message "backlog Status enum: row(s) $($badStatus -join ' ') have a Status not in {Pending, In Progress, Shipped, Deferred, Cancelled}"
        Write-Output '  fix: correct the Status cell to a valid enum value in _product-backlog.md'
    }
    else {
        Add-Result -Level 'PASS' -Message 'backlog Status enum: all Feature Inventory rows use valid Status values'
    }

    # (4) Spec link existence: referenced docs/specs/*.md files should exist on disk
    $specRefs = [regex]::Matches($backlogText, 'docs/specs/[A-Za-z0-9._/-]+\.md') | ForEach-Object { $_.Value } | Sort-Object -Unique
    $missingSpecs = @()
    foreach ($sref in $specRefs) {
        if (-not (Test-Path -Path (Join-NormalPath $root $sref) -PathType Leaf)) {
            $missingSpecs += $sref
        }
    }
    if ($missingSpecs.Count -gt 0) {
        Add-Result -Level 'WARN' -Message "backlog spec links: referenced spec file(s) not found: $($missingSpecs -join ' ') (pending features may not have specs yet)"
    }
    else {
        Add-Result -Level 'PASS' -Message 'backlog spec links: all referenced spec files exist'
    }
}

# Routing index governance split checks
$routingIndex = Join-NormalPath $workflowsDir 'routing.md'
if (Test-Path -Path $routingIndex -PathType Leaf) {
    Add-Result -Level 'PASS' -Message 'routing index present at .agent/workflows/routing.md'
    Test-ContainsLiteral -Path $routingIndex -Pattern 'canonical: true' -SuccessMessage 'routing index declares canonical authority' -FailureMessage 'routing index missing canonical authority marker'
    Test-ContainsLiteral -Path $routingIndex -Pattern 'AGENTS.md outranks' -SuccessMessage 'routing index acknowledges AGENTS.md precedence' -FailureMessage 'routing index missing AGENTS.md precedence acknowledgment'
}
else {
    Add-Result -Level 'FAIL' -Message 'routing index missing at .agent/workflows/routing.md'
}
Test-ContainsLiteral -Path $projectAgentsFile -Pattern '.agent/workflows/routing.md' -SuccessMessage 'AGENTS.md references routing index (authority handoff present)' -FailureMessage 'AGENTS.md missing routing index reference (authority handoff absent)'
Test-ContainsLiteral -Path (Join-NormalPath $workflowsDir 'commands.md') -Pattern '.agent/workflows/routing.md' -SuccessMessage 'commands.md points to canonical routing index' -FailureMessage 'commands.md missing canonical routing index reference'

# Security scanning workflow presence check (AC-8 of ci-security-scanning spec)
# Only relevant for repos using GitHub Actions (skip for non-Actions repos)
$securityWorkflow = Join-NormalPath $root '.github/workflows/security.yml'
$githubWorkflowsDir = Join-NormalPath $root '.github/workflows'
if (Test-Path -Path $githubWorkflowsDir -PathType Container) {
    if (Test-Path -Path $securityWorkflow -PathType Leaf) {
        Add-Result -Level 'PASS' -Message 'security scanning workflow present at .github/workflows/security.yml'
    }
    else {
        Add-Result -Level 'WARN' -Message 'security scanning workflow absent — .github/workflows/security.yml not found (add SAST + secret detection + dependency audit to protect this repo)'
    }
}

# Document lifecycle bloat checks
$globalLessonsMax = if ($env:GLOBAL_LESSONS_MAX) { [int]$env:GLOBAL_LESSONS_MAX } else { 20 }
if (Test-Path -Path $currentStatePath -PathType Leaf) {
    $lessonsCount = ([regex]::Matches($csContent, '(?m)^- \[Category:')).Count
    if ($lessonsCount -gt $globalLessonsMax) {
        Add-Result -Level 'WARN' -Message "Global Lessons exceeds cap ($lessonsCount > $globalLessonsMax); run /retro to archive LOW-severity entries"
    }
    elseif ($lessonsCount -gt 0) {
        Add-Result -Level 'PASS' -Message "Global Lessons count within cap ($lessonsCount/$globalLessonsMax)"
    }
}

# Stale _raw-intake check
$specsDir = Join-NormalPath $root 'docs/specs'
if (Test-Path -Path $specsDir -PathType Container) {
    $staleRawIntake = @(Get-ChildItem -Path $specsDir -Filter '_raw-intake*.md' -File -ErrorAction SilentlyContinue)
    if ($staleRawIntake.Count -gt 0) {
        Add-Result -Level 'WARN' -Message "stale _raw-intake files detected: $($staleRawIntake.Count) -- /ship should clean these up"
    }
}

# Project spec template check (#172) (parity with validate.sh): detect a genuine
# downstream app that ran /app-init by its project-architecture ADR
# (ADR-00N-project-architecture.md). The framework's own governance ADRs do not
# match this pattern, so these checks never false-fire on the framework repo;
# the signal is deploy-independent so it also covers fork/clone adopters.
$appInitAdrCount = 0
foreach ($adrDir in @((Join-NormalPath $root 'docs/adr'), (Join-NormalPath $root '.agentcortex/adr'))) {
    if (Test-Path -Path $adrDir -PathType Container) {
        $appInitAdrCount += @(Get-ChildItem -Path $adrDir -Filter '*-project-architecture.md' -File -ErrorAction SilentlyContinue).Count
    }
}
if ($appInitAdrCount -gt 0) {
    $projectTemplates = @(Get-ChildItem -Path (Join-NormalPath $root '.agentcortex/templates') -Filter 'spec-app-feature-*.md' -File -ErrorAction SilentlyContinue)
    if ($projectTemplates.Count -eq 0) {
        Add-Result -Level 'WARN' -Message "project spec template missing: docs/adr/ has ADR(s) but no .agentcortex/templates/spec-app-feature-<project>.md found -- run /app-init to create one, or spec-intake will use the generic template"
    }
    else {
        Add-Result -Level 'PASS' -Message 'project spec template present alongside ADR(s)'
    }
    # Round-15 Finding 1/10: Project Name SSoT presence check
    $csFile = Join-NormalPath $root '.agentcortex/context/current_state.md'
    if (Test-Path -Path $csFile -PathType Leaf) {
        $csContent15 = Get-Content -Path $csFile -Raw -Encoding UTF8
        $projNameM = [regex]::Match($csContent15, '(?m)\*\*Project Name\*\*:\s*(.+)')
        $projNameVal = if ($projNameM.Success) { $projNameM.Groups[1].Value.Trim() } else { '' }
        if ([string]::IsNullOrWhiteSpace($projNameVal) -or $projNameVal -eq '(set by /app-init)') {
            Add-Result -Level 'WARN' -Message "Project Name field absent or placeholder in current_state.md -- /app-init has run (ADRs exist) but SSoT Project Name was not set; spec-intake will fall back to glob template resolution"
        } else {
            Add-Result -Level 'PASS' -Message "SSoT Project Name is set: $projNameVal"
        }
    }
}

# Round-16 Finding 7: Domain Decisions entry cap (spec.md §8 hard cap: 10 entries)
$domainDecisionsExceeded = 0
if (Test-Path -Path $specsDir -PathType Container) {
    foreach ($specFile in (Get-ChildItem -Path $specsDir -Filter '*.md' -File -ErrorAction SilentlyContinue)) {
        if ($specFile.Name -eq '.gitkeep.md') { continue }
        $specContent = Get-Content -Path $specFile.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
        if ($specContent -match '(?m)^## Domain Decisions') {
            $ddMatch = [regex]::Match($specContent, '(?ms)^## Domain Decisions\r?\n(.*?)(?=^## |\z)')
            $ddBody = if ($ddMatch.Success) { $ddMatch.Groups[1].Value } else { '' }
            $entryCount = ([regex]::Matches($ddBody, '\[(DECISION|TRADEOFF|CONSTRAINT)\]')).Count
            if ($entryCount -gt 10) {
                Write-Host "  spec Domain Decisions cap exceeded: $($specFile.Name) ($entryCount entries > 10)"
                $domainDecisionsExceeded++
            }
        }
    }
}
if ($domainDecisionsExceeded -gt 0) {
    Add-Result -Level 'WARN' -Message "docs/specs/ files with Domain Decisions exceeding 10-entry cap (spec.md §8 — requires user acknowledgment): $domainDecisionsExceeded"
} else {
    $specDdCount = 0
    if (Test-Path -Path $specsDir -PathType Container) {
        foreach ($sf in (Get-ChildItem -Path $specsDir -Filter '*.md' -File -ErrorAction SilentlyContinue)) {
            $sfContent = Get-Content -Path $sf.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
            if ($sfContent -match '(?m)^## Domain Decisions') { $specDdCount++ }
        }
    }
    if ($specDdCount -gt 0) { Add-Result -Level 'PASS' -Message 'all specs with Domain Decisions sections are within 10-entry cap' }
}

# Round-15 Finding 7: Spec frontmatter status validation
$validStatuses = @('draft','frozen','shipped','cancelled','living')
$specBadStatus = 0; $specMissingFrontmatter = 0; $specFileCount = 0
$specsDir = Join-NormalPath $root 'docs/specs'
if (Test-Path -Path $specsDir -PathType Container) {
    foreach ($specFile in (Get-ChildItem -Path $specsDir -Filter '*.md' -File -ErrorAction SilentlyContinue)) {
        if ($specFile.Name -eq '.gitkeep.md') { continue }  # skip placeholder
        # Skip _-prefixed meta/index files (_product-backlog*, _research-*): not
        # governed specs; exempt from the status enum, parity with validate.sh (#170).
        if ($specFile.Name -like '_*') { continue }
        $specFileCount++
        $specLines = Get-Content -Path $specFile.FullName -Encoding UTF8 -ErrorAction SilentlyContinue
        if (-not $specLines -or $specLines[0].TrimEnd() -ne '---') {
            $specMissingFrontmatter++; continue
        }
        # Scan for status: ONLY within the frontmatter block — from line 1 until
        # the closing `---` (or EOF if unclosed) — mirroring validate.sh's awk
        # `/^---/{if(n++) exit}` scoping so a body line `status: x` cannot be
        # misread as frontmatter (F2 parity).
        $statusLine = $null
        for ($i = 1; $i -lt $specLines.Count; $i++) {
            if ($specLines[$i].TrimEnd() -eq '---') { break }
            if ($specLines[$i] -match '^status:\s*') { $statusLine = $specLines[$i]; break }
        }
        if (-not $statusLine) { $specMissingFrontmatter++; continue }
        $statusVal = ($statusLine -replace '^status:\s*','').Trim()
        if ($validStatuses -notcontains $statusVal) { $specBadStatus++ }
    }
}
if ($specMissingFrontmatter -gt 0) {
    Add-Result -Level 'WARN' -Message "docs/specs/ files missing YAML frontmatter or status field: $specMissingFrontmatter (engineering_guardrails.md §4.2 requires status: draft|frozen|shipped|cancelled)"
} elseif ($specBadStatus -gt 0) {
    Add-Result -Level 'WARN' -Message "docs/specs/ files with unrecognized status value: $specBadStatus (valid: draft, frozen, shipped, cancelled, living)"
} elseif ($specFileCount -gt 0) {
    Add-Result -Level 'PASS' -Message 'all docs/specs/ files have valid status frontmatter'
}

# ACX phase shim skill-existence check (parity with validate.sh)
$agentsDir = Join-NormalPath $root '.claude/agents'
if (Test-Path -Path $agentsDir -PathType Container) {
    $shimSkillErrors = 0
    $shimCount = 0
    foreach ($shim in (Get-ChildItem -Path $agentsDir -Filter 'acx-*.md' -File -ErrorAction SilentlyContinue)) {
        $shimCount++
        $lines = Get-Content -Path $shim.FullName -Encoding UTF8
        $inFrontmatter = $false; $inSkills = $false
        foreach ($line in $lines) {
            if ($line -eq '---') { $inFrontmatter = -not $inFrontmatter; $inSkills = $false; continue }
            if (-not $inFrontmatter) { break }
            if ($line -match '^skills:') { $inSkills = $true; continue }
            if ($inSkills) {
                if ($line -match '^\s+-\s+(.+)$') {
                    $skillName = $Matches[1].Trim()
                    $skillDir = Join-NormalPath $root ".agent/skills/$skillName"
                    if (Test-Path -Path $skillDir -PathType Leaf) {
                        $skillBody = Join-NormalPath $root ".agents/skills/$skillName/SKILL.md"
                        if (-not (Test-Path -Path $skillBody -PathType Leaf)) {
                            Write-Output "  shim skill missing SKILL.md: $skillName (referenced in $($shim.Name))"
                            $shimSkillErrors++
                        }
                    }
                } elseif ($line -notmatch '^\s') { $inSkills = $false }
            }
        }
    }
    if ($shimCount -eq 0) {
        Add-Result -Level 'SKIP' -Message 'acx phase shim skill check -- no acx-*.md shims found in .claude/agents/'
    } elseif ($shimSkillErrors -gt 0) {
        Add-Result -Level 'FAIL' -Message "acx phase shim skill references are broken: $shimSkillErrors missing SKILL.md"
    } else {
        Add-Result -Level 'PASS' -Message "acx phase shim skill references are all valid ($shimCount shims checked)"
    }
} else {
    Add-Result -Level 'SKIP' -Message 'acx phase shim skill check -- .claude/agents/ not present'
}

# Governance eval coverage advisory (AC-7): capability-by-presence.
# If .agentcortex/eval/governance.yaml exists AND python is available, run
# run_governance_eval.py --coverage and WARN with the count of MUST-rule
# sections that have zero guarding cases. Never FAIL; silent skip when the
# eval file or python is absent. Zero zero-coverage rules -> PASS.
$acxEvalYaml   = Join-NormalPath $root '.agentcortex/eval/governance.yaml'
$acxEvalRunner = Join-NormalPath $root '.agentcortex/tools/run_governance_eval.py'
if (Test-Path -Path $acxEvalYaml -PathType Leaf) {
    if (-not $script:PythonCommand) {
        Add-Result -Level 'SKIP' -Message 'governance eval coverage -- python unavailable (install Python 3.9+ for full validation)'
    } elseif (-not (Test-Path -Path $acxEvalRunner -PathType Leaf)) {
        Add-Result -Level 'SKIP' -Message 'governance eval coverage -- runner not present (run_governance_eval.py missing)'
    } else {
        $prevEA = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        $evalCovText = & $script:PythonCommand.Source $acxEvalRunner --coverage 2>&1 | Out-String
        $ErrorActionPreference = $prevEA
        $zeroMatch = [regex]::Match($evalCovText, 'Zero-coverage rules:\s*(\d+)')
        $zeroCnt = if ($zeroMatch.Success) { [int]$zeroMatch.Groups[1].Value } else { 0 }
        if ($zeroCnt -gt 0) {
            Add-Result -Level 'WARN' -Message "governance eval coverage: $zeroCnt MUST-rule section(s) without eval cases (tier-blind: includes machine-enforced and principle-tier rules; see guardrails s13)"
            $zeroLines = ($evalCovText -split "`r?`n") | Where-Object { $_ -match '^\s+-\s+' } | Select-Object -First 20
            foreach ($zl in $zeroLines) { Write-Output "  $zl" }
        } else {
            Add-Result -Level 'PASS' -Message 'governance eval coverage: 0 MUST-rule section(s) with zero guarding cases'
        }
    }
}

# AC-6: governance specs missing signal_tier frontmatter (guardrails §13 ADD-Gate).
# Advisory WARN only — never FAIL. Checks docs/specs/*.md (skips _* meta/index
# files). Conditions to WARN (ALL must hold):
#   1. frontmatter primary_domain: contains "governance" (case-insensitive).
#   2. frontmatter created: >= 2026-06-10 (ISO, lexical compare). Missing = skip.
#   3. frontmatter status: is NOT shipped or cancelled.
#   4. frontmatter has NO signal_tier: line (any value silences).
$stWarnCount = 0
$stWarnFiles = @()
$stSpecDir = Join-NormalPath $root 'docs/specs'
if (Test-Path -Path $stSpecDir -PathType Container) {
    foreach ($stSpec in Get-ChildItem -Path $stSpecDir -Filter '*.md' -File -ErrorAction SilentlyContinue) {
        # Skip underscore-prefixed meta/index specs (_*.md).
        if ($stSpec.Name -like '_*') { continue }
        $stRaw = Get-Content -LiteralPath $stSpec.FullName -Raw -Encoding utf8 -ErrorAction SilentlyContinue
        if ($null -eq $stRaw) { continue }
        # Normalize line endings, then extract YAML frontmatter between first --- pair.
        $stNorm = $stRaw -replace "`r`n", "`n" -replace "`r", "`n"
        $stLines = $stNorm -split "`n"
        $stFmLines = @()
        $stInFm = $false
        $stFmDone = $false
        foreach ($stLine in $stLines) {
            if (-not $stFmDone) {
                if ($stLine -eq '---') {
                    if (-not $stInFm) { $stInFm = $true; continue }
                    else { $stFmDone = $true; break }
                }
                if ($stInFm) { $stFmLines += $stLine }
            }
        }
        $stFm = $stFmLines -join "`n"
        # Condition 1: primary_domain contains "governance" (case-insensitive).
        $stDomainMatch = [regex]::Match($stFm, '(?m)^primary_domain:\s*(.+)$')
        if (-not $stDomainMatch.Success) { continue }
        $stDomain = $stDomainMatch.Groups[1].Value.Trim()
        if ($stDomain -notmatch '(?i)governance') { continue }
        # Condition 2: created: >= 2026-06-10 (lexical). Missing = grandfathered, skip.
        $stCreatedMatch = [regex]::Match($stFm, '(?m)^created:\s*(.+)$')
        if (-not $stCreatedMatch.Success) { continue }
        $stCreated = $stCreatedMatch.Groups[1].Value.Trim()
        if ($stCreated -lt '2026-06-10') { continue }
        # Condition 3: status not shipped or cancelled.
        $stStatusMatch = [regex]::Match($stFm, '(?m)^status:\s*(\S+)')
        $stStatus = if ($stStatusMatch.Success) { $stStatusMatch.Groups[1].Value.Trim() } else { '' }
        if ($stStatus -eq 'shipped' -or $stStatus -eq 'cancelled') { continue }
        # Condition 4: no signal_tier: line present.
        if ($stFm -match '(?m)^signal_tier:') { continue }
        $stWarnFiles += $stSpec.Name
        $stWarnCount++
    }
}
if ($stWarnCount -gt 0) {
    Add-Result -Level 'WARN' -Message "governance specs missing signal_tier frontmatter (guardrails §13 ADD-Gate): $stWarnCount"
    foreach ($stF in $stWarnFiles) {
        Write-Output "  governance spec missing signal_tier: $stF"
    }
} else {
    Add-Result -Level 'PASS' -Message 'governance-rule specs declare signal_tier (or none apply)'
}

Write-Output ''
Write-Output "Summary: pass=$($script:PassCount) warn=$($script:WarnCount) fail=$($script:FailCount) skip=$($script:SkipCount)"
if ($script:FailCount -gt 0) {
    Write-Output 'Agentic OS integrity check failed'
    exit 1
}

Write-Output 'Agentic OS integrity check passed'
