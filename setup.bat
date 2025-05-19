@echo off
REM Setup script for kodomo-shokudo-survey (Windows version)

echo === こども食堂アンケート集計システム セットアップ ===
echo.

REM Check Python version
echo Checking Python version...
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python not found. Please install Python 3.8 or higher.
    exit /b 1
)

for /f "tokens=*" %%a in ('python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"') do set PYTHON_VERSION=%%a
echo Python version: %PYTHON_VERSION%

REM Create virtual environment
echo.
echo Creating virtual environment...
if exist venv (
    echo Virtual environment already exists.
) else (
    python -m venv venv
    echo Virtual environment created.
)

REM Activate virtual environment
echo.
echo Activating virtual environment...
call venv\Scripts\activate
echo Virtual environment activated.

REM Install dependencies
echo.
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
echo Dependencies installed.

REM Create .env file from template if it doesn't exist
echo.
echo Setting up environment variables...
if exist .env (
    echo .env file already exists.
) else (
    copy .env.template .env
    echo .env file created from template.
    echo Please edit the .env file to add your API keys and other settings.
)

REM Create directories if they don't exist
echo.
echo Creating necessary directories...
if not exist static\img mkdir static\img
echo Directories created.

REM Final instructions
echo.
echo === Setup Complete ===
echo.
echo To run the application:
echo   1. Edit the .env file to add your API keys and settings
echo   2. Activate the virtual environment (if not already activated):
echo      venv\Scripts\activate
echo   3. Run the application:
echo      python app.py
echo.
echo To run tests:
echo   python test_app.py
echo.
echo To deploy to Vercel:
echo   1. Install Vercel CLI: npm install -g vercel
echo   2. Run: vercel
echo.
echo Thank you for using こども食堂アンケート集計システム!

REM Keep the window open
pause
