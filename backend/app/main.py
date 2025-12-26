"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .database import close_neo4j_driver
from .routers import chat, provisions

settings = get_settings()

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(chat.router)
app.include_router(provisions.router)


@app.on_event("shutdown")
def shutdown_event():
    """Cleanup on shutdown."""
    close_neo4j_driver()


@app.get("/")
def read_root():
    """Health check endpoint."""
    return {"status": "ok", "service": "Le Livre API"}
