"""
PocketBase setup: creates/updates all collections with correct schema and API rules.
- applications:   public create (anyone can submit a job application)
- hire_talent:    public create (anyone can submit a hire request)
- hire_developer: public list/view (frontend shows jobs), admin-only create/update/delete

Usage:
  1. Start PocketBase:  ./pocketbase.exe serve
  2. Run this script:   python setup_pb.py
"""
import httpx
import os
import time

PB_URL   = os.getenv("POCKETBASE_URL",    "http://127.0.0.1:8090")
PB_EMAIL = os.getenv("PB_ADMIN_EMAIL",    "admin@workmatch.com")
PB_PASS  = os.getenv("PB_ADMIN_PASSWORD", "admin123456")


def wait_for_pb(retries=15):
    for i in range(retries):
        try:
            r = httpx.get(f"{PB_URL}/api/health", timeout=3)
            if r.status_code == 200:
                print("  ✅ PocketBase is running")
                return True
        except Exception:
            pass
        print(f"  Waiting for PocketBase... ({i+1}/{retries})")
        time.sleep(2)
    return False


def get_admin_token() -> str:
    r = httpx.post(
        f"{PB_URL}/api/admins/auth-with-password",
        json={"identity": PB_EMAIL, "password": PB_PASS},
    )
    if r.status_code == 200:
        print("  ✅ Admin authenticated")
        return r.json()["token"]
    # First-time: no admins yet — use the setup endpoint
    print("  Creating admin account...")
    r2 = httpx.post(f"{PB_URL}/api/admins",
                    json={"email": PB_EMAIL, "password": PB_PASS,
                          "passwordConfirm": PB_PASS})
    if r2.status_code not in (200, 201):
        raise RuntimeError(f"Could not create admin: {r2.text}")
    r3 = httpx.post(
        f"{PB_URL}/api/admins/auth-with-password",
        json={"identity": PB_EMAIL, "password": PB_PASS},
    )
    r3.raise_for_status()
    print("  ✅ Admin created and authenticated")
    return r3.json()["token"]


# ── Collection schemas ─────────────────────────────────────────────────────────

COLLECTIONS = [
    {
        "name": "applications",
        # Public: anyone can create (submit application) and list/view
        "listRule":   "",
        "viewRule":   "",
        "createRule": "",
        "updateRule": None,   # admin only
        "deleteRule": None,   # admin only
        "schema": [
            {"name": "full_name", "type": "text",  "required": True,  "options": {}},
            {"name": "email",     "type": "email", "required": True,  "options": {}},
            {"name": "phone",     "type": "text",  "required": True,  "options": {}},
            {"name": "position",  "type": "text",  "required": True,  "options": {}},
            {
                "name": "cv",
                "type": "file",
                "required": False,
                "options": {
                    "maxSelect": 1,
                    "maxSize": 10485760,   # 10 MB
                    "mimeTypes": ["application/pdf",
                                  "application/msword",
                                  "application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
                    "protected": False,
                },
            },
            {"name": "consent", "type": "bool", "required": True, "options": {}},
        ],
    },
    {
        "name": "hire_talent",
        # Public: anyone can create (submit hire request) and list/view
        "listRule":   "",
        "viewRule":   "",
        "createRule": "",
        "updateRule": None,
        "deleteRule": None,
        "schema": [
            {"name": "full_name",    "type": "text",  "required": True,  "options": {}},
            {"name": "company_name", "type": "text",  "required": True,  "options": {}},
            {"name": "email",        "type": "email", "required": True,  "options": {}},
            {"name": "phone",        "type": "text",  "required": True,  "options": {}},
            {"name": "inquiry",      "type": "text",  "required": True,  "options": {}},
            {"name": "consent",      "type": "bool",  "required": True,  "options": {}},
        ],
    },
    {
        "name": "hire_developer",
        # Public list/view so frontend can display job listings
        # Only admin can create/update/delete jobs
        "listRule":   "",
        "viewRule":   "",
        "createRule": None,   # admin only
        "updateRule": None,   # admin only
        "deleteRule": None,   # admin only
        "schema": [
            {"name": "job_title",        "type": "text",   "required": True,  "options": {}},
            {"name": "location",         "type": "text",   "required": True,  "options": {}},
            {
                "name": "type",
                "type": "select",
                "required": True,
                "options": {"maxSelect": 1, "values": ["Full Time", "Contract"]},
            },
            {"name": "experience",       "type": "text",   "required": True,  "options": {}},
            {"name": "openings",         "type": "number", "required": True,
             "options": {"min": 1, "max": None, "noDecimal": True}},
            {"name": "job_description",  "type": "text",   "required": True,  "options": {}},
            {"name": "primary_skills",   "type": "text",   "required": True,  "options": {}},
            {"name": "secondary_skills", "type": "text",   "required": False, "options": {}},
        ],
    },
]


def get_collection_id(token: str, name: str):
    r = httpx.get(
        f"{PB_URL}/api/collections/{name}",
        headers={"Authorization": token},
    )
    if r.status_code == 200:
        return r.json()["id"]
    return None


def upsert_collection(token: str, col: dict):
    name    = col["name"]
    headers = {"Authorization": token}
    payload = {
        "name":       name,
        "type":       "base",
        "schema":     col["schema"],
        "listRule":   col.get("listRule"),
        "viewRule":   col.get("viewRule"),
        "createRule": col.get("createRule"),
        "updateRule": col.get("updateRule"),
        "deleteRule": col.get("deleteRule"),
    }

    col_id = get_collection_id(token, name)
    if col_id:
        # Update existing collection
        r = httpx.patch(
            f"{PB_URL}/api/collections/{col_id}",
            headers=headers,
            json=payload,
        )
        if r.status_code == 200:
            print(f"  ✅ Collection '{name}' updated (rules + schema)")
        else:
            print(f"  ❌ Failed to update '{name}': {r.status_code} - {r.text[:300]}")
    else:
        # Create new collection
        r = httpx.post(
            f"{PB_URL}/api/collections",
            headers=headers,
            json=payload,
        )
        if r.status_code in (200, 201):
            print(f"  ✅ Collection '{name}' created")
        else:
            print(f"  ❌ Failed to create '{name}': {r.status_code} - {r.text[:300]}")


if __name__ == "__main__":
    print("🔧 Setting up PocketBase collections...")
    print(f"   URL: {PB_URL}")
    print()

    if not wait_for_pb():
        print("❌ PocketBase not reachable. Start it first:")
        print("   Windows: .\\pocketbase.exe serve")
        print("   Linux:   ./pocketbase serve")
        exit(1)

    token = get_admin_token()
    print()

    for col in COLLECTIONS:
        upsert_collection(token, col)

    print()
    print("✨ Setup complete!")
    print(f"   Admin UI:  {PB_URL}/_/")
    print(f"   Email:     {PB_EMAIL}")
    print(f"   Password:  {PB_PASS}")
    print()
    print("Collections and API rules:")
    print("  applications   → public create + list/view, admin delete")
    print("  hire_talent    → public create + list/view, admin delete")
    print("  hire_developer → public list/view, admin create/update/delete")
