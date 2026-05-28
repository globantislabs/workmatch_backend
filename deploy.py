"""
deploy.py — Work Match: All-in-one deployment & update tool
Pure Python, no bash required.

Commands:
    python3 deploy.py install    # Fresh install on server
    python3 deploy.py update     # Update code + restart services
    python3 deploy.py fix-admin  # Reset PocketBase admin password
    python3 deploy.py status     # Show service status
    python3 deploy.py logs       # Tail service logs
    python3 deploy.py push       # Upload files from local machine via SCP then update
"""
import os, sys, subprocess, shutil, time, argparse, urllib.request, json, secrets
from pathlib import Path
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
APP_DIR      = Path("/var/www/workmatch")
BACKUP_DIR   = Path("/var/www/workmatch_backups")
SERVICE_NAME = "workmatch"
PB_SERVICE   = "pocketbase"
DOMAIN       = "admin.theworkmatch.com"
PB_VERSION   = "0.22.4"
PB_BINARY    = APP_DIR / "pocketbase"
PB_URL_LOCAL = "http://127.0.0.1:8090"
ADMIN_EMAIL  = "admin@workmatch.com"
ADMIN_PASS   = "admin123456"
SSH_HOST     = "ubuntu@admin.theworkmatch.com"
REMOTE_STAGE = "~/backend"

# ── Colours ───────────────────────────────────────────────────────────────────
G = "\033[0;32m"; B = "\033[0;34m"; Y = "\033[1;33m"; R = "\033[0;31m"; N = "\033[0m"

def ok(msg):   print(f"{G}✅{N} {msg}")
def info(msg): print(f"{B}▶{N}  {msg}")
def warn(msg): print(f"{Y}⚠{N}  {msg}")
def err(msg):  print(f"{R}❌{N} {msg}")

# ── Shell helpers ─────────────────────────────────────────────────────────────
def run(cmd, check=True, capture=False, env=None):
    kw = dict(check=check, env=env)
    if capture:
        kw["capture_output"] = True
        kw["text"] = True
    if isinstance(cmd, str):
        kw["shell"] = True
    return subprocess.run(cmd, **kw)

def sudo(cmd, check=True, env=None):
    if isinstance(cmd, list):
        return run(["sudo"] + cmd, check=check, env=env)
    return run(f"sudo {cmd}", check=check, env=env)

def systemctl(action, service, check=True):
    if not service:
        return sudo(["systemctl", action], check=check)
    return sudo(["systemctl", action, service], check=check)

def service_active(name):
    return sudo(["systemctl", "is-active", "--quiet", name], check=False).returncode == 0

def write_file(path, content):
    """Write content to a privileged path via sudo tee."""
    proc = subprocess.Popen(["sudo", "tee", str(path)],
                            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL)
    proc.communicate(content.encode())

def pb_arch():
    r = run(["uname", "-m"], capture=True)
    return "arm64" if r.stdout.strip() == "aarch64" else "amd64"

def http_get(url, timeout=5):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status, r.read()
    except Exception as e:
        return 0, str(e).encode()

def http_post(url, payload, timeout=5):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())
    except Exception as e:
        return 0, {"error": str(e)}


# ══════════════════════════════════════════════════════════════════════════════
# INSTALL / UPDATE STEPS
# ══════════════════════════════════════════════════════════════════════════════

def backup():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    sudo(["chown", f"{os.getenv('USER')}:{os.getenv('USER')}", str(BACKUP_DIR)])
    if APP_DIR.exists():
        name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        info(f"Creating backup: {name}")
        sudo(["cp", "-r", str(APP_DIR), str(BACKUP_DIR / name)])
        ok(f"Backup at {BACKUP_DIR / name}")
        return name
    return None


def stop_services():
    for svc in [SERVICE_NAME, PB_SERVICE]:
        if service_active(svc):
            info(f"Stopping {svc}...")
            systemctl("stop", svc)
            ok(f"{svc} stopped")


def setup_app_dir():
    if not APP_DIR.exists():
        sudo(["mkdir", "-p", str(APP_DIR)])
    sudo(["chown", "-R", f"{os.getenv('USER')}:{os.getenv('USER')}", str(APP_DIR)])


def setup_venv():
    venv = APP_DIR / "venv"
    if not venv.exists():
        info("Creating Python virtual environment...")
        run([sys.executable, "-m", "venv", str(venv)])
        ok("Virtual environment created")


def copy_files():
    info("Copying application files...")
    src = Path(".").resolve()
    dst_root = APP_DIR.resolve()

    if src == dst_root:
        ok("Already in app directory — skipping file copy")
        return

    # Core Python files
    for f in ["main.py", "requirements.txt", "seed_data.py", "setup_pb.py", "fix_admin.py", "deploy.py"]:
        if (src / f).exists():
            shutil.copy(src / f, dst_root / f)
            print(f"   {f}")
    
    # Directories (public includes all HTML pages including password reset)
    for d in ["public", "pb_migrations"]:
        if (src / d).exists():
            dst = dst_root / d
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src / d, dst)
            print(f"   {d}/")
    
    # Ensure uploads directory exists
    (dst_root / "uploads").mkdir(exist_ok=True)
    ok("Files copied (including password reset pages)")


def install_deps():
    info("Installing Python dependencies...")
    pip = APP_DIR / "venv" / "bin" / "pip"
    run([str(pip), "install", "--upgrade", "pip", "-q"])
    run([str(pip), "install", "-r", str(APP_DIR / "requirements.txt"), "-q"])
    ok("Dependencies installed")


def download_pocketbase():
    if PB_BINARY.exists():
        warn("PocketBase binary already exists — skipping download")
        return
    info(f"Downloading PocketBase v{PB_VERSION}...")
    arch = pb_arch()
    url = (f"https://github.com/pocketbase/pocketbase/releases/download/"
           f"v{PB_VERSION}/pocketbase_{PB_VERSION}_linux_{arch}.zip")
    tmp_zip = Path("/tmp/pocketbase.zip")
    tmp_dir = Path("/tmp/pb_extract")
    urllib.request.urlretrieve(url, tmp_zip)
    run(["unzip", "-q", str(tmp_zip), "-d", str(tmp_dir)])
    shutil.copy(tmp_dir / "pocketbase", PB_BINARY)
    PB_BINARY.chmod(0o755)
    shutil.rmtree(tmp_dir, ignore_errors=True)
    tmp_zip.unlink(missing_ok=True)
    ok("PocketBase downloaded")


def create_pb_service():
    svc = Path(f"/etc/systemd/system/{PB_SERVICE}.service")
    if svc.exists():
        warn("PocketBase service already exists — skipping")
        return
    info("Creating PocketBase systemd service...")
    write_file(svc, f"""[Unit]
Description=PocketBase for Work Match
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory={APP_DIR}
ExecStart={PB_BINARY} serve --http=127.0.0.1:8090 --dir={APP_DIR}/pb_data
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
""")
    ok("PocketBase service created")


def create_app_service():
    svc = Path(f"/etc/systemd/system/{SERVICE_NAME}.service")
    if svc.exists():
        warn("FastAPI service already exists — skipping")
        return
    info("Creating FastAPI systemd service...")
    secret = secrets.token_urlsafe(32)
    write_file(svc, f"""[Unit]
Description=Work Match Admin Dashboard (FastAPI)
After=network.target {PB_SERVICE}.service
Requires={PB_SERVICE}.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory={APP_DIR}
Environment="PATH={APP_DIR}/venv/bin"
Environment="POCKETBASE_URL=http://127.0.0.1:8090"
Environment="PB_ADMIN_EMAIL={ADMIN_EMAIL}"
Environment="PB_ADMIN_PASSWORD={ADMIN_PASS}"
Environment="SECRET_KEY={secret}"
ExecStart={APP_DIR}/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
""")
    ok("FastAPI service created")


def set_permissions():
    info("Setting permissions...")
    sudo(["mkdir", "-p", str(APP_DIR / "pb_data")])
    sudo(["mkdir", "-p", str(APP_DIR / "uploads")])
    sudo(["chown", "-R", "www-data:www-data", str(APP_DIR)])
    sudo(["chmod", "-R", "755", str(APP_DIR)])
    sudo(["chmod", "775", str(APP_DIR / "uploads")])
    sudo(["chmod", "775", str(APP_DIR / "pb_data")])
    ok("Permissions set")


def start_pocketbase():
    info("Starting PocketBase...")
    systemctl("daemon-reload", "")
    systemctl("enable", PB_SERVICE)
    systemctl("start", PB_SERVICE)
    time.sleep(3)
    if service_active(PB_SERVICE):
        ok("PocketBase running on port 8090")
    else:
        err("PocketBase failed to start")
        sudo(["journalctl", "-u", PB_SERVICE, "-n", "30"])
        sys.exit(1)


def run_setup_scripts(mode):
    python = str(APP_DIR / "venv" / "bin" / "python")
    env = {**os.environ,
           "POCKETBASE_URL": PB_URL_LOCAL,
           "PB_ADMIN_EMAIL": ADMIN_EMAIL,
           "PB_ADMIN_PASSWORD": ADMIN_PASS,
           "PB_DB": str(APP_DIR / "pb_data" / "data.db")}
    if mode == "install":
        info("Running PocketBase setup (collections + admin)...")
        sudo(["--preserve-env=POCKETBASE_URL,PB_ADMIN_EMAIL,PB_ADMIN_PASSWORD",
              "-u", "www-data", python, str(APP_DIR / "setup_pb.py")], env=env)
        ok("Collections created")
        info("Seeding sample data...")
        sudo(["--preserve-env=POCKETBASE_URL,PB_ADMIN_EMAIL,PB_ADMIN_PASSWORD",
              "-u", "www-data", python, str(APP_DIR / "seed_data.py")], env=env)
        ok("Sample data seeded")
    # Always fix admin on both install and update
    info("Verifying admin credentials...")
    sudo(["--preserve-env=POCKETBASE_URL,PB_ADMIN_EMAIL,PB_ADMIN_PASSWORD,PB_DB",
          "-u", "www-data", python, str(APP_DIR / "fix_admin.py")], env=env)


def start_fastapi():
    info("Starting FastAPI...")
    systemctl("enable", SERVICE_NAME)
    systemctl("start", SERVICE_NAME)
    time.sleep(3)
    if service_active(SERVICE_NAME):
        ok("FastAPI running on port 8000")
    else:
        err("FastAPI failed to start")
        sudo(["journalctl", "-u", SERVICE_NAME, "-n", "30"])
        sys.exit(1)


def configure_nginx():
    nginx_conf = Path("/etc/nginx/sites-available/workmatch")
    if nginx_conf.exists():
        warn("Nginx already configured — reloading")
        systemctl("reload", "nginx")
        ok("Nginx reloaded")
        return
    info("Configuring Nginx...")
    write_file(nginx_conf, f"""server {{
    listen 80;
    server_name {DOMAIN};
    client_max_body_size 10M;

    location / {{
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }}

    location /uploads/ {{
        alias {APP_DIR}/uploads/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }}
}}
""")
    sudo(["ln", "-sf", str(nginx_conf), "/etc/nginx/sites-enabled/workmatch"])
    r = sudo(["nginx", "-t"], check=False)
    if r.returncode == 0:
        systemctl("restart", "nginx")
        ok("Nginx configured")
    else:
        err("Nginx config test failed")
        sys.exit(1)


def health_check():
    info("Health check...")
    time.sleep(2)
    code, _ = http_get("http://localhost:8000/admin/login")
    if code == 200:
        ok("Application is responding")
    else:
        warn(f"App returned HTTP {code} — check logs if needed")


def print_summary(backup_name=None):
    print(f"\n{'━'*54}")
    print(f"{G}✨ Done!{N}")
    print(f"{'━'*54}")
    print(f"\n{B}🌐 Dashboard:{N}  https://{DOMAIN}/admin")
    print(f"{B}👤 Login:{N}      {ADMIN_EMAIL} / {ADMIN_PASS}")
    print(f"{B}🔑 Password Reset:{N} https://{DOMAIN}/admin/forgot-password")
    print(f"\n{B}📋 Commands:{N}")
    print(f"   Logs:    sudo journalctl -u {SERVICE_NAME} -f")
    print(f"   Restart: sudo systemctl restart {PB_SERVICE} {SERVICE_NAME}")
    print(f"   Update:  python3 deploy.py update")
    if backup_name:
        print(f"\n{B}💾 Backup:{N} {BACKUP_DIR}/{backup_name}")
    print(f"\n{B}✨ New Features:{N}")
    print(f"   • Password reset functionality")
    print(f"   • Full CRUD for Applications & Hire Talent")
    print(f"   • Edit modals in admin dashboard")
    print(f"\n{'━'*54}\n")


# ══════════════════════════════════════════════════════════════════════════════
# COMMANDS
# ══════════════════════════════════════════════════════════════════════════════

def cmd_install():
    """Full fresh install on the server."""
    if os.geteuid() == 0:
        err("Do not run as root. Use a sudo-capable user.")
        sys.exit(1)
    print(f"\n🚀 Work Match — INSTALL\n")
    backup_name = backup()
    stop_services()
    setup_app_dir()
    setup_venv()
    copy_files()
    install_deps()
    download_pocketbase()
    create_pb_service()
    create_app_service()
    set_permissions()
    start_pocketbase()
    run_setup_scripts("install")
    start_fastapi()
    configure_nginx()
    health_check()
    print_summary(backup_name)


def cmd_update():
    """Update code files and restart FastAPI (keeps PocketBase running)."""
    if os.geteuid() == 0:
        err("Do not run as root.")
        sys.exit(1)
    print(f"\n🔄 Work Match — UPDATE\n")

    # Re-own so we can write (only if not already running from APP_DIR)
    if Path(".").resolve() != APP_DIR.resolve():
        sudo(["chown", "-R", f"{os.getenv('USER')}:{os.getenv('USER')}", str(APP_DIR)])

    copy_files()
    install_deps()

    # Fix ownership back
    set_permissions()

    info("Restarting FastAPI...")
    systemctl("restart", SERVICE_NAME)
    time.sleep(3)
    if service_active(SERVICE_NAME):
        ok("FastAPI restarted")
    else:
        err("FastAPI failed to restart")
        sudo(["journalctl", "-u", SERVICE_NAME, "-n", "30"])
        sys.exit(1)

    health_check()
    print_summary()


def cmd_fix_admin():
    """Reset / create PocketBase admin — works even when _admins table is empty."""
    print(f"\n🔧 Work Match — FIX ADMIN\n")

    # Install bcrypt if needed
    try:
        import bcrypt
    except ImportError:
        info("Installing bcrypt...")
        run([sys.executable, "-m", "pip", "install", "bcrypt", "-q"])
        import bcrypt

    import sqlite3, string, random

    # Find DB — check both possible locations
    candidates = [
        APP_DIR / "pb_data" / "data.db",
        Path("/var/www/workmatch/pb_data/data.db"),
    ]
    db_path = next((p for p in candidates if p.exists()), None)
    if not db_path:
        err("Database not found. Check PocketBase has started at least once.")
        sys.exit(1)

    info(f"Using DB: {db_path}")

    # Stop PocketBase so DB isn't locked
    was_running = service_active(PB_SERVICE)
    if was_running:
        info("Stopping PocketBase...")
        systemctl("stop", PB_SERVICE)
        time.sleep(2)

    hashed = bcrypt.hashpw(ADMIN_PASS.encode(), bcrypt.gensalt(10)).decode()

    con = sqlite3.connect(str(db_path))
    cur = con.cursor()

    # Check table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='_admins'")
    table_exists = cur.fetchone() is not None

    if table_exists:
        cur.execute("SELECT id, email FROM _admins")
        admins = cur.fetchall()
    else:
        admins = []

    print(f"   Table exists: {table_exists}")
    print(f"   Admins found: {admins or 'none'}")

    if admins:
        # Update existing admin
        match = [a for a in admins if a[1] == ADMIN_EMAIL]
        target = match[0] if match else admins[0]
        cur.execute("UPDATE _admins SET passwordHash=? WHERE id=?", (hashed, target[0]))
        con.commit()
        ok(f"Password reset for {target[1]}")

    elif table_exists:
        # Table exists but empty — INSERT directly
        info("Inserting admin record directly into DB...")
        import time as _time
        # Generate a 15-char random ID like PocketBase uses
        chars = string.ascii_letters + string.digits
        new_id = ''.join(random.choices(chars, k=15))
        now = _time.strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("""
            INSERT INTO _admins (id, avatar, email, passwordHash, created, updated)
            VALUES (?, 0, ?, ?, ?, ?)
        """, (new_id, ADMIN_EMAIL, hashed, now, now))
        con.commit()
        ok(f"Admin inserted: {ADMIN_EMAIL}")

    else:
        # Table doesn't exist — PocketBase never ran, start it fresh
        con.close()
        warn("_admins table missing — starting PocketBase to initialize DB...")
        systemctl("start", PB_SERVICE)
        time.sleep(5)
        # Try PocketBase v0.22 setup endpoint (works only when no admins exist)
        code, resp = http_post(f"{PB_URL_LOCAL}/api/admins",
                               {"email": ADMIN_EMAIL, "password": ADMIN_PASS,
                                "passwordConfirm": ADMIN_PASS})
        if code in (200, 201):
            ok(f"Admin created via API: {resp.get('email')}")
        else:
            err(f"API creation failed ({code}): {resp}")
            err("Try deleting pb_data/data.db and restarting PocketBase for a clean init.")
            sys.exit(1)
        _verify_login()
        return

    con.close()

    # Restart PocketBase
    info("Starting PocketBase...")
    systemctl("start", PB_SERVICE)
    time.sleep(4)

    _verify_login()


def _verify_login():
    info("Verifying login...")
    code, resp = http_post(f"{PB_URL_LOCAL}/api/admins/auth-with-password",
                           {"identity": ADMIN_EMAIL, "password": ADMIN_PASS})
    if code == 200:
        ok(f"Login verified!")
        print(f"\n   Email:    {ADMIN_EMAIL}")
        print(f"   Password: {ADMIN_PASS}")
        print(f"   Login:    https://{DOMAIN}/admin/login\n")
    else:
        err(f"Verification failed ({code}): {resp}")
        warn("Try: sudo systemctl restart pocketbase  then run fix-admin again")


def cmd_status():
    """Show status of all services."""
    print(f"\n📊 Work Match — STATUS\n")
    for svc in [PB_SERVICE, SERVICE_NAME, "nginx"]:
        active = service_active(svc)
        state = f"{G}running{N}" if active else f"{R}stopped{N}"
        print(f"   {svc:<20} {state}")

    print()
    # Quick API check
    code, _ = http_get("http://localhost:8000/admin/login")
    api_ok = f"{G}OK (HTTP {code}){N}" if code == 200 else f"{R}FAIL (HTTP {code}){N}"
    print(f"   FastAPI health       {api_ok}")

    code2, _ = http_get(f"{PB_URL_LOCAL}/api/health")
    pb_ok = f"{G}OK{N}" if code2 == 200 else f"{R}FAIL (HTTP {code2}){N}"
    print(f"   PocketBase health    {pb_ok}\n")


def cmd_logs(service=None):
    """Tail logs for a service (default: workmatch)."""
    svc = service or SERVICE_NAME
    print(f"\n📋 Logs for {svc} (Ctrl+C to stop)\n")
    try:
        subprocess.run(["sudo", "journalctl", "-u", svc, "-f", "--no-pager"])
    except KeyboardInterrupt:
        pass


def cmd_push(host=SSH_HOST, remote_dir=REMOTE_STAGE):
    """Upload files from local machine via SCP, then run update on server."""
    print(f"\n📤 Work Match — PUSH to {host}\n")

    # Core Python files
    files = ["main.py", "requirements.txt", "fix_admin.py", "deploy.py",
             "setup_pb.py", "seed_data.py"]
    
    # Directories (public includes all HTML pages including password reset)
    dirs  = ["public", "pb_migrations"]

    info(f"Creating remote staging dir {remote_dir}...")
    subprocess.run(["ssh", host, f"mkdir -p {remote_dir}"], check=True)

    info("Uploading files...")
    for f in files:
        if Path(f).exists():
            subprocess.run(["scp", f, f"{host}:{remote_dir}/"], check=True)
            print(f"   {f}")

    for d in dirs:
        if Path(d).exists():
            subprocess.run(["scp", "-r", d, f"{host}:{remote_dir}/"], check=True)
            print(f"   {d}/")

    ok("Upload complete (including password reset pages)")

    info("Running update on server...")
    subprocess.run(["ssh", host,
                    f"cd {remote_dir} && python3 deploy.py update"], check=True)


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Work Match deployment tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  install     Full fresh install (venv, PocketBase, systemd, nginx)
  update      Copy files + restart FastAPI (keeps PocketBase running)
  fix-admin   Reset PocketBase admin password in SQLite
  status      Show service health
  logs        Tail service logs  [--service pocketbase]
  push        Upload from local machine via SCP then update server
              [--host ubuntu@server] [--dir ~/staging]
        """
    )
    parser.add_argument("command", choices=["install", "update", "fix-admin",
                                            "status", "logs", "push"])
    parser.add_argument("--service", default=None,
                        help="Service name for logs command")
    parser.add_argument("--host",    default=SSH_HOST,
                        help="SSH host for push command")
    parser.add_argument("--dir",     default=REMOTE_STAGE,
                        help="Remote staging dir for push command")

    args = parser.parse_args()

    dispatch = {
        "install":   cmd_install,
        "update":    cmd_update,
        "fix-admin": cmd_fix_admin,
        "status":    cmd_status,
        "logs":      lambda: cmd_logs(args.service),
        "push":      lambda: cmd_push(args.host, args.dir),
    }
    dispatch[args.command]()


if __name__ == "__main__":
    main()
