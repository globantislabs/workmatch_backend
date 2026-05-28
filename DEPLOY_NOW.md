# Deploy Updated Code to Fix 500 Errors

## The Issue
You're getting 500 errors on `/admin/api/blogs` because the updated code with error handling hasn't been deployed to the server yet.

## The Fix (Already Done Locally)
The code in `main.py` has been updated with proper error handling:
- `admin_list_blogs()` now returns `[]` instead of 500 error
- `admin_list_jobs()` now returns `[]` instead of 500 error
- Authentication fixed with proper Bearer token format

## Deploy Now

### Option 1: Deploy from Server (Recommended)
```bash
# SSH into your server
ssh ubuntu@admin.theworkmatch.com

# Navigate to the backend directory
cd ~/backend

# Run the update command
python3 deploy.py update
```

### Option 2: Push from Local Machine
```bash
# From your local machine (where the code is)
python3 deploy.py push
```

This will:
1. Upload all files via SCP
2. Install dependencies
3. Restart the FastAPI service
4. Keep PocketBase running

## After Deployment

### 1. Check Service Status
```bash
sudo systemctl status workmatch
```

### 2. Check Logs
```bash
sudo journalctl -u workmatch -f
```

### 3. Test in Browser
1. Go to `https://admin.theworkmatch.com/admin/login`
2. Clear browser cache (Ctrl+Shift+Delete)
3. Clear localStorage: F12 → Console → Type: `localStorage.clear()`
4. Login again
5. Click on "Blog Posts" tab
6. Should see empty state or list of blogs (no 500 error)

## What to Expect

### Before Deployment
- ❌ 500 error on `/admin/api/blogs`
- ❌ Cannot save blog posts
- ❌ Console shows "Internal Server Error"

### After Deployment
- ✅ Blogs tab loads (shows empty state if no blogs)
- ✅ Can create new blog posts
- ✅ Edit/Delete buttons work
- ✅ No 500 errors in console

## If Still Getting Errors

### Check if blogs collection exists
```bash
# SSH into server
ssh ubuntu@admin.theworkmatch.com

# Check PocketBase collections
curl http://127.0.0.1:8090/api/collections
```

### Create blogs collection if missing
```bash
cd /var/www/workmatch
sudo -u www-data python3 setup_pb.py
```

### Restart both services
```bash
sudo systemctl restart pocketbase
sudo systemctl restart workmatch
```

## Quick Verification

After deployment, run this from the server:
```bash
# Get a token
TOKEN=$(curl -s -X POST https://admin.theworkmatch.com/api/auth/login \
  -F "username=admin@workmatch.com" \
  -F "password=admin123456" | jq -r '.token')

# Test blogs endpoint
curl -H "Authorization: Bearer $TOKEN" \
  https://admin.theworkmatch.com/admin/api/blogs

# Should return: [] or list of blogs (not 500 error)
```

## Deploy Command (Copy-Paste Ready)
```bash
ssh ubuntu@admin.theworkmatch.com "cd ~/backend && python3 deploy.py update"
```

This single command will deploy everything and fix the 500 errors.
