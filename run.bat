@echo off
setlocal

REM Ensure we're in a Git repository
git rev-parse --is-inside-work-tree >nul 2>&1
IF ERRORLEVEL 1 (
    echo Not a Git repository. Aborting.
    exit /b 1
)

REM Fetch latest remote info
git fetch >nul 2>&1

REM Get current branch
for /f "delims=" %%b in ('git rev-parse --abbrev-ref HEAD') do set CUR_BRANCH=%%b

REM Get count of remote commits ahead of local HEAD
for /f "delims=" %%c in ('git rev-list HEAD..origin/%CUR_BRANCH% --count 2^>nul') do set COMMITS_AHEAD=%%c

IF NOT "%COMMITS_AHEAD%"=="0" (
    echo(
    echo ======================================
    echo WARNING: You are behind origin
    echo Consider running: git pull
    echo ======================================
    echo(
    pause
)

REM Check for uncommitted local changes
git diff-index --quiet HEAD --
IF ERRORLEVEL 1 (
    echo(
    echo ======================================
    echo WARNING: You have uncommitted local changes.
    echo Use git status to review.
    echo ======================================
    echo(
    pause
)

REM Try venv first, then env
set "ACT=.\venv\Scripts\activate.bat"
if not exist "%ACT%" set "ACT=.\env\Scripts\activate.bat"

if exist "%ACT%" (
  echo Activating: %ACT%
  call "%ACT%"
) else (
  echo No .\venv or .\env found. Using system Python.
  REM If you want to fail instead, uncomment the next line:
  REM exit /b 1
)

echo Launching Codiak Streamlit
streamlit run app.py

endlocal