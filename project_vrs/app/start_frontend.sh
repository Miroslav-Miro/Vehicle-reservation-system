#!/bin/sh
echo "Current directory:"
pwd
cd /app/frontend

# Print the working directory after moving
echo "Changed to frontend directory: $(pwd)"
echo "Frontend directory contents:"
ls -la

echo "Starting Angular application..."

npx ng serve --host 0.0.0.0
