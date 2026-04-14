Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Normalize-PathString {
    param([Parameter(Mandatory = $true)][string]$Path)
    if ($Path.StartsWith('\\?\')) { return $Path.Substring(4) }
    return $Path
}

function Join-NormalPath {
    param(
        [Parameter(Mandatory = $true)][string]$Base,
        [Parameter(Mandatory = $true)][string]$Child
    )
    return [System.IO.Path]::Combine((Normalize-PathString $Base), $Child)
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
    $content = Get-Content -Raw -Encoding utf8 -Path $Path
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
        Add-Result -Level $MissingPythonLevel -Message "$Label -- python unavailable"
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
$script:PythonCommand = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $script:PythonCommand) {
    $script:PythonCommand = Get-Command python -ErrorAction SilentlyContinue
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
$commandSyncCheck = Join-NormalPath $root '.agentcortex/tools/check_command_sync.py'
$triggerRegistry = Join-NormalPath $root '.agentcortex/metadata/trigger-registry.yaml'
$triggerCompactIndex = Join-NormalPath $root '.agentcortex/metadata/trigger-compact-index.json'
$lifecycleScenarios = Join-NormalPath $root '.agentcortex/metadata/lifecycle-scenarios.json'
$skillConflictMatrix = Join-NormalPath $root '.agent/rules/skill_conflict_matrix.md'
$agentConfigYaml = Join-NormalPath $root '.agent/config.yaml'
$optionalGuardHook = Join-NormalPath $root '.githooks/pre-commit.guard-ssot.sample'

$requiredFiles = @(
    (Join-NormalPath $workflowsDir 'hotfix.md'),
    (Join-NormalPath $workflowsDir 'worktree-first.md'),
    (Join-NormalPath $workflowsDir 'new-feature.md'),
    (Join-NormalPath $workflowsDir 'medium-feature.md'),
    (Join-NormalPath $workflowsDir 'small-fix.md'),
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
    (Join-NormalPath $workflowsDir 'claude-cli.md'),
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
    (Join-NormalPath $claudeCommandsDir 'claude-cli.md')
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

# Downstream repos receive deploy_brain.* at the repo root (not under installers/).
# Redefine wrapper paths so required_files validation matches the actual layout.
if (-not $isSourceRepo) {
    $rootDeploySh  = Join-NormalPath $root 'deploy_brain.sh'
    $rootDeployPs1 = Join-NormalPath $root 'deploy_brain.ps1'
    $rootDeployCmd = Join-NormalPath $root 'deploy_brain.cmd'
    # Rebuild requiredFiles with updated paths
    $requiredFiles = @(
        (Join-NormalPath $workflowsDir 'hotfix.md'),
        (Join-NormalPath $workflowsDir 'worktree-first.md'),
        (Join-NormalPath $workflowsDir 'new-feature.md'),
        (Join-NormalPath $workflowsDir 'medium-feature.md'),
        (Join-NormalPath $workflowsDir 'small-fix.md'),
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
        (Join-NormalPath $workflowsDir 'claude-cli.md'),
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
}

if ($isSourceRepo) {
    Add-Result -Level 'SKIP' -Message 'claude adapter files -- source repo (created by deploy in downstream)'
    Test-FileGroup -Label 'required framework files present' -Paths $requiredFiles
    $sourceDirs = @(
        $workflowsDir,
        (Join-NormalPath $root '.agents/skills'),
        (Join-NormalPath $root '.agent/skills')
    )
    Test-DirGroup -Label 'required framework directories present' -Paths $sourceDirs
}
else {
    Test-FileGroup -Label 'required framework files present' -Paths $requiredFiles
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
    }

    if (Test-Path -Path $triggerMetadataValidator -PathType Leaf) {
        if (Test-Path -Path $lifecycleScenarios -PathType Leaf) {
            Invoke-PythonCheck -Label 'metadata deep validation' -MissingPythonLevel 'FAIL' -ScriptPath $triggerMetadataValidator -Arguments @('--root', $root)
        }
        else {
            Add-Result -Level 'FAIL' -Message 'metadata deep validation unavailable -- lifecycle scenarios missing'
        }
    }
    else {
        Add-Result -Level 'SKIP' -Message 'metadata deep checks -- CI-only validator not deployed'
    }

    if (Test-Path -Path $triggerCompactIndexGenerator -PathType Leaf) {
        Invoke-PythonCheck -Label 'compact index freshness' -MissingPythonLevel 'FAIL' -ScriptPath $triggerCompactIndexGenerator -Arguments @('--root', $root, '--check')
    }
    else {
        Add-Result -Level 'SKIP' -Message 'compact index freshness -- CI-only generator not deployed'
    }
}
elseif (Test-Path -Path $triggerCompactIndex -PathType Leaf) {
    Add-Result -Level 'FAIL' -Message 'metadata runtime incomplete -- compact index present without trigger registry'
}
else {
    Add-Result -Level 'SKIP' -Message 'metadata checks -- no trigger registry found'
}

Invoke-PythonCheck -Label 'command sync check' -MissingPythonLevel 'FAIL' -ScriptPath $commandSyncCheck -Arguments @('--root', $root)

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

$activeCodexRules = Join-NormalPath $root 'codex/rules/default.rules'
if (-not (Test-Path -Path $activeCodexRules -PathType Leaf)) { $activeCodexRules = $codexRules }
Test-ContainsRegex -Path $activeCodexRules -Pattern 'prefix_rule\(' -SuccessMessage 'codex rules include prefix_rule()' -FailureMessage 'codex rules missing prefix_rule()'
Test-ContainsLiteral -Path $activeCodexRules -Pattern 'docker system prune -a' -SuccessMessage 'codex rules include docker system prune guard' -FailureMessage 'codex rules missing docker system prune guard'
Test-ContainsLiteral -Path $activeCodexRules -Pattern 'chown -R' -SuccessMessage 'codex rules include chown -R guard' -FailureMessage 'codex rules missing chown -R guard'

Test-ContainsLiteral -Path $rootDeploySh -Pattern '.agentcortex/bin/deploy.sh' -SuccessMessage 'deploy_brain.sh references canonical deploy script' -FailureMessage 'deploy_brain.sh missing canonical deploy reference'
Test-ContainsLiteral -Path $rootDeployPs1 -Pattern "'.agentcortex', 'bin', 'deploy.sh'" -SuccessMessage 'deploy_brain.ps1 references canonical deploy script' -FailureMessage 'deploy_brain.ps1 missing canonical deploy reference'
Test-ContainsLiteral -Path $rootDeployCmd -Pattern '.agentcortex\bin\deploy' -SuccessMessage 'deploy_brain.cmd references canonical deploy entrypoint' -FailureMessage 'deploy_brain.cmd missing canonical deploy reference'

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
        $domainDocContent = Get-Content -Path $domainDoc.FullName -Raw -Encoding utf8
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
    if (-not ($deployBlock | Where-Object { $_ -eq '!.agentcortex/context/work/.gitkeep' })) {
        Write-Output '  deploy ignore block missing .gitkeep negation pattern'
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

$readmeZhTw = Join-NormalPath $root 'README_zh-TW.md'
if (Test-Path -Path $readmeZhTw -PathType Leaf) {
    Test-ContainsRegex -Path $readmeZhTw -Pattern '\u6D41\u7A0B\u9A45\u52D5.*AI Agent' -SuccessMessage 'README_zh-TW.md encoding looks healthy' -FailureMessage 'README_zh-TW.md appears mojibaked or re-encoded'
}

$testingProtocolZhTw = Join-NormalPath $root '.agentcortex/docs/TESTING_PROTOCOL_zh-TW.md'
if (Test-Path -Path $testingProtocolZhTw -PathType Leaf) {
    Test-ContainsRegex -Path $testingProtocolZhTw -Pattern '\u6E2C\u8A66\u6559\u6230\u5B88\u5247' -SuccessMessage 'TESTING_PROTOCOL_zh-TW.md encoding looks healthy' -FailureMessage 'TESTING_PROTOCOL_zh-TW.md appears mojibaked or re-encoded'
}

$readmeEn = Join-NormalPath $root 'README.md'
if (Test-Path -Path $readmeEn -PathType Leaf) {
    $params = @{
        Path = $readmeEn
        Pattern = 'Why Agentic OS?'
        SuccessMessage = 'README.md encoding looks healthy'
        FailureMessage = 'README.md appears mojibaked or re-encoded'
    }
    Test-ContainsLiteral @params
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
    Test-ContainsRegex -Path $auditGuardrailsZhTw -Pattern '\u81EA\u52D5\u5316.*Shell Script' -SuccessMessage 'audit-guardrails_zh-TW.md encoding looks healthy' -FailureMessage 'audit-guardrails_zh-TW.md appears mojibaked or re-encoded'
}

$worklogMaxLines = if ($env:WORKLOG_MAX_LINES) { [int]$env:WORKLOG_MAX_LINES } else { 300 }
$worklogMaxKb = if ($env:WORKLOG_MAX_KB) { [int]$env:WORKLOG_MAX_KB } else { 12 }
$activeWorklogWarnThreshold = if ($env:ACTIVE_WORKLOG_WARN_THRESHOLD) { [int]$env:ACTIVE_WORKLOG_WARN_THRESHOLD } else { 8 }
$legacyGateEvidenceCutoff = if ($env:WORKLOG_GATE_EVIDENCE_LEGACY_CUTOFF) { $env:WORKLOG_GATE_EVIDENCE_LEGACY_CUTOFF } else { '2026-03-25' }
$worklogDir = Join-NormalPath $root '.agentcortex/context/work'
if (Test-Path -Path $worklogDir -PathType Container) {
    $worklogs = @(Get-ChildItem -Path $worklogDir -Filter *.md -File -ErrorAction SilentlyContinue)
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

    if ($worklogs.Count -gt $activeWorklogWarnThreshold) {
        Add-Result -Level 'WARN' -Message "active work log count exceeds hygiene threshold ($($worklogs.Count) > $activeWorklogWarnThreshold)"
    }
    else {
        Add-Result -Level 'PASS' -Message 'active work log count is within hygiene threshold'
    }
    # Work Log integrity marker check — detect truncated writes from interrupted sessions
    $worklogTruncated = 0
    foreach ($wl in $worklogs) {
        $wlContent = Get-Content -Path $wl.FullName -Raw -ErrorAction SilentlyContinue
        if (-not $wlContent) { continue }
        # A well-formed work log must have at least a Branch header and one ## section.
        # Accept both the current "- Branch:" header and any legacy bolded variant.
        $hasBranchHeader = $wlContent -match '(?m)^- (\*\*Branch\*\*|Branch):'
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
    # Legal phase transitions for gate evidence validation
    $legalTransitions = @{
        'bootstrap' = @('plan')
        'plan'      = @('implement')
        'implement' = @('review','test','ship')
        'review'    = @('implement','test','ship')
        'test'      = @('handoff','ship','implement')
        'handoff'   = @('ship','retro')
        'ship'      = @()
    }
    foreach ($wl in $worklogs) {
        $content = Get-Content -Path $wl.FullName -Raw -ErrorAction SilentlyContinue
        if (-not $content) { continue }
        $createdDate = ''
        $createdDateMatch = [regex]::Match($content, '(?m)^- \*\*Created Date\*\*:\s*(.+)$')
        if ($createdDateMatch.Success) {
            $createdDate = $createdDateMatch.Groups[1].Value.Trim()
        }
        $isLegacyGateEvidenceLog = $createdDate -and $createdDate -lt $legacyGateEvidenceCutoff
        if ($content -notmatch '(?m)^- (`Current Phase`|Current Phase):') { $phaseFieldMissing++ }
        if ($content -notmatch '(?m)^- (`Checkpoint SHA`|Checkpoint SHA):') { $checkpointMissing++ }
        if ($content -notmatch '(?m)^## Gate Evidence') {
            if ($isLegacyGateEvidenceLog) {
                $legacyGateEvidenceMissing++
            } else {
                $gateEvidenceMissing++
            }
        } elseif ($content -notmatch '(?m)^- Gate:.*Verdict:') {
            if ($isLegacyGateEvidenceLog) {
                $legacyGateEvidenceMissing++
            } else {
                $gateEvidenceMissing++
            }
        } else {
            # Parse gate receipts and verify phase progression
            $gates = @([regex]::Matches($content, '(?m)^- Gate:\s*(\w+)\s*\|') | ForEach-Object { $_.Groups[1].Value })
            if ($gates.Count -ge 2) {
                for ($i = 1; $i -lt $gates.Count; $i++) {
                    $prev = $gates[$i - 1]
                    $curr = $gates[$i]
                    $allowed = $legalTransitions[$prev]
                    if ($allowed -and ($curr -notin $allowed)) {
                        Write-Output "  illegal gate progression in $($wl.Name): ${prev}->${curr}"
                        $gateProgressionIllegal++
                        break
                    }
                }
            }
        }
        if ($content -notmatch '(?m)^## Phase Summary') { $phaseSummaryMissing++ }
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
                Where-Object { $_.Name -notmatch '^_' } |
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

# Document lifecycle bloat checks
$globalLessonsMax = if ($env:GLOBAL_LESSONS_MAX) { [int]$env:GLOBAL_LESSONS_MAX } else { 20 }
if (Test-Path -Path $currentStatePath -PathType Leaf) {
    $lessonsCount = @([regex]::Matches($csContent, '(?m)^- \[Category:') | Measure-Object).Count
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

Write-Output ''
Write-Output "Summary: pass=$($script:PassCount) warn=$($script:WarnCount) fail=$($script:FailCount) skip=$($script:SkipCount)"
if ($script:FailCount -gt 0) {
    Write-Output 'Agentic OS integrity check failed'
    exit 1
}

Write-Output 'Agentic OS integrity check passed'
