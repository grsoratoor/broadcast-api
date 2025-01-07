#!/bin/bash

set -e

# Variables
GITHUB_REPO_URL="https://github.com/grsoratoor/broadcast-api.git"
PROJECT_DIR="broadcast_bot"
VENV_DIR=".venv"
REQUIREMENTS_FILE="requirements.txt"

# Clone the GitHub repository
if [ ! -d "$PROJECT_DIR" ]; then
    echo "Cloning repository from $GITHUB_REPO_URL..."
    git clone "$GITHUB_REPO_URL" "$PROJECT_DIR"
else
    echo "Project directory $PROJECT_DIR already exists. Skipping cloning."
fi

# Navigate to the project directory
cd "$PROJECT_DIR" || { echo "Failed to navigate to $PROJECT_DIR. Exiting."; exit 1; }

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment: $VENV_DIR"
    python3 -m venv "$VENV_DIR"
else
    echo "Virtual environment $VENV_DIR already exists."
fi

# Activate the virtual environment
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
elif [ -f "$VENV_DIR/Scripts/activate" ]; then
    source "$VENV_DIR/Scripts/activate"
else
    echo "Error: Could not activate the virtual environment."
    exit 1
fi

# Install dependencies
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "Installing dependencies from $REQUIREMENTS_FILE..."
    pip install -r "$REQUIREMENTS_FILE"
else
    echo "Error: $REQUIREMENTS_FILE not found."
    deactivate
    exit 1
fi

# Run Django setup commands
echo "Running Django setup..."
python manage.py migrate
python manage.py collectstatic --noinput

# Optionally, create a superuser
read -p "Do you want to create a Django superuser? (y/n): " CREATE_SUPERUSER
if [ "$CREATE_SUPERUSER" = "y" ]; then
    python manage.py createsuperuser
fi


# Deactivate the virtual environment
deactivate

echo "Django project setup completed successfully."
