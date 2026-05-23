from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.routers import macro as macro_router
from backend.routers import portfolio as portfolio_router

app = FastAPI(title="Bond Signal API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(macro_router.router, prefix="/api")
app.include_router(portfolio_router.router, prefix="/api")

# Serve React build when it exists (production mode)
_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if _dist.exists():
    app.mount("/", StaticFiles(directory=str(_dist), html=True), name="static")
