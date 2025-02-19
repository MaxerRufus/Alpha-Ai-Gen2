#!/bin/bash
pip install --upgrade pip
pip install -r requirements.txt
python -m gunicorn wsgi:app --bind 0.0.0.0:$PORT