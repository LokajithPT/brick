# BRICK: Marlette Residence Assistant

**Building Resource Indexing & Contextual Knowledge**

## Overview
AI-powered document assistant for querying architectural PDFs with image references.

## Demo Features
- [x] PDF text extraction (266 pages across 2 documents)
- [x] Page image extraction
- [x] Keyword search across documents
- [x] AI-powered answers (Groq)
- [x] Document index browser
- [x] Page image viewer

## Tech Stack (POC)
- **LLM:** Groq (Llama 3.1 8B) - Free tier
- **Parsing:** Local (PyMuPDF) - Free
- **Images:** Stored locally
- **Backend:** FastAPI
- **Frontend:** Next.js 14

## Documents Processed
- Marlette Permit Set: 59 pages
- Working Design Book: 207 pages

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/query | Query documents |
| GET | /api/documents | List documents |
| GET | /api/index/{namespace} | Browse by section |

## To Run
```bash
# Backend
cd brick/backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd brick/frontend
npm install
npm run dev
```

## Production Upgrade Path
For enterprise deployment:
1. **Claude 3.5 Sonnet** - Vision + Chat (best for technical drawings)
2. **LlamaParse** - Better PDF parsing with tables/schematics
3. **Pinecone** - Vector search for semantic queries
4. **Multi-user auth** - Team collaboration

## Sample Questions
- "What are the kitchen specifications?"
- "What flooring is specified?"
- "Show me the primary bath fixtures"
- "What appliances are in the guest kitchen?"
