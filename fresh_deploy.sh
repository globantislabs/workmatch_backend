#!/bin/bash
# =============================================================================
#  WorkMatch — Full Fresh Deployment Script
#  Run on Ubuntu server as a user with sudo privileges
#  Usage:  bash fresh_deploy.sh
# =============================================================================
set -euo pipefail

# ── CONFIGURATION — edit these before running ────────────────────────────────
FRONTEND_REPO="https://github.com/globantislabs/workmatch_frontend.git"
BACKEND_REPO="https://github.com/globantislabs/workmatch_backend.git"

FRONTEND_DIR="/var/www/workmatch_frontend"
BACKEND_DIR="/opt/workmatch_backend"

DOMAIN_FRONTEND="theworkmatch.com"          # main site
DOMAIN_BACKEND="admin.theworkmatch.com"     # admin / API

PB_ADMIN_EMAIL="admin@workmatch.com"
PB_ADMIN_PASSWORD="admin123456"   # CHANGE THIS

FASTAPI_PORT=8000
POCKETBASE_PORT=8090
# ─────────────────────────────────────────────────────────────────────────────

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
log()  { echo -e "${GREEN}[✔]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
info() { echo -e "${CYAN}[→]${NC} $1"; }
err()  { echo -e "${RED}[✘]${NC} $1"; exit 1; }

echo ""
echo "============================================================"
echo "   WorkMatch — Fresh Deployment"
echo "   Frontend : $DOMAIN_FRONTEND"
echo "   Backend  : $DOMAIN_BACKEND"
echo "============================================================"
echo ""

# ── STEP 1: System packages ───────────────────────────────────────────────────
info "Updating system and installing packages..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    nginx python3 python3-pip python3-venv git curl rsync \
    certbot python3-certbot-nginx ufw
log "Packages installed"

# ── STEP 2: Stop & remove old services ───────────────────────────────────────
info "Stopping and removing old services..."

for SVC in workmatch workmatch_backend workmatch_fastapi pocketbase workmatch_pocketbase; do
    if systemctl is-active --quiet "$SVC" 2>/dev/null; then
        sudo systemctl stop "$SVC"
        warn "Stopped service: $SVC"
    fi
    if systemctl is-enabled --quiet "$SVC" 2>/dev/null; then
        sudo systemctl disable "$SVC"
        warn "Disabled service: $SVC"
    fi
    if [ -f "/etc/systemd/system/$SVC.service" ]; then
        sudo rm -f "/etc/systemd/system/$SVC.service"
        warn "Removed unit file: $SVC.service"
    fi
done

sudo systemctl daemon-reload
log "Old services cleaned up"

# ── STEP 3: Remove old nginx configs ─────────────────────────────────────────
info "Removing old Nginx configs..."
sudo rm -f /etc/nginx/sites-enabled/workmatch*
sudo rm -f /etc/nginx/sites-enabled/default
sudo rm -f /etc/nginx/sites-available/workmatch*
log "Old Nginx configs removed"

# ── STEP 4: Remove old app directories ───────────────────────────────────────
info "Removing old application directories..."
sudo rm -rf "$FRONTEND_DIR"
sudo rm -rf "$BACKEND_DIR"
sudo rm -rf /var/www/workmatch
sudo rm -rf /opt/workmatch_backend_repo
sudo rm -rf /opt/workmatch_frontend_repo
log "Old directories removed"

# ── STEP 5: Clone fresh code ──────────────────────────────────────────────────
info "Cloning fresh frontend code..."
sudo mkdir -p "$FRONTEND_DIR"
sudo git clone "$FRONTEND_REPO" "$FRONTEND_DIR"
log "Frontend cloned → $FRONTEND_DIR"

info "Cloning fresh backend code..."
sudo mkdir -p "$BACKEND_DIR"
sudo git clone "$BACKEND_REPO" "$BACKEND_DIR"
log "Backend cloned → $BACKEND_DIR"

# ── STEP 6: Python virtual environment & dependencies ────────────────────────
info "Setting up Python virtual environment..."

# Ensure python3-venv is installed
sudo apt-get install -y -qq python3-venv python3-pip

# Remove any broken venv from previous run
sudo rm -rf "$BACKEND_DIR/.venv"

# Create fresh venv
sudo python3 -m venv "$BACKEND_DIR/.venv"

# Verify venv was created
if [ ! -f "$BACKEND_DIR/.venv/bin/pip" ]; then
    err "venv creation failed — pip not found at $BACKEND_DIR/.venv/bin/pip"
fi

sudo "$BACKEND_DIR/.venv/bin/pip" install --upgrade pip -q
sudo "$BACKEND_DIR/.venv/bin/pip" install gunicorn -q
sudo "$BACKEND_DIR/.venv/bin/pip" install -r "$BACKEND_DIR/requirements.txt" -q
log "Python dependencies installed"

# ── STEP 7: PocketBase binary ─────────────────────────────────────────────────
info "Setting up PocketBase..."
if [ ! -f "$BACKEND_DIR/pocketbase" ]; then
    # Download latest PocketBase if not in repo
    PB_VERSION="0.22.20"
    PB_URL="https://github.com/pocketbase/pocketbase/releases/download/v${PB_VERSION}/pocketbase_${PB_VERSION}_linux_amd64.zip"
    warn "pocketbase binary not found in repo — downloading v${PB_VERSION}..."
    curl -sL "$PB_URL" -o /tmp/pocketbase.zip
    sudo unzip -o /tmp/pocketbase.zip pocketbase -d "$BACKEND_DIR/"
    rm /tmp/pocketbase.zip
fi
sudo chmod +x "$BACKEND_DIR/pocketbase"
log "PocketBase ready"

# ── STEP 8: Create required directories ──────────────────────────────────────
info "Creating required directories..."
sudo mkdir -p "$BACKEND_DIR/pb_data"
sudo mkdir -p "$BACKEND_DIR/uploads"
sudo mkdir -p "$BACKEND_DIR/public"
log "Directories created"

# ── STEP 9: Write .env file ───────────────────────────────────────────────────
info "Writing .env configuration..."
sudo tee "$BACKEND_DIR/.env" > /dev/null <<EOF
# PocketBase
POCKETBASE_URL=http://127.0.0.1:${POCKETBASE_PORT}
PB_PUBLIC_URL=https://${DOMAIN_BACKEND}
PB_ADMIN_EMAIL=${PB_ADMIN_EMAIL}
PB_ADMIN_PASSWORD=${PB_ADMIN_PASSWORD}

# Server
HOST=0.0.0.0
PORT=${FASTAPI_PORT}
EOF
log ".env written"

# ── STEP 10: Fix permissions ──────────────────────────────────────────────────
info "Setting permissions..."
sudo chown -R www-data:www-data "$FRONTEND_DIR"
sudo chown -R www-data:www-data "$BACKEND_DIR"
sudo find "$FRONTEND_DIR" -type d -exec chmod 755 {} \;
sudo find "$FRONTEND_DIR" -type f -exec chmod 644 {} \;
sudo find "$BACKEND_DIR"  -type d -exec chmod 755 {} \;
sudo find "$BACKEND_DIR"  -type f -exec chmod 644 {} \;
sudo chmod +x "$BACKEND_DIR/pocketbase"
sudo chmod 600 "$BACKEND_DIR/.env"
log "Permissions set"

# ── STEP 11: Systemd — PocketBase service ────────────────────────────────────
info "Creating PocketBase systemd service..."
sudo tee /etc/systemd/system/workmatch_pocketbase.service > /dev/null <<EOF
[Unit]
Description=WorkMatch PocketBase
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=${BACKEND_DIR}
ExecStart=${BACKEND_DIR}/pocketbase serve --http=127.0.0.1:${POCKETBASE_PORT} --dir=${BACKEND_DIR}/pb_data
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=workmatch_pocketbase

[Install]
WantedBy=multi-user.target
EOF
log "PocketBase service created"

# ── STEP 12: Systemd — FastAPI service ───────────────────────────────────────
info "Creating FastAPI systemd service..."
sudo tee /etc/systemd/system/workmatch_backend.service > /dev/null <<EOF
[Unit]
Description=WorkMatch FastAPI Backend
After=network.target workmatch_pocketbase.service
Requires=workmatch_pocketbase.service
StartLimitIntervalSec=0

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=${BACKEND_DIR}
EnvironmentFile=${BACKEND_DIR}/.env
ExecStart=${BACKEND_DIR}/.venv/bin/gunicorn \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    main:app \
    --bind 127.0.0.1:${FASTAPI_PORT} \
    --timeout 120 \
    --access-logfile /var/log/workmatch_fastapi_access.log \
    --error-logfile /var/log/workmatch_fastapi_error.log
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=workmatch_backend

[Install]
WantedBy=multi-user.target
EOF
log "FastAPI service created"

# ── STEP 13: Nginx config — Frontend (theworkmatch.com) ──────────────────────
info "Writing Nginx config for frontend..."
info "Writing Nginx config for frontend..."
sudo tee /etc/nginx/sites-available/workmatch_frontend > /dev/null <<EOF
# ── HTTP → HTTPS redirect ────────────────────────────────────────────────────
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN_FRONTEND} www.${DOMAIN_FRONTEND};
    return 301 https://\$host\$request_uri;
}

# ── HTTPS — Frontend ─────────────────────────────────────────────────────────
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name ${DOMAIN_FRONTEND} www.${DOMAIN_FRONTEND};

    # SSL — filled in by certbot
    ssl_certificate     /etc/letsencrypt/live/${DOMAIN_FRONTEND}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN_FRONTEND}/privkey.pem;
    include             /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam         /etc/letsencrypt/ssl-dhparams.pem;

    # Security headers
    add_header X-Frame-Options        "SAMEORIGIN"  always;
    add_header X-Content-Type-Options "nosniff"     always;
    add_header X-XSS-Protection       "1; mode=block" always;
    add_header Referrer-Policy        "strict-origin-when-cross-origin" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    root  ${FRONTEND_DIR};
    index index.html;

    # Gzip
    gzip on;
    gzip_types text/plain text/css application/javascript application/json image/svg+xml;
    gzip_min_length 1024;

    # Static assets — long cache
    location ~* \.(jpg|jpeg|png|gif|ico|svg|webp|woff|woff2|ttf|eot|css|js)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        try_files \$uri =404;
    }

    # Clean URLs — /careers → careers.html
    location / {
        try_files \$uri \$uri.html \$uri/ =404;
    }

    # Career detail clean URL
    location /career-detail/ {
        rewrite ^/career-detail/(.*)$ /career-details.html?name=\$1 last;
    }

    access_log /var/log/nginx/workmatch_frontend_access.log;
    error_log  /var/log/nginx/workmatch_frontend_error.log;
}
EOF
log "Frontend Nginx config written"

# ── STEP 15: Nginx config — Backend (admin.theworkmatch.com) ─────────────────
info "Writing Nginx config for backend/admin..."
sudo tee /etc/nginx/sites-available/workmatch_backend > /dev/null <<EOF
# ── HTTP → HTTPS redirect ────────────────────────────────────────────────────
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN_BACKEND};
    return 301 https://\$host\$request_uri;
}

# ── HTTPS — Backend / Admin ──────────────────────────────────────────────────
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name ${DOMAIN_BACKEND};

    # SSL — filled in by certbot
    ssl_certificate     /etc/letsencrypt/live/${DOMAIN_BACKEND}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN_BACKEND}/privkey.pem;
    include             /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam         /etc/letsencrypt/ssl-dhparams.pem;

    # Security headers
    add_header X-Frame-Options        "SAMEORIGIN"  always;
    add_header X-Content-Type-Options "nosniff"     always;
    add_header X-XSS-Protection       "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    client_max_body_size 20M;

    # Gzip
    gzip on;
    gzip_types text/plain text/css application/javascript application/json;

    # PocketBase file storage — proxy directly to PB (bypasses FastAPI)
    location ^~ /api/files/ {
        proxy_pass         http://127.0.0.1:${POCKETBASE_PORT}/api/files/;
        proxy_set_header   Host              \$host;
        proxy_set_header   X-Real-IP         \$remote_addr;
        proxy_set_header   X-Forwarded-For   \$proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto \$scheme;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # FastAPI — all other requests
    location / {
        proxy_pass         http://127.0.0.1:${FASTAPI_PORT};
        proxy_set_header   Host              \$host;
        proxy_set_header   X-Real-IP         \$remote_addr;
        proxy_set_header   X-Forwarded-For   \$proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto \$scheme;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade           \$http_upgrade;
        proxy_set_header   Connection        "upgrade";
        proxy_connect_timeout 60s;
        proxy_send_timeout    60s;
        proxy_read_timeout    120s;
    }

    access_log /var/log/nginx/workmatch_backend_access.log;
    error_log  /var/log/nginx/workmatch_backend_error.log;
}
EOF
log "Backend Nginx config written"

# ── STEP 16: Enable Nginx sites ───────────────────────────────────────────────
info "Enabling Nginx sites..."
sudo ln -sf /etc/nginx/sites-available/workmatch_frontend /etc/nginx/sites-enabled/workmatch_frontend
sudo ln -sf /etc/nginx/sites-available/workmatch_backend  /etc/nginx/sites-enabled/workmatch_backend
log "Nginx sites enabled"

# ── STEP 17: Test Nginx config ────────────────────────────────────────────────
info "Testing Nginx configuration..."
sudo nginx -t || err "Nginx config test failed — check errors above"
log "Nginx config OK"

# ── STEP 18: Firewall ─────────────────────────────────────────────────────────
info "Configuring firewall..."
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
log "Firewall configured"

# ── STEP 19: Enable & start services ─────────────────────────────────────────
info "Starting PocketBase service..."
sudo systemctl daemon-reload
sudo systemctl enable workmatch_pocketbase
sudo systemctl start workmatch_pocketbase
sleep 3

if systemctl is-active --quiet workmatch_pocketbase; then
    log "PocketBase is running"
else
    err "PocketBase failed to start — run: sudo journalctl -u workmatch_pocketbase -n 50"
fi

info "Starting FastAPI backend service..."
sudo systemctl enable workmatch_backend
sudo systemctl start workmatch_backend
sleep 3

if systemctl is-active --quiet workmatch_backend; then
    log "FastAPI backend is running"
else
    err "FastAPI failed to start — run: sudo journalctl -u workmatch_backend -n 50"
fi

# ── STEP 20: Reload Nginx ─────────────────────────────────────────────────────
info "Reloading Nginx..."
sudo systemctl reload nginx
log "Nginx reloaded"

# ── STEP 21: SSL certificates ─────────────────────────────────────────────────
echo ""
warn "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
warn " SSL SETUP — Run these two commands manually after this script:"
warn ""
warn "   sudo certbot --nginx -d ${DOMAIN_FRONTEND} -d www.${DOMAIN_FRONTEND}"
warn "   sudo certbot --nginx -d ${DOMAIN_BACKEND}"
warn ""
warn " Then reload nginx:"
warn "   sudo systemctl reload nginx"
warn "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── DONE ──────────────────────────────────────────────────────────────────────
echo ""
echo "============================================================"
echo -e "${GREEN}   ✔  Fresh deployment complete!${NC}"
echo "============================================================"
echo ""
echo "  Frontend  → http://${DOMAIN_FRONTEND}  (HTTPS after certbot)"
echo "  Admin     → http://${DOMAIN_BACKEND}   (HTTPS after certbot)"
echo ""
echo "  Service status:"
echo "    sudo systemctl status workmatch_pocketbase"
echo "    sudo systemctl status workmatch_backend"
echo ""
echo "  Live logs:"
echo "    sudo journalctl -u workmatch_pocketbase -f"
echo "    sudo journalctl -u workmatch_backend -f"
echo ""
echo "  Nginx logs:"
echo "    sudo tail -f /var/log/nginx/workmatch_frontend_error.log"
echo "    sudo tail -f /var/log/nginx/workmatch_backend_error.log"
echo "============================================================"
