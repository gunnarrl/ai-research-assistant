# main.py

import fitz  # PyMuPDF
from fastapi import FastAPI, File, UploadFile, HTTPException
from typing import Annotated

# Import the summary generation function from our new module
from gemini_service import generate_summary

# Create an instance of the FastAPI class
app = FastAPI(
    title="AI Research Assistant API",
    description="API for the AI Research Assistant application.",
    version="0.1.0",
)

@app.get("/health")
def read_health_check():
    """
    Health check endpoint to verify API is running.
    """
    return {"status": "ok"}


@app.post("/summarize")
async def summarize_pdf(file: Annotated[UploadFile, File(description="A PDF file to summarize.")]):
    """
    Accepts a PDF, extracts text, and returns an AI-generated summary.
    """
    # Validate the file's content type
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload a PDF document."
        )

    try:
        # Read the file content into memory
        file_bytes = await file.read()

        # Open the PDF from the in-memory bytes and extract text
        pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
        extracted_text = ""
        for page in pdf_document:
            extracted_text += page.get_text()
        pdf_document.close()

        # Check if any text was extracted
        if not extracted_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from the PDF. The document might be empty or image-based."
            )

        # Call the Gemini service to get the summary
        summary = await generate_summary(extracted_text)

        # Return the summary in the final JSON response
        return {"summary": summary}

    except HTTPException as e:
        # Re-raise HTTP exceptions to let FastAPI handle them
        raise e
    except Exception as e:
        # Handle potential errors during PDF processing or summarization
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


