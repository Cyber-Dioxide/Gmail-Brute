@echo off
:: ============================================================
:: SMTP Tester Pro v2.0 - Windows Installation Script
:: ============================================================
:: This script will:
::   1. Check if Python is installed
::   2. Download and install Python if needed
::   3. Install required dependencies
::   4. Launch SMTP Tester
:: ============================================================

setlocal enabledelayedexpansion
title SMTP Tester Pro v2.0 - Installer

:: Colors for output
for /F %%a in ('echo prompt $E^| cmd') do set "ESC=%%a"
set "RED=!ESC![91m"
set "GREEN=!ESC![92m"
set "YELLOW=!ESC![93m"
set "CYAN=!ESC![96m"
set "WHITE=!ESC![97m"
set "RESET=!ESC![0m"

:: ============================================================
:: DISPLAY BANNER
:: ============================================================
cls
echo.
echo  !CYAN!╔══════════════════════════════════════════════════════════════╗!RESET!
echo  !CYAN!║!RESET!  !WHITE!SMTP Tester Pro v2.0!RESET! - Windows Installer         !CYAN!║!RESET!
echo  !CYAN!║!RESET!                                                              !CYAN!║!RESET!
echo  !CYAN!║!RESET!  !YELLOW!•!RESET! Auto Python Install    !YELLOW!•!RESET! Auto Dependencies    !CYAN!║!RESET!
echo  !CYAN!║!RESET!  !YELLOW!•!RESET! Easy Setup            !YELLOW!•!RESET! One-Click Start      !CYAN!║!RESET!
echo  !CYAN!╚══════════════════════════════════════════════════════════════╝!RESET!
echo.

:: ============================================================
:: CHECK ADMIN RIGHTS
:: ============================================================
echo !CYAN![*]!RESET! Checking administrator privileges...
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo !YELLOW![!] Warning: Not running as administrator!RESET!
    echo !YELLOW![!] Python installation may require admin rights!RESET!
    echo.
    pause
) else (
    echo !GREEN![+] Running with administrator privileges!RESET!
)
echo.

:: ============================================================
:: CHECK PYTHON INSTALLATION
:: ============================================================
echo !CYAN![*]!RESET! Checking Python installation...

:: Check Python 3
python --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo !GREEN![+] Python !PYTHON_VERSION! is installed!RESET!
    set PYTHON_CMD=python
    goto :python_found
)

:: Check Python3 alias
python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%i in ('python3 --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo !GREEN![+] Python !PYTHON_VERSION! is installed!RESET!
    set PYTHON_CMD=python3
    goto :python_found
)

:: Check common installation paths
set "PYTHON_PATHS=C:\Python312 C:\Python311 C:\Python310 C:\Python39 C:\Python38 C:\Program Files\Python312 C:\Program Files\Python311 C:\Program Files\Python310 C:\Program Files\Python39 C:\Program Files\Python38 C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312 C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311 C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python310 C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python39 C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python38"

for %%p in (%PYTHON_PATHS%) do (
    if exist "%%p\python.exe" (
        echo !GREEN![+] Found Python at: %%p!RESET!
        set PYTHON_CMD="%%p\python.exe"
        goto :python_found
    )
)

:: Python not found - download and install
echo !YELLOW![!] Python not found!RESET!
echo.
echo !CYAN![*]!RESET! Would you like to download and install Python 3.12?
echo.
set /p INSTALL_PYTHON="!WHITE!Install Python? (Y/N): !RESET!"
if /i "%INSTALL_PYTHON%" neq "Y" (
    echo !RED![!] Cannot continue without Python. Exiting...!RESET!
    pause
    exit /b 1
)

:: ============================================================
:: DOWNLOAD AND INSTALL PYTHON
:: ============================================================
echo.
echo !CYAN![*]!RESET! Downloading Python 3.12...

set PYTHON_INSTALLER=%TEMP%\python_installer.exe
set PYTHON_URL=https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe

:: Use PowerShell to download
powershell -Command "& {Invoke-WebRequest -Uri '!PYTHON_URL!' -OutFile '!PYTHON_INSTALLER!'}"

if not exist "%PYTHON_INSTALLER%" (
    echo !RED![!] Failed to download Python installer!RESET!
    echo !YELLOW![!] Please download manually from: https://www.python.org/downloads/!RESET!
    pause
    exit /b 1
)

echo !GREEN![+] Python installer downloaded!RESET!
echo.
echo !CYAN![*]!RESET! Installing Python...
echo !YELLOW![!] This may take a few minutes...!RESET!

:: Install Python with all features and add to PATH
"%PYTHON_INSTALLER%" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_pip=1

:: Wait for installation to complete
timeout /t 60 /nobreak >nul

:: Clean up installer
del "%PYTHON_INSTALLER%" >nul 2>&1

:: Refresh environment variables
call refreshenv >nul 2>&1

:: Re-check Python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo !GREEN![+] Python installed successfully!RESET!
    set PYTHON_CMD=python
) else (
    echo !RED![!] Python installation may have failed!RESET!
    echo !YELLOW![!] Please restart this script after installing Python manually.!RESET!
    pause
    exit /b 1
)

:python_found
echo.

:: ============================================================
:: CREATE VIRTUAL ENVIRONMENT (OPTIONAL)
:: ============================================================
echo !CYAN![*]!RESET! Would you like to create a virtual environment?
echo    !WHITE!(Recommended for isolated installation)!RESET!
echo.
set /p CREATE_VENV="!WHITE!Create virtual environment? (Y/N): !RESET!"

if /i "%CREATE_VENV%" equ "Y" (
    echo.
    echo !CYAN![*]!RESET! Creating virtual environment...
    
    %PYTHON_CMD% -m venv venv
    
    if exist "venv\Scripts\activate.bat" (
        call venv\Scripts\activate.bat
        echo !GREEN![+] Virtual environment created and activated!RESET!
        set PYTHON_CMD=venv\Scripts\python.exe
        set PIP_CMD=venv\Scripts\pip.exe
    ) else (
        echo !YELLOW![!] Failed to create virtual environment, using system Python!RESET!
        set PIP_CMD=pip
    )
) else (
    set PIP_CMD=pip
)

echo.

:: ============================================================
:: UPGRADE PIP
:: ============================================================
echo !CYAN![*]!RESET! Upgrading pip...
%PYTHON_CMD% -m pip install --upgrade pip --quiet >nul 2>&1
echo !GREEN![+] pip upgraded!RESET!
echo.

:: ============================================================
:: INSTALL DEPENDENCIES
:: ============================================================
echo !CYAN!════════════════════════════════════════════════════════════!RESET!
echo !CYAN![*]!RESET! Installing Dependencies...
echo !CYAN!════════════════════════════════════════════════════════════!RESET!
echo.

:: Check if requirements.txt exists
if exist "requirements.txt" (
    echo !CYAN![*]!RESET! Installing from requirements.txt...
    %PYTHON_CMD% -m pip install -r requirements.txt --quiet
    
    if %errorlevel% equ 0 (
        echo !GREEN![+] Dependencies installed successfully!RESET!
    ) else (
        echo !YELLOW![!] Some dependencies may have failed to install!RESET!
        echo !CYAN![*]!RESET! Trying individual packages...
    )
)

:: Install core packages individually
echo.
echo !CYAN![*]!RESET! Installing core packages...

:: Install rich
echo    Installing rich...
%PYTHON_CMD% -m pip install rich --quiet >nul 2>&1
if %errorlevel% equ 0 (
    echo    !GREEN!✓!RESET! rich installed
) else (
    echo    !RED!✗!RESET! rich failed
)

:: Install PySocks
echo    Installing PySocks...
%PYTHON_CMD% -m pip install PySocks --quiet >nul 2>&1
if %errorlevel% equ 0 (
    echo    !GREEN!✓!RESET! PySocks installed
) else (
    echo    !RED!✗!RESET! PySocks failed
)

:: Install dnspython (optional)
echo    Installing dnspython...
%PYTHON_CMD% -m pip install dnspython --quiet >nul 2>&1
if %errorlevel% equ 0 (
    echo    !GREEN!✓!RESET! dnspython installed
) else (
    echo    !YELLOW!○!RESET! dnspython skipped (optional)
)

echo.

:: ============================================================
:: VERIFY INSTALLATION
:: ============================================================
echo !CYAN!════════════════════════════════════════════════════════════!RESET!
echo !CYAN![*]!RESET! Verifying Installation...
echo !CYAN!════════════════════════════════════════════════════════════!RESET!
echo.

%PYTHON_CMD% -c "import rich; print('    [✓] rich:', rich.__version__)" 2>nul
if %errorlevel% neq 0 echo    [✗] rich: NOT INSTALLED

%PYTHON_CMD% -c "import socks; print('    [✓] PySocks: OK')" 2>nul
if %errorlevel% neq 0 echo    [✗] PySocks: NOT INSTALLED

%PYTHON_CMD% -c "import dns; print('    [✓] dnspython: OK')" 2>nul
if %errorlevel% neq 0 echo    [○] dnspython: NOT INSTALLED (optional)

echo.

:: ============================================================
:: CREATE SAMPLE DATA FILES
:: ============================================================
echo !CYAN![*]!RESET! Checking data files...

if not exist "data" mkdir data

:: Create sample emails.txt
if not exist "data\emails.txt" (
    echo !YELLOW![*]!RESET! Creating sample emails.txt...
    (
        echo # Sample Email List
        echo # One email per line, lines starting with # are ignored
        echo test@example.com
        echo user@gmail.com
    ) > data\emails.txt
    echo    !GREEN!✓!RESET! Created data\emails.txt
)

:: Create sample passwords.txt
if not exist "data\passwords.txt" (
    echo !YELLOW![*]!RESET! Creating sample passwords.txt...
    (
        echo # Sample Password List
        echo # One password per line
        echo password123
        echo 12345678
        echo qwerty
        echo letmein
    ) > data\passwords.txt
    echo    !GREEN!✓!RESET! Created data\passwords.txt
)

:: Create sample proxies.txt
if not exist "data\proxies.txt" (
    echo !YELLOW![*]!RESET! Creating sample proxies.txt...
    (
        echo # Sample Proxy List
        echo # Format: host:port or protocol://host:port
        echo # SOCKS5 examples:
        echo # 127.0.0.1:1080
        echo # socks5://127.0.0.1:1080
        echo # With auth: socks5://host:port:user:pass
    ) > data\proxies.txt
    echo    !GREEN!✓!RESET! Created data\proxies.txt
)

:: Create results directory
if not exist "results" mkdir results

echo.

:: ============================================================
:: CREATE QUICK START SCRIPTS
:: ============================================================
echo !CYAN![*]!RESET! Creating quick start scripts...

:: Create run_interactive.bat
(
    echo @echo off
    echo title SMTP Tester Pro - Interactive Mode
    echo if exist "venv\Scripts\activate.bat" call venv\Scripts\activate.bat
    echo python smtp_tester.py
    echo echo.
    echo echo Press any key to exit...
    echo pause ^>nul
) > run_interactive.bat
echo    !GREEN!✓!RESET! Created run_interactive.bat

:: Create run_quick.bat
(
    echo @echo off
    echo title SMTP Tester Pro - Quick Start
    echo if exist "venv\Scripts\activate.bat" call venv\Scripts\activate.bat
    echo echo Starting SMTP Tester Pro...
    echo echo.
    echo set /p HOST="Enter SMTP Host: "
    echo set /p PORT="Enter SMTP Port [587]: "
    echo if "%%PORT%%"=="" set PORT=587
    echo python smtp_tester.py -H %%HOST%% -P %%PORT%% -e data\emails.txt -p data\passwords.txt
    echo echo.
    echo echo Press any key to exit...
    echo pause ^>nul
) > run_quick.bat
echo    !GREEN!✓!RESET! Created run_quick.bat

echo.

:: ============================================================
:: DISPLAY SUCCESS MESSAGE
:: ============================================================
echo.
echo  !GREEN!╔══════════════════════════════════════════════════════════════╗!RESET!
echo  !GREEN!║!RESET!           !WHITE!Installation Complete!!RESET!                          !GREEN!║!RESET!
echo  !GREEN!╠══════════════════════════════════════════════════════════════╣!RESET!
echo  !GREEN!║!RESET!                                                              !GREEN!║!RESET!
echo  !GREEN!║!RESET!  !WHITE!Available Commands:!RESET!                                        !GREEN!║!RESET!
echo  !GREEN!║!RESET!                                                              !GREEN!║!RESET!
echo  !GREEN!║!RESET!  !CYAN!run_interactive.bat!RESET!    - Start interactive mode        !GREEN!║!RESET!
echo  !GREEN!║!RESET!  !CYAN!run_quick.bat!RESET!          - Quick start with prompts      !GREEN!║!RESET!
echo  !GREEN!║!RESET!  !CYAN!python smtp_tester.py --help!RESET! - Show all options         !GREEN!║!RESET!
echo  !GREEN!║!RESET!                                                              !GREEN!║!RESET!
echo  !GREEN!║!RESET!  !WHITE!Sample Files:!RESET!                                           !GREEN!║!RESET!
echo  !GREEN!║!RESET!    !YELLOW!data\emails.txt!RESET!     - Add your email list here      !GREEN!║!RESET!
echo  !GREEN!║!RESET!    !YELLOW!data\passwords.txt!RESET!  - Add your password list here   !GREEN!║!RESET!
echo  !GREEN!║!RESET!    !YELLOW!data\proxies.txt!RESET!    - Add proxies here (optional)   !GREEN!║!RESET!
echo  !GREEN!║!RESET!                                                              !GREEN!║!RESET!
echo  !GREEN!╚══════════════════════════════════════════════════════════════╝!RESET!
echo.

:: ============================================================
:: ASK TO START
:: ============================================================
set /p START_NOW="!WHITE!Start SMTP Tester now? (Y/N): !RESET!"
if /i "%START_NOW%" equ "Y" (
    echo.
    echo !CYAN!════════════════════════════════════════════════════════════!RESET!
    echo !CYAN![*]!RESET! Launching SMTP Tester Pro...
    echo !CYAN!════════════════════════════════════════════════════════════!RESET!
    echo.
    %PYTHON_CMD% smtp_tester.py
)

echo.
echo !WHITE!Thank you for using SMTP Tester Pro!!RESET!
echo.
pause
exit /b 0
