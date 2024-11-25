:: filepath: E:/dev/gen-captions/setup_env.bat
@echo off
REM Check if venv directory exists
IF NOT EXIST "venv" (
    echo Create a new 'venv' virtual environment...
    python -m venv venv
    echo Activate the virtual environment
    venv\Scripts\activate
    echo Upgrade pip to the latest version...
    python -m pip install --upgrade pip
    echo Run pip install to install dependencies ...
    pip.exe install -r requirements.txt
    echo Virtual environment 'venv' created, pip upgraded, and dependencies installed.
) ELSE (
    REM ...existing code...
    echo Virtual environment 'venv' already exists.
    echo Activate the virtual environment
    venv\Scripts\activate
    echo Upgrade pip to the latest version...
    python -m pip install --upgrade pip
)