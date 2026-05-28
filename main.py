from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import httpx, os, io, time, asyncio
from typing import Optional

app = FastAPI()

# CORS configuration - properly configured for production
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
security = HTTPBearer()
PB_URL = os.getenv("POCKETBASE_URL", "http://127.0.0.1:8090")
PB_PUBLIC_URL = "https://admin.theworkmatch.com"

# ── Shared persistent client — reuses TCP connections ─────────────────────────
_http: httpx.AsyncClient | None = None

def http() -> httpx.AsyncClient:
    global _http
    if _http is None or _http.is_closed:
        _http = httpx.AsyncClient(
            base_url=PB_URL, timeout=10.0,
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
    return _http

@app.on_event("shutdown")
async def _shutdown():
    if _http and not _http.is_closed:
        await _http.aclose()

# ── Cached admin token — re-auths only once per day ───────────────────────────
_tok: dict = {"v": None, "exp": 0}
_tok_lock = asyncio.Lock()

async def pb_token() -> str:
    now = time.time()
    if _tok["v"] and now < _tok["exp"] - 300:
        return _tok["v"]
    async with _tok_lock:
        if _tok["v"] and now < _tok["exp"] - 300:
            return _tok["v"]
        r = await http().post("/api/admins/auth-with-password", json={
            "identity": os.getenv("PB_ADMIN_EMAIL", "admin@workmatch.com"),
            "password": os.getenv("PB_ADMIN_PASSWORD", "admin123456"),
        })
        r.raise_for_status()
        _tok["v"] = r.json()["token"]
        _tok["exp"] = now + 86400
        return _tok["v"]

async def verify_token(creds: HTTPAuthorizationCredentials = Depends(security)):
    # HTTPBearer extracts just the token, we need to add "Bearer " prefix for PocketBase
    r = await http().post("/api/admins/auth-refresh", 
                         headers={"Authorization": f"Bearer {creds.credentials}"})
    if r.status_code != 200:
        raise HTTPException(401, "Invalid or expired session")
    return r.json()["admin"]

def items(r: dict) -> list:
    return r.get("items", [])

def auth(t: str) -> dict:
    return {"Authorization": t}


# ── Static & pages ────────────────────────────────────────────────────────────
app.mount("/static",  StaticFiles(directory="public"),  name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
async def root(): return FileResponse("public/admin-responsive.html")

@app.get("/admin")
async def admin_page(): return FileResponse("public/admin-responsive.html")

@app.get("/admin/login")
async def login_page(): return FileResponse("public/login.html")

@app.post("/api/auth/request-password-reset")
async def request_password_reset(email: str = Form()):
    """Request password reset - sends reset link to admin email"""
    t = await pb_token()
    r = await http().post("/api/admins/request-password-reset",
                          headers=auth(t), json={"email": email})
    if r.status_code != 200:
        # Don't reveal if email exists or not for security
        return {"message": "If the email exists, a reset link has been sent"}
    return {"message": "If the email exists, a reset link has been sent"}

@app.post("/api/auth/confirm-password-reset")
async def confirm_password_reset(
    token: str = Form(), password: str = Form(), passwordConfirm: str = Form()
):
    """Confirm password reset with token"""
    r = await http().post("/api/admins/confirm-password-reset",
                          json={"token": token, "password": password,
                                "passwordConfirm": passwordConfirm})
    if r.status_code != 200:
        raise HTTPException(400, "Invalid or expired reset token")
    return {"message": "Password reset successfully"}


# ── Auth ──────────────────────────────────────────────────────────────────────
@app.post("/api/auth/login")
async def login(username: str = Form(), password: str = Form()):
    r = await http().post("/api/admins/auth-with-password",
                          json={"identity": username, "password": password})
    if r.status_code != 200:
        raise HTTPException(401, "Invalid credentials")
    d = r.json()
    return {"token": d["token"], "admin": d["admin"]}

# ── Public form submissions ───────────────────────────────────────────────────
@app.post("/api/applications/submit")
async def submit_application(
    full_name: str = Form(), email: str = Form(), phone: str = Form(),
    position: str = Form(), consent: bool = Form(), cv: UploadFile = File(None),
):
    if not consent:
        raise HTTPException(400, "Consent is required")
    t = await pb_token()
    cv_bytes = await cv.read() if cv else None
    if cv_bytes:
        r = await http().post("/api/collections/applications/records",
            headers=auth(t),
            data={"full_name": full_name, "email": email, "phone": phone,
                  "position": position, "consent": "true"},
            files={"cv": (cv.filename, cv_bytes, cv.content_type or "application/octet-stream")})
    else:
        r = await http().post("/api/collections/applications/records",
            headers=auth(t),
            json={"full_name": full_name, "email": email, "phone": phone,
                  "position": position, "consent": consent})
    r.raise_for_status()
    return {"message": "Application submitted successfully"}

@app.post("/api/hire-talent/submit")
async def submit_hire_talent(
    full_name: str = Form(), company_name: str = Form(), email: str = Form(),
    phone: str = Form(), inquiry: str = Form(), consent: bool = Form(),
):
    if not consent:
        raise HTTPException(400, "Consent is required")
    t = await pb_token()
    r = await http().post("/api/collections/hire_talent/records", headers=auth(t),
        json={"full_name": full_name, "company_name": company_name, "email": email,
              "phone": phone, "inquiry": inquiry, "consent": consent})
    r.raise_for_status()
    return {"message": "Consultation request submitted successfully"}

# ── Admin stats — parallel PB queries ────────────────────────────────────────
@app.get("/admin/api/stats")
async def get_stats(user: dict = Depends(verify_token)):
    t = await pb_token()
    h = auth(t)
    # Fire both queries simultaneously
    apps_r, hire_r = await asyncio.gather(
        http().get("/api/collections/applications/records", headers=h, params={"perPage": 500}),
        http().get("/api/collections/hire_talent/records",  headers=h, params={"perPage": 500}),
    )
    apps  = items(apps_r.json())
    hires = items(hire_r.json())
    pos_count, month_count, hire_month = {}, {}, {}
    for a in apps:
        pos_count[a["position"]] = pos_count.get(a["position"], 0) + 1
        m = a["created"][:7]; month_count[m] = month_count.get(m, 0) + 1
    for h in hires:
        m = h["created"][:7]; hire_month[m] = hire_month.get(m, 0) + 1
    return {
        "total":       len(apps),
        "totalHire":   len(hires),
        "byPosition":  [{"position": k, "count": v} for k, v in pos_count.items()],
        "byMonth":     [{"month": k, "count": v} for k, v in sorted(month_count.items())],
        "byMonthHire": [{"month": k, "count": v} for k, v in sorted(hire_month.items())],
    }

@app.get("/admin/api/applications")
async def get_applications(
    position: Optional[str] = Query(None), startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None), search: Optional[str] = Query(None),
    user: dict = Depends(verify_token),
):
    t = await pb_token()
    f = []
    if position:  f.append(f'position="{position}"')
    if startDate: f.append(f'created>="{startDate} 00:00:00"')
    if endDate:   f.append(f'created<="{endDate} 23:59:59"')
    if search:    f.append(f'(full_name~"{search}"||email~"{search}"||phone~"{search}")')
    params = {"perPage": 500, "sort": "-created"}
    if f: params["filter"] = "&&".join(f)
    r = await http().get("/api/collections/applications/records", headers=auth(t), params=params)
    return [{
        "id": a["id"], "full_name": a["full_name"], "email": a["email"],
        "phone": a["phone"], "position": a["position"],
        "cv_filename": a.get("cv", ""),
        "cv_url": f"{PB_PUBLIC_URL}/api/files/applications/{a['id']}/{a['cv']}" if a.get("cv") else "",
        "created_at": a["created"],
    } for a in items(r.json())]

@app.get("/admin/api/applications/{rec_id}")
async def get_application(rec_id: str, user: dict = Depends(verify_token)):
    t = await pb_token()
    r = await http().get(f"/api/collections/applications/records/{rec_id}", headers=auth(t))
    if r.status_code == 404: raise HTTPException(404, "Not found")
    a = r.json()
    return {
        "id": a["id"], "full_name": a["full_name"], "email": a["email"],
        "phone": a["phone"], "position": a["position"],
        "cv_filename": a.get("cv", ""),
        "cv_url": f"{PB_PUBLIC_URL}/api/files/applications/{a['id']}/{a['cv']}" if a.get("cv") else "",
        "created_at": a["created"],
    }

@app.put("/admin/api/applications/{rec_id}")
async def update_application(
    rec_id: str, full_name: str = Form(), email: str = Form(),
    phone: str = Form(), position: str = Form(), user: dict = Depends(verify_token)
):
    t = await pb_token()
    r = await http().patch(f"/api/collections/applications/records/{rec_id}",
        headers=auth(t),
        json={"full_name": full_name, "email": email, "phone": phone, "position": position})
    if r.status_code == 404: raise HTTPException(404, "Not found")
    r.raise_for_status()
    return {"message": "Application updated"}


@app.get("/admin/api/hire-talent")
async def get_hire_talent(
    search: Optional[str] = Query(None), startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None), user: dict = Depends(verify_token),
):
    t = await pb_token()
    f = []
    if startDate: f.append(f'created>="{startDate} 00:00:00"')
    if endDate:   f.append(f'created<="{endDate} 23:59:59"')
    if search:    f.append(f'(full_name~"{search}"||company_name~"{search}"||email~"{search}")')
    params = {"perPage": 500, "sort": "-created"}
    if f: params["filter"] = "&&".join(f)
    r = await http().get("/api/collections/hire_talent/records", headers=auth(t), params=params)
    return [{
        "id": h["id"], "full_name": h["full_name"], "company_name": h["company_name"],
        "email": h["email"], "phone": h["phone"], "inquiry": h.get("inquiry", ""),
        "created_at": h["created"],
    } for h in items(r.json())]

@app.get("/admin/api/hire-talent/{rec_id}")
async def get_hire_talent_record(rec_id: str, user: dict = Depends(verify_token)):
    t = await pb_token()
    r = await http().get(f"/api/collections/hire_talent/records/{rec_id}", headers=auth(t))
    if r.status_code == 404: raise HTTPException(404, "Not found")
    h = r.json()
    return {
        "id": h["id"], "full_name": h["full_name"], "company_name": h["company_name"],
        "email": h["email"], "phone": h["phone"], "inquiry": h.get("inquiry", ""),
        "created_at": h["created"],
    }

@app.put("/admin/api/hire-talent/{rec_id}")
async def update_hire_talent(
    rec_id: str, full_name: str = Form(), company_name: str = Form(),
    email: str = Form(), phone: str = Form(), inquiry: str = Form(),
    user: dict = Depends(verify_token)
):
    t = await pb_token()
    r = await http().patch(f"/api/collections/hire_talent/records/{rec_id}",
        headers=auth(t),
        json={"full_name": full_name, "company_name": company_name, "email": email,
              "phone": phone, "inquiry": inquiry})
    if r.status_code == 404: raise HTTPException(404, "Not found")
    r.raise_for_status()
    return {"message": "Hire talent record updated"}


@app.delete("/admin/api/applications/{rec_id}")
async def delete_application(rec_id: str, user: dict = Depends(verify_token)):
    t = await pb_token()
    r = await http().delete(f"/api/collections/applications/records/{rec_id}", headers=auth(t))
    if r.status_code == 404: raise HTTPException(404, "Not found")
    return {"message": "Deleted"}

@app.delete("/admin/api/hire-talent/{rec_id}")
async def delete_hire_talent(rec_id: str, user: dict = Depends(verify_token)):
    t = await pb_token()
    r = await http().delete(f"/api/collections/hire_talent/records/{rec_id}", headers=auth(t))
    if r.status_code == 404: raise HTTPException(404, "Not found")
    return {"message": "Deleted"}


# ── Jobs ──────────────────────────────────────────────────────────────────────
@app.get("/api/jobs")
async def list_jobs():
    r = await http().get("/api/collections/hire_developer/records",
                         params={"perPage": 200, "sort": "-created"})
    return _fmt_jobs(items(r.json()))

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    r = await http().get(f"/api/collections/hire_developer/records/{job_id}")
    if r.status_code == 404: raise HTTPException(404, "Job not found")
    return _fmt_job(r.json())

@app.get("/admin/api/jobs")
async def admin_list_jobs(user: dict = Depends(verify_token)):
    try:
        t = await pb_token()
        r = await http().get("/api/collections/hire_developer/records",
                             headers=auth(t), params={"perPage": 200, "sort": "-created"})
        r.raise_for_status()
        return _fmt_jobs(items(r.json()))
    except Exception as e:
        return []

@app.post("/admin/api/jobs")
async def create_job(
    job_title: str = Form(), location: str = Form(), type: str = Form(),
    experience: str = Form(), openings: int = Form(), job_description: str = Form(),
    primary_skills: str = Form(), secondary_skills: str = Form(""),
    user: dict = Depends(verify_token),
):
    if type not in ("Full Time", "Contract"):
        raise HTTPException(400, "type must be 'Full Time' or 'Contract'")
    t = await pb_token()
    r = await http().post("/api/collections/hire_developer/records", headers=auth(t),
        json={"job_title": job_title, "location": location, "type": type,
              "experience": experience, "openings": openings,
              "job_description": job_description, "primary_skills": primary_skills,
              "secondary_skills": secondary_skills})
    r.raise_for_status()
    return {"message": "Job created", "id": r.json()["id"]}

@app.put("/admin/api/jobs/{job_id}")
async def update_job(
    job_id: str, job_title: str = Form(), location: str = Form(), type: str = Form(),
    experience: str = Form(), openings: int = Form(), job_description: str = Form(),
    primary_skills: str = Form(), secondary_skills: str = Form(""),
    user: dict = Depends(verify_token),
):
    t = await pb_token()
    r = await http().patch(f"/api/collections/hire_developer/records/{job_id}",
        headers=auth(t),
        json={"job_title": job_title, "location": location, "type": type,
              "experience": experience, "openings": openings,
              "job_description": job_description, "primary_skills": primary_skills,
              "secondary_skills": secondary_skills})
    if r.status_code == 404: raise HTTPException(404, "Job not found")
    r.raise_for_status()
    return {"message": "Job updated"}

@app.delete("/admin/api/jobs/{job_id}")
async def delete_job(job_id: str, user: dict = Depends(verify_token)):
    t = await pb_token()
    r = await http().delete(f"/api/collections/hire_developer/records/{job_id}", headers=auth(t))
    if r.status_code == 404: raise HTTPException(404, "Job not found")
    return {"message": "Job deleted"}

def _fmt_job(j: dict) -> dict:
    return {"id": j["id"], "job_title": j["job_title"], "location": j["location"],
            "type": j["type"], "experience": j["experience"], "openings": j["openings"],
            "job_description": j["job_description"], "primary_skills": j["primary_skills"],
            "secondary_skills": j.get("secondary_skills", ""), "created_at": j["created"]}

def _fmt_jobs(lst: list) -> list:
    return [_fmt_job(j) for j in lst]


# ── Blogs ─────────────────────────────────────────────────────────────────────
def _fmt_blog(b: dict, full: bool = False) -> dict:
    d = {"id": b["id"], "title": b["title"], "slug": b["slug"],
         "excerpt": b.get("excerpt", ""), "author": b.get("author", ""),
         "tags": b.get("tags", ""), "published": b.get("published", False),
         "banner_url": f"{PB_PUBLIC_URL}/api/files/blogs/{b['id']}/{b['banner']}" if b.get("banner") else "",
         "created_at": b["created"]}
    if full: d["content"] = b.get("content", "")
    return d

@app.get("/api/blogs")
async def list_blogs(published_only: bool = Query(True)):
    params = {"perPage": 200, "sort": "-created"}
    if published_only: params["filter"] = "published=true"
    r = await http().get("/api/collections/blogs/records", params=params)
    return [_fmt_blog(b) for b in items(r.json())]

@app.get("/api/blogs/slug/{slug}")
async def get_blog_by_slug(slug: str):
    """Fetch a blog post by its URL slug"""
    r = await http().get("/api/collections/blogs/records", 
                         params={"filter": f'slug="{slug}"', "perPage": 1})
    results = items(r.json())
    if not results:
        raise HTTPException(404, "Blog post not found")
    return _fmt_blog(results[0], full=True)

@app.get("/api/blogs/{blog_id_or_slug}")
async def get_blog(blog_id_or_slug: str):
    """Fetch a blog by ID or slug (auto-detects which one)"""
    # If it looks like a PocketBase ID (15 char alphanumeric), try ID first
    if len(blog_id_or_slug) == 15 and blog_id_or_slug.isalnum():
        r = await http().get(f"/api/collections/blogs/records/{blog_id_or_slug}")
        if r.status_code == 200:
            return _fmt_blog(r.json(), full=True)
    # Otherwise, search by slug
    r = await http().get("/api/collections/blogs/records", 
                         params={"filter": f'slug="{blog_id_or_slug}"', "perPage": 1})
    results = items(r.json())
    if not results:
        raise HTTPException(404, "Blog post not found")
    return _fmt_blog(results[0], full=True)

@app.get("/admin/api/blogs")
async def admin_list_blogs(user: dict = Depends(verify_token)):
    try:
        t = await pb_token()
        r = await http().get("/api/collections/blogs/records",
                             headers=auth(t), params={"perPage": 200, "sort": "-created"})
        r.raise_for_status()
        return [_fmt_blog(b, full=True) for b in items(r.json())]
    except Exception as e:
        # Return empty list if collection doesn't exist or is empty
        return []

@app.post("/admin/api/blogs")
async def create_blog(
    title: str = Form(), slug: str = Form(), excerpt: str = Form(""),
    content: str = Form(), author: str = Form(""), tags: str = Form(""),
    published: bool = Form(False), banner: UploadFile = File(None),
    user: dict = Depends(verify_token),
):
    t = await pb_token()
    data = {"title": title, "slug": slug, "excerpt": excerpt, "content": content,
            "author": author, "tags": tags, "published": "true" if published else "false"}
    if banner and banner.filename:
        img = await banner.read()
        r = await http().post("/api/collections/blogs/records", headers=auth(t),
                              data=data, files={"banner": (banner.filename, img, banner.content_type or "image/jpeg")})
    else:
        r = await http().post("/api/collections/blogs/records", headers=auth(t),
                              json={**data, "published": published})
    r.raise_for_status()
    return {"message": "Blog created", "id": r.json()["id"]}

@app.put("/admin/api/blogs/{blog_id}")
async def update_blog(
    blog_id: str, title: str = Form(), slug: str = Form(), excerpt: str = Form(""),
    content: str = Form(), author: str = Form(""), tags: str = Form(""),
    published: bool = Form(False), banner: UploadFile = File(None),
    user: dict = Depends(verify_token),
):
    t = await pb_token()
    data = {"title": title, "slug": slug, "excerpt": excerpt, "content": content,
            "author": author, "tags": tags, "published": "true" if published else "false"}
    if banner and banner.filename:
        img = await banner.read()
        r = await http().patch(f"/api/collections/blogs/records/{blog_id}", headers=auth(t),
                               data=data, files={"banner": (banner.filename, img, banner.content_type or "image/jpeg")})
    else:
        r = await http().patch(f"/api/collections/blogs/records/{blog_id}", headers=auth(t),
                               json={**data, "published": published})
    if r.status_code == 404: raise HTTPException(404, "Blog not found")
    r.raise_for_status()
    return {"message": "Blog updated"}

@app.delete("/admin/api/blogs/{blog_id}")
async def delete_blog(blog_id: str, user: dict = Depends(verify_token)):
    t = await pb_token()
    r = await http().delete(f"/api/collections/blogs/records/{blog_id}", headers=auth(t))
    if r.status_code == 404: raise HTTPException(404, "Blog not found")
    return {"message": "Blog deleted"}


# ── Export ────────────────────────────────────────────────────────────────────
@app.get("/admin/api/export/excel")
async def export_excel(user: dict = Depends(verify_token)):
    from openpyxl import Workbook
    t = await pb_token()
    r = await http().get("/api/collections/applications/records",
                         headers=auth(t), params={"perPage": 500, "sort": "-created"})
    rows = items(r.json())
    wb = Workbook(); ws = wb.active; ws.title = "Applications"
    ws.append(["#", "Full Name", "Email", "Phone", "Position", "CV Filename", "Submitted At"])
    for i, a in enumerate(rows, 1):
        ws.append([i, a["full_name"], a["email"], a["phone"], a["position"], a.get("cv", ""), a["created"]])
    out = io.BytesIO(); wb.save(out); out.seek(0)
    return StreamingResponse(out,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=applications.xlsx"})

@app.get("/admin/api/export/pdf")
async def export_pdf(user: dict = Depends(verify_token)):
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    t = await pb_token()
    r = await http().get("/api/collections/applications/records",
                         headers=auth(t), params={"perPage": 500, "sort": "-created"})
    rows = items(r.json())
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    h1   = ParagraphStyle("h1",   parent=styles["Heading1"], fontSize=20, textColor=colors.HexColor("#0f62fe"), alignment=TA_CENTER, spaceAfter=6)
    addr = ParagraphStyle("addr", parent=styles["Normal"],   fontSize=10, alignment=TA_CENTER, spaceAfter=3)
    h2   = ParagraphStyle("h2",   parent=styles["Heading2"], fontSize=14, alignment=TA_CENTER, spaceAfter=20)
    elems = [
        Paragraph("<b>The Work Match</b>", h1),
        Paragraph("Old No 178/B1, New No 766/1,", addr),
        Paragraph("Shakthi Towers 1, Thousand Lights, Annasalai, Chennai - 600 002", addr),
        Spacer(1, 0.3*inch), Paragraph("<b>Job Applications Report</b>", h2), Spacer(1, 0.2*inch),
    ]
    data = [["S.No", "Full Name", "Email", "Phone", "Position", "Resume", "Date"]]
    for i, a in enumerate(rows, 1):
        cv = a.get("cv", ""); link = f'<link href="{PB_URL}/api/files/applications/{a["id"]}/{cv}" color="blue"><u>{cv or "N/A"}</u></link>'
        data.append([str(i), a["full_name"], a["email"], a["phone"], a["position"], Paragraph(link, styles["Normal"]), a["created"][:10]])
    tbl = Table(data, colWidths=[0.5*inch,1.2*inch,1.5*inch,1*inch,1.2*inch,1.3*inch,1*inch])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#0f62fe")),("TEXTCOLOR",(0,0),(-1,0),colors.whitesmoke),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,0),10),("BOTTOMPADDING",(0,0),(-1,0),12),
        ("GRID",(0,0),(-1,-1),0.5,colors.grey),("FONTSIZE",(0,1),(-1,-1),8),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f0f4ff")]),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    elems.append(tbl); doc.build(elems); buf.seek(0)
    return StreamingResponse(buf, media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=applications.pdf"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# ── Password Reset Pages ─────────────────────────────────────────────────────
@app.get("/admin/forgot-password")
async def forgot_password_page(): return FileResponse("public/forgot-password.html")

@app.get("/admin/reset-password")
async def reset_password_page(): return FileResponse("public/reset-password.html")


# ── Change Password ───────────────────────────────────────────────────────────
@app.post("/admin/api/change-password")
async def change_password(
    oldPassword: str = Form(), password: str = Form(), 
    passwordConfirm: str = Form(), user: dict = Depends(verify_token)
):
    """Change admin password - requires current password verification"""
    if password != passwordConfirm:
        raise HTTPException(400, "Passwords do not match")
    if len(password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters")
    
    # Verify old password first
    r = await http().post("/api/admins/auth-with-password",
                          json={"identity": user["email"], "password": oldPassword})
    if r.status_code != 200:
        raise HTTPException(401, "Current password is incorrect")
    
    # Update password
    t = await pb_token()
    r = await http().patch(f"/api/admins/{user['id']}",
                           headers=auth(t),
                           json={"password": password, "passwordConfirm": passwordConfirm})
    if r.status_code != 200:
        raise HTTPException(400, "Failed to update password")
    
    return {"message": "Password changed successfully"}
