# Deployment Notes and Best Practices

## Critical: Single App Instance Pattern

### The Problem

If you create **two FastAPI app instances** in `main.py`, the second one will overwrite the first, causing:

- ❌ Missing lifespan events
- ❌ Missing CORS middleware
- ❌ Missing health endpoint
- ❌ Missing router configuration
- ❌ 404 errors on `/api/v1/docs` and all routes

### The Solution

**Always use the factory pattern with a single app instance:**

```python
# ✅ CORRECT - Single app instance via factory
def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        lifespan=lifespan,
        docs_url=f"{settings.API_V1_PREFIX}/docs",
        # ... all configuration
    )
    app.add_middleware(CORSMiddleware, ...)
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    return app

# Create the application instance ONCE
app = create_application()
```

```python
# ❌ WRONG - Two app instances (second overwrites first)
app = create_application()  # First instance with all config

app = FastAPI()  # Second instance - OVERWRITES first! All config lost!
```

### Current Implementation

Our `app/main.py` correctly implements the single instance pattern:

1. **Factory Function**: `create_application()` creates and configures the app
2. **Single Instance**: `app = create_application()` creates one instance
3. **No Duplicates**: No second `FastAPI()` call that would overwrite

### Verification

To verify your app is correctly configured:

```bash
# Check that docs are accessible
curl http://localhost:5055/api/v1/docs

# Check health endpoint
curl http://localhost:5055/health

# Check OpenAPI schema
curl http://localhost:5055/api/v1/openapi.json
```

All should return valid responses, not 404.

---

## Production Deployment Checklist

### 1. Environment Variables

Ensure `.env` or environment variables are set:

```env
DATABASE_URL=postgresql://user:password@host:5432/database
SECRET_KEY=your-super-secret-key-change-in-production
DEBUG=False
```

### 2. Database Migrations

```bash
# Run migrations before starting app
alembic upgrade head
```

### 3. Application Startup

**Using Uvicorn directly:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 5055 --workers 4
```

**Using Gunicorn with Uvicorn workers (recommended for production):**
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:5055
```

### 4. Reverse Proxy (Nginx)

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5055;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/v1/docs {
        proxy_pass http://127.0.0.1:5055;
        proxy_set_header Host $host;
    }
}
```

### 5. SSL/TLS (Let's Encrypt)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com
```

### 6. Process Management (Systemd)

Create `/etc/systemd/system/aerospace-api.service`:

```ini
[Unit]
Description=Aerospace Parts Material Management API
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/adsmmpyapi
Environment="PATH=/path/to/adsmmpyapi/venv/bin"
ExecStart=/path/to/adsmmpyapi/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 127.0.0.1:5055
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable aerospace-api
sudo systemctl start aerospace-api
sudo systemctl status aerospace-api
```

---

## Common Deployment Issues

### Issue: 404 on `/api/v1/docs`

**Cause:** Duplicate FastAPI app instances or incorrect router configuration.

**Solution:**
1. Verify `app/main.py` has only ONE `app = create_application()` line
2. Check that `create_application()` includes: `docs_url=f"{settings.API_V1_PREFIX}/docs"`
3. Ensure router is included: `app.include_router(api_router, prefix=settings.API_V1_PREFIX)`

### Issue: CORS Errors

**Cause:** CORS middleware not configured or wrong origins.

**Solution:**
1. Check `app/main.py` has CORS middleware added
2. Verify `settings.ALLOWED_ORIGINS` includes your frontend domain
3. For production, replace `["*"]` with specific domains

### Issue: Database Connection Errors

**Cause:** Wrong DATABASE_URL or database not accessible.

**Solution:**
1. Verify `.env` has correct `DATABASE_URL`
2. Test connection: `psql $DATABASE_URL`
3. Ensure database exists: `CREATE DATABASE aerospace_parts;`
4. Run migrations: `alembic upgrade head`

### Issue: Module Not Found Errors

**Cause:** Virtual environment not activated or dependencies not installed.

**Solution:**
1. Activate venv: `source venv/bin/activate` (Linux) or `.\venv\Scripts\activate.ps1` (Windows)
2. Install dependencies: `pip install -r requirements.txt`
3. Verify: `python -c "import sqlalchemy; print('OK')"`

---

## Performance Optimization

### 1. Worker Configuration

```bash
# Calculate workers: (2 x CPU cores) + 1
# For 4 cores: (2 x 4) + 1 = 9 workers
gunicorn app.main:app -w 9 -k uvicorn.workers.UvicornWorker
```

### 2. Database Connection Pooling

Ensure SQLAlchemy connection pool is configured in `app/db/session.py`:

```python
engine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)
```

### 3. Caching

Consider adding Redis for:
- Session storage
- API response caching
- Rate limiting

### 4. Static Files

For production, serve static files via Nginx, not FastAPI:

```nginx
location /static/ {
    alias /path/to/static/files/;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

---

## Monitoring and Logging

### 1. Application Logs

Configure logging in `app/core/config.py`:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
```

### 2. Health Checks

Use the `/health` endpoint for monitoring:

```bash
# Add to monitoring system
curl http://localhost:5055/health
```

### 3. Metrics

Consider adding:
- Prometheus metrics endpoint
- Application performance monitoring (APM)
- Error tracking (Sentry, Rollbar)

---

## Security Checklist

- [ ] Change `SECRET_KEY` in production
- [ ] Set `DEBUG=False` in production
- [ ] Use HTTPS (SSL/TLS)
- [ ] Configure CORS with specific origins (not `["*"]`)
- [ ] Use environment variables for secrets (not hardcoded)
- [ ] Enable rate limiting
- [ ] Use strong database passwords
- [ ] Regularly update dependencies
- [ ] Enable firewall rules
- [ ] Use database connection encryption

---

**Last Updated:** January 23, 2026
