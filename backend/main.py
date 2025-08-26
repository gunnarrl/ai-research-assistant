# main.py

from fastapi import FastAPI

# 1. Create an instance of the FastAPI class
app = FastAPI(
    title="AI Research Assistant API",
    description="API for the AI Research Assistant application.",
    version="0.1.0",
)

# 2. Define the health check endpoint
@app.get("/health")
def read_health_check():
    """
    This endpoint can be used to verify that the
    API server is running and responsive.
    """
    return {"status": "ok"}