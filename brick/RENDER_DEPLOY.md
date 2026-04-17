# Deploy to Render.com

## 1. Backend Service

### Create Backend Service
```bash
# Connect your GitHub repo to Render
# Repository: your-repo/brick
```

**Settings:**
- Root Directory: `brick/backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app.main:app --workers 4 --bind 0.0.0.0:$PORT`

**Environment Variables:**
```
GROQ_API_KEY=gsk_xxxxxxxx
CORS_ORIGINS=https://your-frontend.onrender.com
NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
```

## 2. Frontend Service

### Create Frontend Service
**Settings:**
- Root Directory: `brick/frontend`
- Build Command: `npm run build`
- Start Command: `npm run start`

**Environment Variables:**
```
NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
```

## 3. Deploy Order

1. Deploy Backend first
2. Get backend URL
3. Update `NEXT_PUBLIC_API_URL` in frontend env
4. Deploy Frontend
5. Add frontend URL to backend's `CORS_ORIGINS`

## Quick Commands

```bash
# Test backend locally
cd brick/backend && source venv/bin/activate && gunicorn app.main:app --workers 4 --bind 0.0.0.0:8000

# Build frontend for production
cd brick/frontend && npm run build
```