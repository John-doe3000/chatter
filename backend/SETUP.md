#!/bin/bash
# Django Backend Bootstrap Setup Script

# Create and activate virtual environment
python3 -m venv .venv

# Activate on Windows (Git Bash)
source .venv/Scripts/activate

# Activate on Windows (PowerShell) - use this instead if you're in PowerShell:
# .venv\Scripts\Activate.ps1

# Activate on macOS/Linux:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser (optional - for Django admin access)
# python manage.py createsuperuser

# Run the development server
python manage.py runserver

# Server will be available at http://127.0.0.1:8000/
# Admin at http://127.0.0.1:8000/admin/
