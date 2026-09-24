"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, SessionLocal, Base
from app.models import *  # noqa — registers all models with Base.metadata

# Import routers
from app.routers.auth_routes import router as auth_router
from app.routers.listings import router as listings_router
from app.routers.requirements import router as requirements_router
from app.routers.all_routes import (
    offers_router, assessments_router, quotes_router,
    orders_router, recovery_router, payments_router,
    messages_router, disputes_router, notifications_router,
    admin_router, uploads_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Seed demo data
    if settings.DEMO_MODE:
        from app.seed import seed_database
        db = SessionLocal()
        try:
            seed_database(db)
        finally:
            db.close()

    yield


app = FastAPI(
    title="Wast-e API",
    description="Marketplace for rejected recyclable materials — India",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(listings_router)
app.include_router(requirements_router)
app.include_router(offers_router)
app.include_router(assessments_router)
app.include_router(quotes_router)
app.include_router(orders_router)
app.include_router(recovery_router)
app.include_router(payments_router)
app.include_router(messages_router)
app.include_router(disputes_router)
app.include_router(notifications_router)
app.include_router(admin_router)
app.include_router(uploads_router)


@app.get("/api/health")
def health():
    return {"status": "ok", "demo_mode": settings.DEMO_MODE}
