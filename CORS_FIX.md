# CORS Issue Fix

## Problem
CORS error when accessing `/api/jobs` from `https://admin.theworkmatch.com`

## Root Cause
The CORS middleware configuration needs to properly handle requests from the same domain.

## Solution Applied

### 1. Updated CORS Configuration in `main.py`
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://theworkmatch.com",
        "https://www.theworkmatch.com",
        "https://admin.theworkmatch.com",
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)
```

### 2. Key Changes
- Explicitly listed all HTTP methods instead of using `"*"`
- Added `expose_headers=["*"]` to ensure response headers are accessible
- Kept `allow_credentials=True` for authentication

## Testing

After deploying, test with:

```bash
# Test from command line
curl -I https://admin.theworkmatch.com/api/jobs

# Should return headers including:
# Access-Control-Allow-Origin: https://admin.theworkmatch.com
# Access-Control-Allow-Credentials: true
```

## If Issue Persists

### Check Nginx Configuration
The nginx.conf might need to add CORS headers. Update `/etc/nginx/sites-available/workmatch`:

```nginx
server {
    listen 80;
    server_name admin.theworkmatch.com;
    client_max_body_size 10M;

    # Add CORS headers for API routes
    location /api/ {
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' '$http_origin' always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS, PATCH' always;
            add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type' always;
            add_header 'Access-Control-Allow-Credentials' 'true' always;
            add_header 'Content-Length' 0;
            add_header 'Content-Type' 'text/plain';
            return 204;
        }

        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    location /uploads/ {
        alias /var/www/workmatch/uploads/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

### Alternative: Simpler Nginx Config (Let FastAPI Handle CORS)
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
        
        # Don't add CORS headers here - let FastAPI handle it
    }

    location /uploads/ {
        alias /var/www/workmatch/uploads/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

## Deployment

After making changes:

```bash
# Deploy updated main.py
python3 deploy.py update

# If nginx config was changed
sudo nginx -t
sudo systemctl reload nginx

# Check logs
sudo journalctl -u workmatch -f
```

## Browser Console Check

Open browser console (F12) and check:
1. Network tab - look at the failed request
2. Check request headers
3. Check response headers
4. Look for preflight OPTIONS request

## Common Issues

1. **Preflight OPTIONS request failing**
   - FastAPI should handle this automatically
   - Check if OPTIONS method is allowed

2. **Credentials flag mismatch**
   - Frontend must use `credentials: 'include'` in fetch
   - Backend must have `allow_credentials=True`

3. **Origin not in allow list**
   - Verify the exact origin in browser console
   - Add it to allow_origins list

## Current Status

✅ CORS middleware updated in main.py
✅ All necessary origins added
✅ Proper methods and headers configured
⏳ Needs deployment to test

Deploy with: `python3 deploy.py update`
