@echo off
rem Runs the Kiln CLI from the plugin's own cli\ project via uv (PowerShell / cmd).
where uv >nul 2>nul || (echo kiln: 'uv' not found. Install it from https://docs.astral.sh/uv/ 1>&2 & exit /b 127)
uv run --quiet --project "%~dp0..\cli" python -m kiln %*
