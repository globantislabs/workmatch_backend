#!/bin/bash
set -e

# --- Configuration: UPDATE THESE PATHS ---
# Directory where your git repo is cloned
REPO_DIR="/opt/workmatch_backend_repo"
# Directory where your backend is actually running
DEST="/opt/workmatch_backend"
USER="www-data"

echo "--- Starting Backend Deployment ---"

# 1. Update from Git
echo ">>> Pulling latest code..."
cd "$REPO_DIR"
git pull origin main

# 2. Sync to production
# CRITICAL: Exclude database and migrations to ensure existing data is never touched
echo ">>> Syncing files to $DEST..."
sudo rsync -av --delete \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='pb_data' \
    --exclude='pb_migrations' \
    --exclude='*.log' \
    "$REPO_DIR/" "$DEST/"

# 3. Update Dependencies
echo ">>> Updating dependencies..."
# Uses python -m pip to ensure it uses the correct venv
sudo -u "$USER" "$DEST/.venv/bin/python" -m pip install -r "$DEST/requirements.txt"

# 4. Fix Permissions
echo ">>> Fixing permissions..."
sudo chown -R "$USER:$USER" "$DEST"
sudo find "$DEST" -type d -exec chmod 755 {} \;
sudo find "$DEST" -type f -exec chmod 644 {} \;

# 5. Restart Backend Service
echo ">>> Restarting backend service..."
sudo systemctl restart workmatch_backend

echo "--- Backend Deployment Finished Successfully ---"
