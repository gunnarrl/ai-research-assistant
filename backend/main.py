# main.py

import fitz  # PyMuPDF
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


# 3. Define the PDF upload and text extraction endpoint
@app.post("/summarize")
async def summarize_pdf(file: Annotated[UploadFile, File(description="A PDF file to summarize.")]):
    """
    Accepts a PDF file, validates it, extracts the full text content,
    and returns the extracted text.
    """
    # Validate the file's content type to ensure it's a PDF
    if file.content_type != "application/pdf":
        # If not a PDF, raise an HTTP 400 Bad Request error
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload a PDF document."
        )

    try:
        # Read the file content into memory
        file_bytes = await file.read()

        # Open the PDF from the in-memory bytes
        pdf_document = fitz.open(stream=file_bytes, filetype="pdf")

        # Initialize an empty string to hold all the text
        extracted_text = ""

        # Iterate through each page of the PDF
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            extracted_text += page.get_text()

        # Close the document
        pdf_document.close()

        # Return the extracted text in a JSON response
        return {"text": extracted_text}

    except Exception as e:
        # Handle potential errors during PDF processing
        raise HTTPException(status_code=500, detail=f"An error occurred while processing the PDF: {e}")

