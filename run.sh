#!/bin/bash

# Configuration
VENV_DIR="venv"
MANAGE_PY="manage.py"
PORT=8000

# Function to check if the server is running
is_server_running() {
    lsof -i :$PORT | grep LISTEN > /dev/null
    return $?
}


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
    deactivate
    exit 1
fi
python "$MANAGE_PY" runserver &
echo "Django server started on port $PORT."

# Deactivate the virtual environment
deactivate
