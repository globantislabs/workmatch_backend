#!/bin/bash
# =============================================================================
#  WorkMatch — Quick Update Script (no wipe, just pull latest & restart)
#  Run on Ubuntu server: bash update.sh
# =============================================================================
set -euo pipefail

FRONTEND_DIR="/var/www/workmatch_frontend"
BACKEND_DIR="/opt/workmatch_backend"

GREEN='\033[0;32m'; CYAN='\033[0;36m'; NC='\033[0m'
log()  { echo -e "${GREEN}[✔]${NC} $1"; }
info() { echo -e "${CYAN}[→]${NC} $1"; }

# Fix git safe directory for sudo
sudo git config --global --add safe.directory "$FRONTEND_DIR" 2>/dev/null || true
sudo git config --global --add safe.directory "$BACKEND_DIR"  2>/dev/null || true

echo ""
echo "============================================================"
echo "   WorkMatch — Quick Update"
echo "============================================================"

# Frontend
info "Pulling latest frontend..."
sudo git -C "$FRONTEND_DIR" fetch origin
sudo git -C "$FRONTEND_DIR" reset --hard origin/main
sudo chown -R www-data:www-data "$FRONTEND_DIR"
log "Frontend updated"

# Backend
info "Pulling latest backend..."
sudo git -C "$BACKEND_DIR" fetch origin
sudo git -C "$BACKEND_DIR" reset --hard origin/main

info "Updating Python dependencies..."
sudo "$BACKEND_DIR/.venv/bin/pip" install -r "$BACKEND_DIR/requirements.txt" -q

sudo chown -R www-data:www-data "$BACKEND_DIR"
sudo chmod +x "$BACKEND_DIR/pocketbase"
sudo chmod 600 "$BACKEND_DIR/.env"
log "Backend updated"

# Restart services
info "Restarting services..."
sudo systemctl restart workmatch_backend
sleep 2
sudo systemctl reload nginx
log "Services restarted"

echo ""
echo "============================================================"
echo -e "${GREEN}   ✔  Update complete!${NC}"
echo "============================================================"
sudo systemctl status workmatch_pocketbase --no-pager -l | head -5
sudo systemctl status workmatch_backend    --no-pager -l | head -5
echo ""
