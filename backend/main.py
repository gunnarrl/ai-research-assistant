# main.py

import fitz  # PyMuPDF
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # Import CORS Middleware
from typing import Annotated

# Import the summary generation function from our new module
from backend.services.gemini_service import generate_summary
from backend.utils.pdf_parser import extract_text_from_pdf

app = FastAPI(
    title="AI Research Assistant API",
    description="API for the AI Research Assistant application.",
    version="0.1.0",
)

origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def read_health_check():
    return {"status": "ok"}

@app.post("/summarize")
async def summarize_pdf(file: Annotated[UploadFile, File(description="A PDF file to summarize.")]):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF.")

    try:
        file_bytes = await file.read()
        
        # 1. Call the PDF parser utility
        extracted_text = extract_text_from_pdf(file_bytes)

        if not extracted_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from PDF. It may be empty or image-based."
            )

        # 2. Call the Gemini service
        summary = await generate_summary(extracted_text)

        return {"summary": summary}

    except HTTPException as e:
        raise e # Re-raise known HTTP exceptions
    except Exception as e:
        # Catch any other unexpected errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

