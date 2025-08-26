# main.py

from fastapi import FastAPI, File, UploadFile, HTTPException
from typing import Annotated

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


# 3. Define the PDF upload endpoint
@app.post("/summarize")
async def summarize_pdf(file: Annotated[UploadFile, File(description="A PDF file to summarize.")]):
    """
    Accepts a PDF file, validates its content type, and returns its metadata.
    This is the first step towards the full summarization feature.
    """
    # Validate the file's content type to ensure it's a PDF
    if file.content_type != "application/pdf":
        # If not a PDF, raise an HTTP 400 Bad Request error
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload a PDF document."
        )

    # On successful validation, return the file's metadata as a JSON response
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "detail": "File successfully uploaded and validated."
    }

