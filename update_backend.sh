#!/bin/bash
set -e

# Configuration
# The folder where you keep your git clone of the backend
REPO_DIR="/opt/workmatch_backend_repo"
# The production directory where your backend runs
DEST="/opt/workmatch_backend"
USER="www-data"

echo "--- Starting Backend Update ---"

# 1. Pull latest code from Git
echo "Pulling latest code from Git..."
cd "$REPO_DIR"
git pull origin main

# 2. Sync files to production directory
# CRITICAL: Exclude pb_data and pb_migrations to keep database safe
echo "Syncing code to $DEST..."
sudo rsync -av --delete \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='pb_data' \
    --exclude='pb_migrations' \
    --exclude='*.log' \
    "$REPO_DIR/" "$DEST/"

# 3. Update dependencies
echo "Updating Python dependencies..."
sudo -u "$USER" "$DEST/.venv/bin/pip" install -r "$DEST/requirements.txt"

# 4. Fix permissions
echo "Updating permissions..."
sudo chown -R "$USER:$USER" "$DEST"
sudo find "$DEST" -type d -exec chmod 755 {} \;
sudo find "$DEST" -type f -exec chmod 644 {} \;

# 5. Restart the backend service
echo "Restarting backend service..."
sudo systemctl restart workmatch_backend

echo "--- Backend Update Complete! ---"
