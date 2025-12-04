@echo off
REM Windows GPU Installation Script
REM Run this in Command Prompt or PowerShell to install all dependencies safely

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║                                                               ║
echo ║  Telugu Actor Face Dataset Builder - Windows GPU Setup       ║
echo ║                                                               ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

REM Check Python version
echo Checking Python version...
python --version
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10 first.
    pause
    exit /b 1
)

REM Check for venv
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate venv
echo Activating virtual environment...
call venv\Scripts\activate.bat

if errorlevel 1 (
    echo ERROR: Could not activate virtual environment
    pause
    exit /b 1
)

echo Virtual environment activated.
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo WARNING: pip upgrade had issues, continuing anyway...
)

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║ Installing Core Dependencies                                  ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

REM Step 1: Install numpy first
echo [1/6] Installing numpy (critical dependency)...
pip install numpy==1.24.3
if errorlevel 1 (
    echo ERROR: Failed to install numpy
    pause
    exit /b 1
)

REM Step 2: Install OpenCV
echo [2/6] Installing OpenCV...
pip install opencv-python==4.8.1.78
if errorlevel 1 (
    echo ERROR: Failed to install OpenCV
    pause
    exit /b 1
)

REM Step 3: Uninstall CPU ONNX Runtime if exists
echo [3/6] Checking for CPU-only ONNX Runtime...
pip uninstall onnxruntime -y
echo.

REM Step 4: Install GPU ONNX Runtime
echo [4/6] Installing ONNX Runtime GPU (this is important for GPU support)...
pip install onnxruntime-gpu==1.17.1
if errorlevel 1 (
    echo WARNING: GPU version failed. Trying CPU-only version...
    echo Note: GPU acceleration will NOT be available
    pip install onnxruntime==1.17.1
)

REM Step 5: Install InsightFace
echo [5/6] Installing InsightFace (face detection)...
pip install insightface==0.7.3
if errorlevel 1 (
    echo ERROR: Failed to install InsightFace
    pause
    exit /b 1
)

REM Step 6: Install remaining dependencies
echo [6/6] Installing remaining dependencies...
pip install -r requirements-windows-gpu.txt
if errorlevel 1 (
    echo WARNING: Some packages had issues. Checking what's available...
)

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║ Installation Complete!                                        ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

echo Testing installation...
python test_system.py

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║ Setup Summary                                                  ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.
echo Virtual environment is activated: %VIRTUAL_ENV%
echo.
echo Next steps:
echo   1. Review test output above for any errors
echo   2. Create .env file with your TMDb API key:
echo      echo TMDB_API_KEY=your_key_here > .env
echo   3. Start building datasets:
echo      python run.py "Prabhas"
echo.
echo For Windows GPU troubleshooting:
echo   Read WINDOWS_GPU_GUIDE.md
echo.
pause
