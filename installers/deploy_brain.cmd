@echo off
setlocal
set "SCRIPT_DIR=%~dp0"

:: deploy_brain.cmd - Windows wrapper dispatcher.
::
:: DESIGN: The WRAPPER (deploy_brain.ps1 / deploy_brain.sh) owns install-vs-update
:: (NVM-style) routing. The canonical .agentcortex\bin\deploy.* is the IMPLEMENTATION
:: that the wrapper calls - it has NO install-vs-update dispatch and an aggressive
:: self-deploy guard. Therefore this .cmd MUST ALWAYS delegate to its sibling wrapper
:: and MUST NOT jump to canonical deploy.* directly (doing so trips the self-deploy
:: guard on `deploy_brain.cmd .` from an installed project root).
::
:: Prefer deploy_brain.ps1: it resolves a real Git Bash and skips the WindowsApps
:: bash.exe WSL placeholder. Fall back to deploy_brain.sh via bash only when the
:: PowerShell wrapper is unavailable.
::
:: NOTE: %~dp0 is captured into SCRIPT_DIR up front because the arg-parse loop below
:: uses SHIFT, and SHIFT rewrites %0 - so %~dp0 would no longer point at this script.

if exist "%SCRIPT_DIR%deploy_brain.ps1" goto run_wrapper_ps1
if exist "%SCRIPT_DIR%deploy_brain.sh" goto run_wrapper_bash

echo [ERROR] No deploy wrapper found alongside this script (expected deploy_brain.ps1 or deploy_brain.sh).
exit /b 1

:run_wrapper_ps1
:: PowerShell -File binds unrecognized --flags to the first positional [string]$Target,
:: which would corrupt --dry-run / --source, so translate cmd-style args into the PS1
:: wrapper's typed parameters. deploy supports only --dry-run and --source; any other
:: token (incl. the validate-only --no-python) falls through to the target, matching
:: deploy_brain.sh / deploy.sh behavior.
set "ACX_DRYRUN="
set "ACX_SOURCE_ARG="
set "ACX_TARGET="
:parse_args
if "%~1"=="" goto run_ps1_invoke
if /i "%~1"=="--dry-run" (set "ACX_DRYRUN=-DryRun" & shift & goto parse_args)
if /i "%~1"=="-DryRun" (set "ACX_DRYRUN=-DryRun" & shift & goto parse_args)
if /i "%~1"=="--source" goto take_source
if /i "%~1"=="-Source" goto take_source
set "ACX_TARGET=%~1"
shift
goto parse_args

:take_source
if "%~2"=="" (echo [ERROR] --source requires a value. & exit /b 1)
set "ACX_SOURCE_ARG=-Source ""%~2"""
shift
shift
goto parse_args

:run_ps1_invoke
if not defined ACX_TARGET set "ACX_TARGET=."
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%deploy_brain.ps1" -Target "%ACX_TARGET%" %ACX_SOURCE_ARG% %ACX_DRYRUN%
exit /b %errorlevel%

:run_wrapper_bash
where bash >nul 2>nul
if errorlevel 1 goto no_bash
bash "%SCRIPT_DIR%deploy_brain.sh" %*
exit /b %errorlevel%

:no_bash
echo [ERROR] bash is not installed. Install Git Bash or WSL, or run the PowerShell deployer.
exit /b 1
