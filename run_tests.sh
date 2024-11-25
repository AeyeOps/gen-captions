#!/bin/bash

# Activate the virtual environment
source venv/bin/activate

# Run pytest
python -m pytest

# Deactivate the virtual environment
deactivate
