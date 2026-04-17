import sys
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="BRICK API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok", "service": "BRICK API", "message": "Backend running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/projects")
def list_projects():
    return {"projects": [], "total": 0}


@app.post("/projects")
def create_project():
    return {"success": True, "project": {"id": "demo", "name": "Demo Project"}}
