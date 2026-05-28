# Work Match Admin Dashboard - Direct Deployment Guide

## Prerequisites

- Ubuntu/Debian server (or similar Linux distribution)
- Python 3.9 or higher
- Nginx
- Domain: admin.theworkmatch.com pointing to your server IP

## Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and required packages
sudo apt install python3 python3-pip python3-venv nginx certbot python3-certbot-nginx -y
```

## Step 2: Upload Application Files

Upload these files to your server at `/var/www/workmatch`:

```bash
# Create directory
sudo mkdir -p /var/www/workmatch
sudo chown $USER:$USER /var/www/workmatch

# Upload files (from your local machine)
scp -r main.py requirements.txt seed_data.py public/ uploads/ user@your-server:/var/www/workmatch/
```

Or clone from git:
```bash
cd /var/www/workmatch
# git clone your-repo-url .
```

## Step 3: Setup Python Environment

```bash
cd /var/www/workmatch

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create uploads directory
mkdir -p uploads

# Set permissions
chmod 755 uploads
```

## Step 4: Initialize Database

```bash
# Still in /var/www/workmatch with venv activated
python seed_data.py
```

## Step 5: Create Systemd Service

Create service file:
```bash
sudo nano /etc/systemd/system/workmatch.service
```

Add this content:
```ini
[Unit]
Description=Work Match Admin Dashboard
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/workmatch
Environment="PATH=/var/www/workmatch/venv/bin"
Environment="SECRET_KEY=your-production-secret-key-change-this-to-random-string"
ExecStart=/var/www/workmatch/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Set permissions and start service:
```bash
# Set ownership
sudo chown -R www-data:www-data /var/www/workmatch

# Reload systemd
sudo systemctl daemon-reload

# Enable and start service
sudo systemctl enable workmatch
sudo systemctl start workmatch

# Check status
sudo systemctl status workmatch
```

## Step 6: Configure Nginx

Create Nginx configuration:
```bash
sudo nano /etc/nginx/sites-available/workmatch
```

Add this content:
```nginx
server {
    listen 80;
    server_name admin.theworkmatch.com;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_buffering off;
    }

    location /uploads/ {
        alias /var/www/workmatch/uploads/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable site:
```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/workmatch /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

## Step 7: Setup SSL Certificate

```bash
# Get SSL certificate from Let's Encrypt
sudo certbot --nginx -d admin.theworkmatch.com

# Follow the prompts
# Choose option 2 to redirect HTTP to HTTPS
```

## Step 8: Verify Deployment

```bash
# Check service status
sudo systemctl status workmatch

# Check logs
sudo journalctl -u workmatch -f

# Test the application
curl http://localhost:8000/admin/login
```

Visit: https://admin.theworkmatch.com

**Default Login:**
- Username: `admin`
- Password: `admin123`

## Useful Commands

```bash
# Restart application
sudo systemctl restart workmatch

# View logs
sudo journalctl -u workmatch -f

# Stop application
sudo systemctl stop workmatch

# Start application
sudo systemctl start workmatch

# Check Nginx status
sudo systemctl status nginx

# Restart Nginx
sudo systemctl restart nginx

# View Nginx error logs
sudo tail -f /var/log/nginx/error.log

# View Nginx access logs
sudo tail -f /var/log/nginx/access.log
```

## Update Application

```bash
# Stop service
sudo systemctl stop workmatch

# Navigate to directory
cd /var/www/workmatch

# Pull latest changes (if using git)
# git pull

# Or upload new files via scp
# scp -r main.py public/ user@your-server:/var/www/workmatch/

# Activate virtual environment
source venv/bin/activate

# Update dependencies if needed
pip install -r requirements.txt

# Set permissions
sudo chown -R www-data:www-data /var/www/workmatch

# Start service
sudo systemctl start workmatch

# Check status
sudo systemctl status workmatch
```

## Firewall Configuration

```bash
# Allow HTTP and HTTPS
sudo ufw allow 'Nginx Full'

# Allow SSH (if not already allowed)
sudo ufw allow OpenSSH

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

## Backup Database

```bash
# Create backup
cp /var/www/workmatch/careers.db /var/www/workmatch/careers.db.backup

# Or with timestamp
cp /var/www/workmatch/careers.db /var/www/workmatch/careers.db.$(date +%Y%m%d_%H%M%S)
```

## Troubleshooting

**Service won't start:**
```bash
sudo journalctl -u workmatch -n 50
```

**Permission errors:**
```bash
sudo chown -R www-data:www-data /var/www/workmatch
sudo chmod -R 755 /var/www/workmatch
sudo chmod 755 /var/www/workmatch/uploads
```

**Port already in use:**
```bash
sudo lsof -i :8000
# Kill the process if needed
sudo kill -9 <PID>
```

**Nginx errors:**
```bash
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
```

## Security Recommendations

1. **Change default admin password** immediately after first login
2. **Update SECRET_KEY** in systemd service file to a random string
3. **Setup firewall** to only allow necessary ports
4. **Regular backups** of the database
5. **Keep system updated**: `sudo apt update && sudo apt upgrade`
6. **Monitor logs** regularly for suspicious activity

## Performance Optimization

For production with high traffic, consider:

```bash
# Install gunicorn
source /var/www/workmatch/venv/bin/activate
pip install gunicorn

# Update systemd service ExecStart to:
# ExecStart=/var/www/workmatch/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 127.0.0.1:8000
```

---

**Support:** For issues, check logs first:
- Application: `sudo journalctl -u workmatch -f`
- Nginx: `sudo tail -f /var/log/nginx/error.log`
