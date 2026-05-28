"""
fix_admin.py — Reset / create PocketBase admin account
Run on server: python3 fix_admin.py

Works in two ways:
  1. If admin exists  → resets password to admin123456
  2. If no admin yet  → creates admin via PocketBase API (first-run mode)
"""
import sqlite3, os, sys, subprocess, time

DB      = os.getenv("PB_DB",       "/var/www/workmatch/pb_data/data.db")
EMAIL   = os.getenv("PB_ADMIN_EMAIL",    "admin@workmatch.com")
PASSWORD = os.getenv("PB_ADMIN_PASSWORD", "admin123456")
PB_URL  = os.getenv("POCKETBASE_URL",    "http://127.0.0.1:8090")

# ── Step 1: check bcrypt available ───────────────────────────────────────────
try:
    import bcrypt
except ImportError:
    print("Installing bcrypt...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "bcrypt", "-q"])
    import bcrypt

# ── Step 2: check DB exists ───────────────────────────────────────────────────
if not os.path.exists(DB):
    print(f"❌ Database not found at: {DB}")
    print("   Check PocketBase has started at least once to create pb_data/data.db")
    sys.exit(1)

# ── Step 3: inspect existing admins ──────────────────────────────────────────
con = sqlite3.connect(DB)
cur = con.cursor()

try:
    cur.execute("SELECT id, email FROM _admins")
    admins = cur.fetchall()
except sqlite3.OperationalError:
    admins = []

print(f"📋 Admins in DB: {admins if admins else 'none'}")

# ── Step 4: hash new password ─────────────────────────────────────────────────
hashed = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt(10)).decode()

if admins:
    # Update all admins OR just the matching email
    match = [a for a in admins if a[1] == EMAIL]
    if match:
        cur.execute("UPDATE _admins SET passwordHash=? WHERE email=?", (hashed, EMAIL))
        print(f"✅ Password reset for {EMAIL}")
    else:
        # Reset first admin found
        first_email = admins[0][1]
        cur.execute("UPDATE _admins SET passwordHash=? WHERE email=?", (hashed, first_email))
        print(f"✅ Password reset for {first_email} (target {EMAIL} not found)")
        EMAIL = first_email
    con.commit()
    con.close()
else:
    # No admins — create via API (PocketBase allows this when table is empty)
    con.close()
    print("⚠️  No admins in DB — creating via PocketBase API...")
    try:
        import urllib.request, json
        payload = json.dumps({
            "email": EMAIL,
            "password": PASSWORD,
            "passwordConfirm": PASSWORD
        }).encode()
        req = urllib.request.Request(
            f"{PB_URL}/api/admins",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            print(f"✅ Admin created: {data.get('email')}")
    except Exception as e:
        print(f"❌ API creation failed: {e}")
        print("   Make sure PocketBase is running: sudo systemctl start pocketbase")
        sys.exit(1)

# ── Step 5: verify by authenticating ─────────────────────────────────────────
print("\n🔍 Verifying credentials...")
time.sleep(1)
try:
    import urllib.request, json
    payload = json.dumps({"identity": EMAIL, "password": PASSWORD}).encode()
    req = urllib.request.Request(
        f"{PB_URL}/api/admins/auth-with-password",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read())
        print(f"✅ Login successful! Token: {data['token'][:30]}...")
        print(f"\n🎉 Admin credentials:")
        print(f"   Email:    {EMAIL}")
        print(f"   Password: {PASSWORD}")
        print(f"\n   Dashboard: https://admin.theworkmatch.com/admin/login")
except Exception as e:
    print(f"❌ Verification failed: {e}")
    print("   PocketBase may need a restart: sudo systemctl restart pocketbase")
    print("   Then re-run this script.")
