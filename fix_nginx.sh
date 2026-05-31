#!/bin/bash
# Fix nginx redirect loop — rewrite clean configs with proper HTTP/HTTPS split
set -e

GREEN='\033[0;32m'; CYAN='\033[0;36m'; NC='\033[0m'
log()  { echo -e "${GREEN}[✔]${NC} $1"; }
info() { echo -e "${CYAN}[→]${NC} $1"; }

info "Writing clean frontend nginx config..."
sudo tee /etc/nginx/sites-available/workmatch_frontend > /dev/null << 'EOF'
# HTTP — redirect to HTTPS only
server {
    listen 80;
    listen [::]:80;
    server_name theworkmatch.com www.theworkmatch.com;
    return 301 https://$host$request_uri;
}

# HTTPS — serve frontend
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    http2 on;
    server_name theworkmatch.com www.theworkmatch.com;

    ssl_certificate     /etc/letsencrypt/live/theworkmatch.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/theworkmatch.com/privkey.pem;
    include             /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam         /etc/letsencrypt/ssl-dhparams.pem;

    root  /var/www/workmatch_frontend;
    index index.html;

    gzip on;
    gzip_types text/plain text/css application/javascript application/json image/svg+xml;
    gzip_min_length 1024;

    # Static assets — long cache
    location ~* \.(jpg|jpeg|png|gif|ico|svg|webp|woff|woff2|ttf|eot|css|js)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        try_files $uri =404;
    }

    # Clean URLs
    location / {
        try_files $uri $uri.html $uri/ =404;
    }

    # Career detail clean URL
    location ~ ^/career-detail/(.+)$ {
        rewrite ^/career-detail/(.+)$ /career-details.html?name=$1 last;
    }

    access_log /var/log/nginx/workmatch_frontend_access.log;
    error_log  /var/log/nginx/workmatch_frontend_error.log;
}
EOF
log "Frontend config written"

info "Writing clean backend nginx config..."
sudo tee /etc/nginx/sites-available/workmatch_backend > /dev/null << 'EOF'
# HTTP — redirect to HTTPS only
server {
    listen 80;
    listen [::]:80;
    server_name admin.theworkmatch.com;
    return 301 https://$host$request_uri;
}

# HTTPS — proxy to FastAPI
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    http2 on;
    server_name admin.theworkmatch.com;

    ssl_certificate     /etc/letsencrypt/live/admin.theworkmatch.com-0001/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/admin.theworkmatch.com-0001/privkey.pem;
    include             /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam         /etc/letsencrypt/ssl-dhparams.pem;

    client_max_body_size 20M;

    gzip on;
    gzip_types text/plain text/css application/javascript application/json;

    # PocketBase files — bypass FastAPI
    location ^~ /api/files/ {
        proxy_pass         http://127.0.0.1:8090/api/files/;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # FastAPI
    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade           $http_upgrade;
        proxy_set_header   Connection        "upgrade";
        proxy_connect_timeout 60s;
        proxy_send_timeout    60s;
        proxy_read_timeout    120s;
    }

    access_log /var/log/nginx/workmatch_backend_access.log;
    error_log  /var/log/nginx/workmatch_backend_error.log;
}
EOF
log "Backend config written"

info "Testing nginx..."
sudo nginx -t
log "Nginx config OK"

info "Reloading nginx..."
sudo systemctl reload nginx
log "Nginx reloaded"

echo ""
echo "============================================================"
echo -e "${GREEN}   ✔  Nginx fixed!${NC}"
echo "============================================================"
echo "  Frontend → https://theworkmatch.com"
echo "  Admin    → https://admin.theworkmatch.com"
echo "  Open in incognito to avoid cached redirects"
echo "============================================================"
