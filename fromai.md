# BRICK Project - Render Deployment Summary

## Current Status (as of April 17, 2026)

### Services Deployed
- **Backend**: brick-api (srv-d7haa51f9bms73e9iekg) - https://brick-api.onrender.com
- **Frontend**: brick-frontend (srv-d7hacfe7r5hc73bn3f6g) - https://brick-frontend-z9dj.onrender.com

### Problem
Backend returns 500 Internal Server Error on all endpoints.

## Issues Discovered

1. **Path Resolution**: Config file uses `Path(__file__).resolve().parent.parent.parent` which resolves incorrectly on Render's filesystem. Render clones repo to `/opt/render/project/src`.

2. **Missing Dependencies**: 
   - `fitz` module not installed (tried switching to `pymupdf`)
   - Many optional dependencies like `llama-index`, `pinecone-client` may have import errors

3. **Start Command**: Was using `gunicorn` but FastAPI requires `uvicorn` for proper async

## Fixes Attempted

1. Created `app/config.py` with dynamic path detection
2. Added startup debug logging to `main.py`
3. Simplified `main.py` to minimal version (no imports)
4. Reduced `requirements.txt` to only essential packages
5. Changed start command from gunicorn to uvicorn (just now)

## Latest Deployment
- Commit: `8987d3b58ffc5291ceb0bdd7224bb9097d503cd9` - "fix: use pymupdf instead of fitz"
- Latest start command: `uvicorn app.main:app --host 0.0.0.0 --port 10000`
- Deployment ID: dep-d7hb0fdckfvc73eg1110 (status: build_in_progress)

## API Key for Render
```
Bearer rnd_Vfy6t8EaZ2g1YQ9rhYZcy9d6Bbsc
```

## What Was Working (Local Development)
- Projects workflow: create → upload PDFs → parse → chat with AI
- PDF parsing with PyMuPDF
- Groq API integration for Q&A
- Frontend at localhost:3000
- Backend at localhost:8000

## Next Steps for Next AI

1. **Check if latest deploy is live**:
```bash
curl https://brick-api.onrender.com/health
```

2. **If still failing**, check Render logs in dashboard or use API:
```bash
curl -H "Authorization: Bearer rnd_Vfy6t8EaZ2g1YQ9rhYZcy9d6Bbsc" \
  "https://api.render.com/v1/services/srv-d7haa51f9bms73e9iekg/deploys"
```

3. **Try these fixes**:
   - Ensure minimal main.py with no router imports works first
   - Then add routers back one by one
   - Make sure each service module handles import errors gracefully

4. **Alternative**: Delete and recreate backend service fresh

## GitHub Repo
https://github.com/LokajithPT/brick

## Files Key
- `brick/backend/app/main.py` - FastAPI app entry point
- `brick/backend/app/config.py` - Path configuration
- `brick/backend/requirements.txt` - Dependencies
- `brick/frontend/` - Next.js frontend