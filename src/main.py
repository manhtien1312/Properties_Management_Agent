from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from src.api import employees, assets, churn, procurement

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Properties Management API",
    description="Backend API for employee and asset management",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(employees.router)
app.include_router(assets.router)
app.include_router(churn.router)
app.include_router(procurement.router)


@app.get("/", tags=["root"])
def read_root():
    """Welcome endpoint"""
    return {
        "message": "Welcome to Properties Management API",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


@app.get("/health", tags=["health"])
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
