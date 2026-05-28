# Work Match Admin Dashboard

A professional admin dashboard for managing job applications and hire talent consultation requests.

## Features

- 📊 Analytics dashboard with charts and metrics
- 👥 Career applications management
- 💼 Hire talent requests tracking
- 📥 Export to Excel and PDF
- 🔐 Secure admin authentication
- 🎨 Clean, modern UI

## Quick Start with Docker

### Prerequisites
- Docker
- Docker Compose

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd backend
```

2. Build and run with Docker Compose:
```bash
docker-compose up -d
```

3. Access the dashboard:
- URL: http://localhost:8000
- Username: `admin`
- Password: `admin123`

### Add Sample Data

```bash
docker exec -it workmatch-admin python seed_data.py
```

## Manual Installation

### Prerequisites
- Python 3.11+
- pip

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python main.py
```

3. Access at http://localhost:8000

## Production Deployment

### For admin.theworkmatch.com

1. Update environment variables in `docker-compose.yml`:
```yaml
environment:
  - SECRET_KEY=your-secure-random-key
```

2. Build and deploy:
```bash
docker-compose up -d
```

3. Configure reverse proxy (Nginx):
```nginx
server {
    listen 80;
    server_name admin.theworkmatch.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

4. Setup SSL with Let's Encrypt:
```bash
certbot --nginx -d admin.theworkmatch.com
```

## Docker Commands

### Start the application
```bash
docker-compose up -d
```

### Stop the application
```bash
docker-compose down
```

### View logs
```bash
docker-compose logs -f
```

### Rebuild after changes
```bash
docker-compose up -d --build
```

### Access container shell
```bash
docker exec -it workmatch-admin bash
```

## Default Credentials

- **Username**: admin
- **Password**: admin123

⚠️ **Important**: Change the default password in production!

## API Endpoints

- `POST /api/auth/login` - Admin login
- `GET /admin/api/stats` - Dashboard statistics
- `GET /admin/api/applications` - Career applications
- `GET /admin/api/hire-talent` - Hire talent requests
- `GET /admin/api/export/excel` - Export to Excel
- `GET /admin/api/export/pdf` - Export to PDF

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript
- **Charts**: Chart.js
- **Authentication**: JWT

## License

MIT License
"# workmatch_backend" 
