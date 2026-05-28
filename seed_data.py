"""
Seed sample data into PocketBase collections.
Run after PocketBase is running and collections are created.
Usage: python seed_data.py
"""
import httpx
import random
import os
import datetime as dt
from datetime import timedelta

PB_URL   = os.getenv("POCKETBASE_URL",    "http://127.0.0.1:8090")
PB_EMAIL = os.getenv("PB_ADMIN_EMAIL",    "admin@workmatch.com")
PB_PASS  = os.getenv("PB_ADMIN_PASSWORD", "admin123456")


def get_admin_token() -> str:
    r = httpx.post(f"{PB_URL}/api/admins/auth-with-password",
                   json={"identity": PB_EMAIL, "password": PB_PASS})
    r.raise_for_status()
    return r.json()["token"]


def clear_collection(token: str, name: str):
    headers = {"Authorization": token}
    r = httpx.get(f"{PB_URL}/api/collections/{name}/records",
                  headers=headers, params={"perPage": 500})
    for item in r.json().get("items", []):
        httpx.delete(f"{PB_URL}/api/collections/{name}/records/{item['id']}",
                     headers=headers)


def seed_applications(token: str):
    headers = {"Authorization": token}
    positions = [
        "Software Engineer", "Frontend Developer", "Backend Developer",
        "Full Stack Developer", "DevOps Engineer", "Data Scientist",
        "Product Manager", "UI/UX Designer", "QA Engineer", "Business Analyst"
    ]
    first_names = ["John", "Sarah", "Michael", "Emily", "David", "Jessica",
                   "Robert", "Lisa", "James", "Maria", "William", "Jennifer",
                   "Richard", "Linda", "Thomas", "Patricia", "Charles", "Nancy",
                   "Daniel", "Karen"]
    last_names  = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
                   "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez",
                   "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor",
                   "Moore", "Jackson", "Martin"]

    for _ in range(25):
        days_ago = random.randint(0, 90)
        created  = (dt.datetime.now(dt.timezone.utc) - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        data = {
            "full_name":   f"{fn} {ln}",
            "email":       f"{fn.lower()}.{ln.lower()}@email.com",
            "phone":       f"+91 {random.randint(70000,99999)} {random.randint(10000,99999)}",
            "position":    random.choice(positions),
            "cv_filename": f"{fn}_{ln}_Resume.pdf",
            "cv_path":     f"uploads/{fn}_{ln}_Resume.pdf",
            "consent":     True,
            "created":     created,
        }
        r = httpx.post(f"{PB_URL}/api/collections/applications/records",
                       headers=headers, json=data)
        if r.status_code not in (200, 201):
            print(f"  Warning: {r.status_code} - {r.text[:100]}")

    print("  ✅ 25 career applications added")


def seed_hire_talent(token: str):
    headers = {"Authorization": token}
    companies = [
        "Tech Innovations Inc", "Digital Solutions Ltd", "Cloud Systems Corp",
        "Data Analytics Pro", "Mobile Apps Studio", "Enterprise Software Co",
        "AI Research Labs", "Cyber Security Firm", "E-commerce Platform",
        "FinTech Solutions", "Healthcare Tech", "EdTech Ventures",
        "Gaming Studios", "Marketing Automation", "Logistics Tech"
    ]
    inquiries = [
        "We need 3 senior full-stack developers for a 6-month SaaS project.",
        "Looking for experienced DevOps engineers for cloud migration and CI/CD.",
        "Require 2 React developers and 1 Node.js backend developer.",
        "Need a team of 5 developers for enterprise application development.",
        "Seeking Python developers with ML/AI experience for data analytics.",
        "Looking for UI/UX designers and frontend developers for redesign.",
        "Need Java developers with Spring Boot for microservices architecture.",
        "Require mobile app developers (iOS and Android) for healthcare app.",
        "Looking for blockchain developers for a cryptocurrency exchange.",
        "Need full-stack developers with e-commerce experience.",
        "Seeking cloud architects and DevOps engineers for AWS setup.",
        "Require data engineers and analysts for big data pipeline.",
        "Looking for cybersecurity experts for penetration testing.",
        "Need Angular developers for enterprise dashboard application.",
        "Seeking Unity game developers for mobile gaming project."
    ]
    first_names = ["John", "Sarah", "Michael", "Emily", "David", "Jessica",
                   "Robert", "Lisa", "James", "Maria"]
    last_names  = ["Smith", "Johnson", "Williams", "Brown", "Jones",
                   "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]

    for i in range(15):
        days_ago = random.randint(0, 90)
        created  = (dt.datetime.now(dt.timezone.utc) - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        data = {
            "full_name":    f"{fn} {ln}",
            "company_name": companies[i],
            "email":        f"{fn.lower()}.{ln.lower()}@company.com",
            "phone":        f"+91 {random.randint(70000,99999)} {random.randint(10000,99999)}",
            "inquiry":      inquiries[i],
            "consent":      True,
            "created":      created,
        }
        r = httpx.post(f"{PB_URL}/api/collections/hire_talent/records",
                       headers=headers, json=data)
        if r.status_code not in (200, 201):
            print(f"  Warning: {r.status_code} - {r.text[:100]}")

    print("  ✅ 15 hire talent requests added")


def seed_jobs(token: str):
    headers = {"Authorization": token}

    # Clear existing
    existing = httpx.get(f"{PB_URL}/api/collections/hire_developer/records",
                         headers=headers, params={"perPage": 200}).json()
    for item in existing.get("items", []):
        httpx.delete(f"{PB_URL}/api/collections/hire_developer/records/{item['id']}",
                     headers=headers)

    jobs = [
        {"job_title": "Senior React Developer", "location": "Chennai / Remote", "type": "Full Time",
         "experience": "4-6 years", "openings": 3,
         "job_description": "Build scalable frontend applications using React, TypeScript and modern tooling. Work closely with design and backend teams.",
         "primary_skills": "React, TypeScript, Redux, REST APIs", "secondary_skills": "Docker, AWS, Jest"},
        {"job_title": "Node.js Backend Engineer", "location": "Chennai", "type": "Full Time",
         "experience": "3-5 years", "openings": 2,
         "job_description": "Design and build high-performance REST and GraphQL APIs. Own microservices end-to-end.",
         "primary_skills": "Node.js, Express, PostgreSQL, GraphQL", "secondary_skills": "Redis, Kubernetes, CI/CD"},
        {"job_title": "DevOps Engineer", "location": "Remote", "type": "Contract",
         "experience": "3-4 years", "openings": 1,
         "job_description": "Manage cloud infrastructure on AWS, set up CI/CD pipelines, and ensure system reliability.",
         "primary_skills": "AWS, Terraform, Docker, Kubernetes", "secondary_skills": "Python, Bash, Prometheus"},
        {"job_title": "Full Stack Developer", "location": "Chennai / Hybrid", "type": "Full Time",
         "experience": "2-4 years", "openings": 4,
         "job_description": "Work across the stack — React frontend and FastAPI/Django backend. Deliver features end-to-end.",
         "primary_skills": "React, Python, FastAPI, PostgreSQL", "secondary_skills": "Docker, Git, Linux"},
        {"job_title": "UI/UX Designer", "location": "Chennai", "type": "Full Time",
         "experience": "2-3 years", "openings": 1,
         "job_description": "Create intuitive user experiences for web and mobile products. Own design from wireframe to handoff.",
         "primary_skills": "Figma, User Research, Prototyping", "secondary_skills": "HTML/CSS, Motion Design"},
        {"job_title": "Data Engineer", "location": "Remote", "type": "Contract",
         "experience": "3-5 years", "openings": 2,
         "job_description": "Build and maintain data pipelines, ETL processes, and analytics infrastructure.",
         "primary_skills": "Python, Apache Spark, SQL, Airflow", "secondary_skills": "AWS Glue, dbt, Tableau"},
    ]

    for job in jobs:
        r = httpx.post(f"{PB_URL}/api/collections/hire_developer/records",
                       headers=headers, json=job)
        if r.status_code not in (200, 201):
            print(f"  Warning: {r.status_code} - {r.text[:100]}")

    print(f"  ✅ {len(jobs)} job listings added")


if __name__ == "__main__":
    print("🌱 Seeding PocketBase...")
    try:
        token = get_admin_token()
        print("  ✅ Admin authenticated")
    except Exception as e:
        print(f"  ❌ Auth failed: {e}")
        print("  Make sure PocketBase is running and admin credentials are correct.")
        exit(1)

    print("  Clearing existing data...")
    clear_collection(token, "applications")
    clear_collection(token, "hire_talent")

    seed_applications(token)
    seed_hire_talent(token)
    seed_jobs(token)
    print("✨ Done!")
