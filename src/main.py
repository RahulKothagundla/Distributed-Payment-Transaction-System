from fastapi import FastAPI
from sqlalchemy import create_engine
from src.config import get_settings
from src.models.transaction import Base
from src.api import transactions
from src.database import get_db  # NEW: Import from database module
import logging

settings = get_settings()

# Database setup
engine = create_engine(settings.database_url)

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production-grade distributed payment processing system"
)

# Include routers
app.include_router(transactions.router)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Distributed Payment Transaction System",
        "version": settings.app_version,
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)