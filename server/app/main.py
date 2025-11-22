from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base
from app.api import (
    auth_router, 
    users_router, 
    photos_router, 
    frames_router,
    generate_router, 
    orders_router, 
    subscription_router,
    questionnaire_router,
    questionnaire_public_router
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Art Painting Constructor API...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully")

    import os
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.GENERATED_IMAGES_DIR, exist_ok=True)
    
    yield

    print("Shutting down Art Painting Constructor API...")
    await engine.dispose()

app = FastAPI(
    title="Art Painting Constructor API",
    description="Backend API для сервиса создания картин по номерам",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Адрес вашего фронтенда
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/api/users", tags=["Users"])
app.include_router(photos_router, prefix="/api/photos", tags=["Photos"])
app.include_router(frames_router, prefix="/api/frames", tags=["Frames"])
app.include_router(generate_router, prefix="/api/generate", tags=["Generation"])
app.include_router(orders_router, prefix="/api/orders", tags=["Orders"])
app.include_router(subscription_router, prefix="/api/subscription", tags=["Subscription"])
app.include_router(questionnaire_router, prefix="/api/questionnaire", tags=["Questionnaire"])
app.include_router(questionnaire_public_router, prefix="/api/questionnaire-public", tags=["Questionnaire Public"])

@app.get("/")
async def root():
    return {
        "message": "Art Painting Constructor API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}