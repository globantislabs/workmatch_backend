# Deploy and Test Instructions

## Current Issue
- 500 error on `/admin/api/blogs`
- Cannot save blog posts
- Authentication might be failing

## Steps to Fix

### 1. Deploy Updated Code
```bash
# SSH into server
ssh ubuntu@admin.theworkmatch.com

# Navigate to staging directory
cd ~/backend

# Pull latest changes or upload files
# Then run update
python3 deploy.py update
```

### 2. Check Server Logs
```bash
# Check FastAPI logs
sudo journalctl -u workmatch -f

# Check PocketBase logs
sudo journalctl -u pocketbase -f

# Check if services are running
sudo systemctl status workmatch
sudo systemctl status pocketbase
```

### 3. Test Authentication
```bash
# Test login endpoint
curl -X POST https://admin.theworkmatch.com/api/auth/login \
  -F "username=admin@workmatch.com" \
  -F "password=admin123456"

# Should return: {"token":"...","admin":{...}}
```

### 4. Test Blogs Endpoint
```bash
# Get token from login response above, then:
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  https://admin.theworkmatch.com/admin/api/blogs

# Should return: [] (empty array) or list of blogs
```

## Common Issues and Solutions

### Issue 1: Code Not Deployed
**Symptom:** Still getting old errors after "fixing"
**Solution:**
```bash
python3 deploy.py update
sudo systemctl restart workmatch
```

### Issue 2: PocketBase Not Running
**Symptom:** Connection refused errors
**Solution:**
```bash
sudo systemctl start pocketbase
sudo systemctl status pocketbase
```

### Issue 3: Blogs Collection Doesn't Exist
**Symptom:** 404 or collection not found
**Solution:**
```bash
# Run migrations
cd /var/www/workmatch
sudo -u www-data python3 setup_pb.py
```

### Issue 4: Token Expired
**Symptom:** "Not authenticated" or 401 errors
**Solution:**
- Logout and login again in the browser
- Clear browser localStorage
- Check token expiration in code

### Issue 5: CORS Still Blocking
**Symptom:** CORS errors in browser console
**Solution:**
```bash
# Check nginx config
sudo nginx -t
sudo systemctl reload nginx
```

## Manual Testing Checklist

After deployment:

1. ✅ Login works
   - Go to `/admin/login`
   - Enter credentials
   - Should redirect to dashboard

2. ✅ Dashboard loads
   - All tabs visible
   - No console errors
   - Stats load

3. ✅ Careers tab works
   - Lists applications
   - Edit button works
   - Delete button works

4. ✅ Hire Talent tab works
   - Lists requests
   - Edit button works
   - Delete button works

5. ✅ Jobs tab works
   - Lists jobs (or empty)
   - Add Job button works
   - Edit/Delete works

6. ✅ Blogs tab works
   - Lists blogs (or empty)
   - Add Post button works
   - Edit/Delete works

7. ✅ Change Password works
   - Button in sidebar
   - Modal opens
   - Can change password

## If Still Getting 500 Errors

### Check Actual Error in Logs
```bash
sudo journalctl -u workmatch -n 100 --no-pager
```

Look for Python tracebacks showing the actual error.

### Common 500 Error Causes

1. **Missing dependency**
   ```bash
   cd /var/www/workmatch
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Database locked**
   ```bash
   sudo systemctl restart pocketbase
   sudo systemctl restart workmatch
   ```

3. **Permission issues**
   ```bash
   sudo chown -R www-data:www-data /var/www/workmatch
   sudo chmod -R 755 /var/www/workmatch
   ```

4. **Environment variables missing**
   ```bash
   # Check service file
   sudo cat /etc/systemd/system/workmatch.service
   
   # Should have:
   # Environment="POCKETBASE_URL=http://127.0.0.1:8090"
   # Environment="PB_ADMIN_EMAIL=admin@workmatch.com"
   # Environment="PB_ADMIN_PASSWORD=admin123456"
   ```

## Quick Fix Script

Create this script on the server:

```bash
#!/bin/bash
# fix-workmatch.sh

echo "Stopping services..."
sudo systemctl stop workmatch
sudo systemctl stop pocketbase

echo "Starting PocketBase..."
sudo systemctl start pocketbase
sleep 3

echo "Starting WorkMatch..."
sudo systemctl start workmatch
sleep 3

echo "Checking status..."
sudo systemctl status pocketbase --no-pager
sudo systemctl status workmatch --no-pager

echo "Tailing logs (Ctrl+C to stop)..."
sudo journalctl -u workmatch -f
```

Run with:
```bash
chmod +x fix-workmatch.sh
./fix-workmatch.sh
```

## Contact Points

If issues persist, check:
1. Server logs: `sudo journalctl -u workmatch -f`
2. Browser console: F12 → Console tab
3. Network tab: F12 → Network tab → Look at failed requests
4. PocketBase admin: `http://127.0.0.1:8090/_/` (from server)

## Success Indicators

You'll know it's working when:
- ✅ No 500 errors in browser console
- ✅ All tabs load without errors
- ✅ Can create/edit/delete records
- ✅ Change password works
- ✅ No "Not authenticated" errors
