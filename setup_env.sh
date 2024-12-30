#!/bin/bash

# Check if venv directory exists
if [ ! -d "venv" ]; then
    python -m venv venv
    source ./venv/bin/activate
    # Upgrade pip to the latest version
    venv/bin/pip install --upgrade pip
    # Run pip install to install dependencies
    venv/bin/pip install -r requirements.txt
    echo "Virtual environment 'venv' created, pip upgraded, and dependencies installed."
else
    echo "Virtual environment 'venv' already exists."
    # Upgrade pip to the latest version
    venv/bin/pip install --upgrade pip
fi
