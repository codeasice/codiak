"""
FastAPI main application entry point for Codiak (React version).
Runs alongside the existing Streamlit app on port 8000.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import tools, text_tools

app = FastAPI(
    title="Codiak API",
    description="Backend API for the Codiak React frontend",
    version="0.1.0",
)

# Allow the Vite dev server (port 5173) and any local origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tools.router, prefix="/api")
app.include_router(text_tools.router, prefix="/api/tools")


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.1.0"}
