"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import time

from app.config import settings
from app.dependencies import lifespan
from app.api import chat, search, ingest, health, admin
from app.ui import routes as ui_routes
from app.utils.logging import get_logger, setup_logging

# Setup logging
setup_logging(settings.log_level, settings.log_file)
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Local RAG Assistant",
    description="A privacy-first knowledge management system",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Mount static files
app.mount("/static", StaticFiles(directory="app/ui/static"), name="static")

# Include API routers
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(ingest.router, prefix="/api/ingest", tags=["ingest"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

# Include UI routes
app.include_router(ui_routes.router)

@app.get("/", include_in_schema=False)
async def root():
    """Redirect to chat UI."""
    return RedirectResponse(url="/chat")