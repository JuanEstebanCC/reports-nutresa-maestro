from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import reports
from app.core.config import settings

app = FastAPI(
    title="Nutresa Maestro Reports API",
    description="API for generating reports from Nutresa Maestro database with subdomain support",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(reports.router, prefix="/api/v1", tags=["reports"])

@app.get("/")
async def root():
    return {"message": "Nutresa Maestro Reports API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
