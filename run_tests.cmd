@echo off
REM Activate the virtual environment
call venv\Scripts\activate.bat

REM Run pytest
python -m pytest

REM Deactivate the virtual environment
deactivate
