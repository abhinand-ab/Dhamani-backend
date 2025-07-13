# Render deploy configuration for Flask
# Use this as your start command in Render settings

gunicorn app:app --bind 0.0.0.0:10000
