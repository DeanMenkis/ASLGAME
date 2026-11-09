@echo off
rem Double-click to play. The first run sets everything up, which takes a few minutes.
rem Windows support is untested.
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo First run: installing Python and the game's libraries. This only happens once.
  set "PATH=%USERPROFILE%\.local\bin;%PATH%"
  where uv >nul 2>nul || powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  uv venv --python 3.11 .venv || goto fail
  uv pip install --python .venv\Scripts\python.exe -r requirements.txt || goto fail
)
.venv\Scripts\python.exe -m aslgame || goto fail
exit /b 0
:fail
pause
exit /b 1
