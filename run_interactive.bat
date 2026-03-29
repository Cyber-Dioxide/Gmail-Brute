@echo off
:: ============================================================
:: SMTP Tester Pro v2.0 - Interactive Mode
:: ============================================================
:: Launches SMTP Tester in interactive mode
:: ============================================================

setlocal enabledelayedexpansion
title SMTP Tester Pro - Interactive Mode

:: Activate virtual environment if exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

cls
python smtp_tester.py
echo.
echo Press any key to exit...
pause >nul
