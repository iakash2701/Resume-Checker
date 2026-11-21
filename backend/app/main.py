from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router as api_router
from app.database import engine, Base
import app.models  # Ensure models are registered

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="HireSwift API",
    description="Backend API for HireSwift ATS",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Welcome to HireSwift API", "docs": "/docs"}
