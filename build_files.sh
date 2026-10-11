#!/bin/bash
# Vercel Build Script for MoneyMate Django Application
echo "Installing Python dependencies..."
python3 -m pip install -r requirements.txt

echo "Collecting static files with WhiteNoise..."
python3 manage.py collectstatic --noinput --clear
