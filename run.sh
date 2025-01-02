#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Configuration
PROJECT_DIR="django_project"
VENV_DIR="venv"
MANAGE_PY="manage.py"
PORT=8000
COMMAND_NAME="send_broadcasts"

# Function to check if the server is running
is_server_running() {
    lsof -i :$PORT | grep LISTEN > /dev/null
    return $?
}

# Function to check if the command is already running
is_command_running() {
    pgrep -f "$MANAGE_PY $COMMAND_NAME" > /dev/null
    return $?
}

# Navigate to the Django project directory
if [ ! -d "$PROJECT_DIR" ]; then
    echo "Error: Django project directory $PROJECT_DIR not found. Exiting."
    exit 1
fi
cd "$PROJECT_DIR"

# Activate the virtual environment
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
elif [ -f "$VENV_DIR/Scripts/activate" ]; then
    source "$VENV_DIR/Scripts/activate"
else
    echo "Error: Could not activate the virtual environment."
    exit 1
fi

# Check if the server is running
if is_server_running; then
    echo "Django server is running on port $PORT. Stopping it..."
    # Kill the server process
    SERVER_PID=$(lsof -t -i :$PORT)
    kill -9 "$SERVER_PID"
    echo "Server stopped."
else
    echo "Django server is not running."
fi

# Start the server
echo "Starting the Django server..."
if [ ! -f "$MANAGE_PY" ]; then
    echo "Error: $MANAGE_PY not found in $PROJECT_DIR. Exiting."
    exit 1
fi
python "$MANAGE_PY" runserver &

# Wait a moment for the server to start
sleep 5

# Check if the 'send_broadcasts' command is already running
if is_command_running; then
    echo "An instance of '$COMMAND_NAME' is already running."
else
  # Run the custom Django management command
  echo "Running the '$COMMAND_NAME' Django command..."
  python "$MANAGE_PY" $COMMAND_NAME &
fi

# Deactivate the virtual environment
deactivate

echo "Script completed successfully."
