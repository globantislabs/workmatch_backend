# Work Match API Documentation

Base URL: `https://admin.theworkmatch.com`

---

## Authentication

All `/admin/api/*` endpoints require a Bearer token in the `Authorization` header.

```
Authorization: <token>
```

Obtain a token via `POST /api/auth/login`.

---

## Auth

### POST /api/auth/login

Login as admin.

**Body** (`multipart/form-data`)

| Field | Type | Required |
|-------|------|----------|
| username | string | yes |
| password | string | yes |

**Response 200**
```json
{
  "token": "eyJ...",
  "admin": { "id": "...", "email": "admin@workmatch.com" }
}
```

**Response 401** — Invalid credentials

---

## Public Forms

### POST /api/applications/submit

Submit a job application (public, no auth).

**Body** (`multipart/form-data`)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| full_name | string | yes | |
| email | string | yes | |
| phone | string | yes | |
| position | string | yes | |
| consent | boolean | yes | Must be `true` |
| cv | file | no | PDF/DOC upload |

**Response 200**
```json
{ "message": "Application submitted successfully" }
```

---

### POST /api/hire-talent/submit

Submit a hire talent / consultation request (public, no auth).

**Body** (`multipart/form-data`)

| Field | Type | Required |
|-------|------|----------|
| full_name | string | yes |
| company_name | string | yes |
| email | string | yes |
| phone | string | yes |
| inquiry | string | yes |
| consent | boolean | yes |

**Response 200**
```json
{ "message": "Consultation request submitted successfully" }
```

---

## Public Jobs

### GET /api/jobs

List all published job listings.

**Response 200**
```json
[
  {
    "id": "abc123",
    "job_title": "Senior React Developer",
    "location": "Chennai / Remote",
    "type": "Full Time",
    "experience": "4-6 years",
    "openings": 3,
    "job_description": "...",
    "primary_skills": "React, TypeScript",
    "secondary_skills": "Docker, AWS",
    "created_at": "2026-03-01 10:00:00"
  }
]
```

---

### GET /api/jobs/{job_id}

Get a single job by ID.

**Response 200** — Job object (same shape as above)
**Response 404** — Job not found

---

## Public Blogs

### GET /api/blogs

List blog posts. Returns published only by default.

**Query Params**

| Param | Type | Default | Notes |
|-------|------|---------|-------|
| published_only | boolean | true | Set `false` to include drafts |

**Response 200**
```json
[
  {
    "id": "xyz789",
    "title": "How to hire great developers",
    "slug": "how-to-hire-great-developers",
    "excerpt": "...",
    "author": "Work Match",
    "tags": "hiring, tech",
    "published": true,
    "banner_url": "https://admin.theworkmatch.com/api/files/blogs/.../banner.jpg",
    "created_at": "2026-03-01 10:00:00"
  }
]
```

---

### GET /api/blogs/{blog_id}

Get a single blog post (includes full `content` field).

**Response 200** — Blog object with `content`
**Response 404** — Not found

---

## Admin — Stats

### GET /admin/api/stats

Dashboard summary stats.

**Headers** — `Authorization: <token>`

**Response 200**
```json
{
  "total": 25,
  "totalHire": 15,
  "byPosition": [
    { "position": "Software Engineer", "count": 5 }
  ],
  "byMonth": [
    { "month": "2026-01", "count": 8 }
  ],
  "byMonthHire": [
    { "month": "2026-01", "count": 3 }
  ]
}
```

---

## Admin — Applications

### GET /admin/api/applications

List all job applications.

**Headers** — `Authorization: <token>`

**Query Params**

| Param | Type | Notes |
|-------|------|-------|
| position | string | Filter by position |
| startDate | string | `YYYY-MM-DD` |
| endDate | string | `YYYY-MM-DD` |
| search | string | Searches name, email, phone |

**Response 200**
```json
[
  {
    "id": "abc123",
    "full_name": "John Smith",
    "email": "john@email.com",
    "phone": "+91 98765 43210",
    "position": "Software Engineer",
    "cv_filename": "John_Smith_Resume.pdf",
    "cv_url": "http://127.0.0.1:8090/api/files/applications/abc123/John_Smith_Resume.pdf",
    "created_at": "2026-03-01 10:00:00"
  }
]
```

---

### DELETE /admin/api/applications/{rec_id}

Delete an application record.

**Headers** — `Authorization: <token>`

**Response 200**
```json
{ "message": "Deleted" }
```

**Response 404** — Not found

---

## Admin — Hire Talent

### GET /admin/api/hire-talent

List all hire talent / consultation requests.

**Headers** — `Authorization: <token>`

**Query Params**

| Param | Type | Notes |
|-------|------|-------|
| search | string | Searches name, company, email |
| startDate | string | `YYYY-MM-DD` |
| endDate | string | `YYYY-MM-DD` |

**Response 200**
```json
[
  {
    "id": "def456",
    "full_name": "Sarah Johnson",
    "company_name": "Tech Innovations Inc",
    "email": "sarah@company.com",
    "phone": "+91 98765 43210",
    "inquiry": "We need 3 senior developers...",
    "created_at": "2026-03-01 10:00:00"
  }
]
```

---

### DELETE /admin/api/hire-talent/{rec_id}

Delete a hire talent record.

**Headers** — `Authorization: <token>`

**Response 200**
```json
{ "message": "Deleted" }
```

---

## Admin — Jobs

### GET /admin/api/jobs

List all job listings (admin, includes unpublished).

**Headers** — `Authorization: <token>`

**Response 200** — Array of job objects

---

### POST /admin/api/jobs

Create a new job listing.

**Headers** — `Authorization: <token>`

**Body** (`multipart/form-data`)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| job_title | string | yes | |
| location | string | yes | |
| type | string | yes | `Full Time` or `Contract` |
| experience | string | yes | e.g. `3-5 years` |
| openings | integer | yes | |
| job_description | string | yes | |
| primary_skills | string | yes | Comma-separated |
| secondary_skills | string | no | Comma-separated |

**Response 200**
```json
{ "message": "Job created", "id": "abc123" }
```

---

### PUT /admin/api/jobs/{job_id}

Update an existing job listing. Same body fields as POST.

**Headers** — `Authorization: <token>`

**Response 200**
```json
{ "message": "Job updated" }
```

**Response 404** — Not found

---

### DELETE /admin/api/jobs/{job_id}

Delete a job listing.

**Headers** — `Authorization: <token>`

**Response 200**
```json
{ "message": "Job deleted" }
```

---

## Admin — Blogs

### GET /admin/api/blogs

List all blog posts including drafts.

**Headers** — `Authorization: <token>`

**Response 200** — Array of blog objects (includes `content` field)

---

### POST /admin/api/blogs

Create a new blog post.

**Headers** — `Authorization: <token>`

**Body** (`multipart/form-data`)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| title | string | yes | |
| slug | string | yes | URL-friendly identifier |
| excerpt | string | no | Short summary |
| content | string | yes | Full HTML/markdown content |
| author | string | no | |
| tags | string | no | Comma-separated |
| published | boolean | no | Default `false` |
| banner | file | no | Image upload |

**Response 200**
```json
{ "message": "Blog created", "id": "xyz789" }
```

---

### PUT /admin/api/blogs/{blog_id}

Update a blog post. Same body fields as POST.

**Headers** — `Authorization: <token>`

**Response 200**
```json
{ "message": "Blog updated" }
```

**Response 404** — Not found

---

### DELETE /admin/api/blogs/{blog_id}

Delete a blog post.

**Headers** — `Authorization: <token>`

**Response 200**
```json
{ "message": "Blog deleted" }
```

---

## Admin — Exports

### GET /admin/api/export/excel

Download all applications as an Excel file.

**Headers** — `Authorization: <token>`

**Response 200** — `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
Filename: `applications.xlsx`

---

### GET /admin/api/export/pdf

Download all applications as a PDF report.

**Headers** — `Authorization: <token>`

**Response 200** — `application/pdf`
Filename: `applications.pdf`

---

## Error Responses

| Status | Meaning |
|--------|---------|
| 400 | Bad request / validation error |
| 401 | Missing or invalid token |
| 404 | Record not found |
| 422 | Missing required fields |
| 500 | Server error |

```json
{ "detail": "Error message here" }
```


---

## Admin — Change Password

### POST /admin/api/change-password

Change the logged-in admin's password.

**Headers** — `Authorization: <token>`

**Body** (`multipart/form-data`)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| oldPassword | string | yes | Current password |
| password | string | yes | New password (min 8 chars) |
| passwordConfirm | string | yes | Must match password |

**Response 200**
```json
{ "message": "Password changed successfully" }
```

**Response 400** — Validation error (passwords don't match, too short, etc.)
**Response 401** — Current password is incorrect

---
