#!/usr/bin/env python3
"""
Minimal FastAPI app to test if the issue is with our configuration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create minimal FastAPI application
app = FastAPI(
    title="Test App",
    version="1.0.0",
    description="Minimal test app",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Test API working"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("test_minimal:app", host="127.0.0.1", port=8002, reload=True)
