# main.py

import fitz  # PyMuPDF
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # Import CORS Middleware
from typing import Annotated

# Import the summary generation function from our new module
from gemini_service import generate_summary

# Create an instance of the FastAPI class
app = FastAPI(
    title="AI Research Assistant API",
    description="API for the AI Research Assistant application.",
    version="0.1.0",
)

# --- CORS (Cross-Origin Resource Sharing) Middleware ---
# This allows your frontend (running on a different URL, e.g., localhost:3000)
# to communicate with your backend (e.g., localhost:8000).

# Define the list of origins that are allowed to make requests.
# For development, this is typically your frontend's local server.
origins = [
    "http://localhost:3000",
    # You could also add your deployed frontend's URL here later
    # "https://your-frontend-domain.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # The list of origins that are allowed to make requests
    allow_credentials=True, # Allows cookies to be included in requests
    allow_methods=["*"],    # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],    # Allows all headers
)
# ---------------------------------------------------------


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
        # The existing general exception handler already returns a 500 error
        # with a consistent JSON format, fulfilling the task requirement.
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

