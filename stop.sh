#!/bin/bash

# Stop Django Development Server and Management Commands
set -e  # Exit immediately if a command exits with a non-zero status

echo "Stopping Django server and management commands..."

# Function to kill processes based on a search string
kill_processes() {
    local SEARCH_TERM=$1
    echo "Searching for processes containing '$SEARCH_TERM'..."
    PIDS=$(pgrep -f "$SEARCH_TERM")
    if [[ -n "$PIDS" ]]; then
        echo "Found processes with PIDs: $PIDS"
        echo "Stopping processes..."
        kill $PIDS
        echo "Processes stopped successfully."
    else
        echo "No processes found for '$SEARCH_TERM'."
    fi
}

# Kill Django development server processes
kill_processes "manage.py runserver"

# Kill Django send_broadcasts command processes
kill_processes "manage.py broadcast"

echo "All relevant Django processes have been stopped."

exit 0
