"""
FastAPI main application entry point for Codiak (React version).
Runs alongside the existing Streamlit app on port 8000.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import tools, text_tools
from api.routers.dragon_keeper import router as dk_router

app = FastAPI(
    title="Codiak API",
    description="Backend API for the Codiak React frontend",
    version="0.1.0",
)

# Allow any localhost origin (covers port changes, IPv4/IPv6 variants)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tools.router, prefix="/api")
app.include_router(text_tools.router, prefix="/api/tools")
app.include_router(dk_router, prefix="/api/dragon-keeper")


@app.on_event("startup")
def startup_event():
    from api.models.dragon_keeper.db import run_migrations
    run_migrations()


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.1.0"}
