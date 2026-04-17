@echo off
setlocal

:: When deployed to installers\, canonical deploy is one level up.
:: Prefer the PowerShell wrapper on Windows because it resolves a real Git Bash
:: path and avoids the WindowsApps bash.exe WSL placeholder.
if exist "%~dp0..\.agentcortex\bin\deploy.ps1" goto run_canonical_ps1

:: Try canonical deploy via bash
if exist "%~dp0..\.agentcortex\bin\deploy.sh" goto run_canonical_bash

:: Bootstrap: canonical not found, prefer the PowerShell wrapper first.
if exist "%~dp0deploy_brain.ps1" goto run_bootstrap_ps1
if exist "%~dp0deploy_brain.sh" goto run_bootstrap_bash

echo [ERROR] Canonical deploy implementation not found and cannot bootstrap.
exit /b 1

:run_canonical_ps1
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\.agentcortex\bin\deploy.ps1" %*
exit /b %errorlevel%

:run_canonical_bash
where bash >nul 2>nul
if errorlevel 1 goto no_bash
bash "%~dp0..\.agentcortex\bin\deploy.sh" %*
exit /b %errorlevel%

:run_bootstrap_bash
where bash >nul 2>nul
if errorlevel 1 goto run_bootstrap_ps1
bash "%~dp0deploy_brain.sh" %*
exit /b %errorlevel%

:run_bootstrap_ps1
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy_brain.ps1" %*
exit /b %errorlevel%

:no_bash
echo [ERROR] bash is not installed. Install Git Bash or WSL, or run the PowerShell deployer.
exit /b 1
