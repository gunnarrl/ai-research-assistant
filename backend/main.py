# main.py

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Annotated
from pydantic import BaseModel

# Import your models and utility functions
# Adjust paths if you've changed the directory structure
from backend.database.models import Document, TextChunk
from backend.utils.pdf_parser import extract_text_from_pdf
from backend.utils.text_processing import chunk_text
from backend.services.embedding_service import generate_embeddings, model as embedding_model
from backend.services.search_service import find_relevant_chunks
from backend.services.gemini_service import get_answer_from_gemini
from .database.database import SessionLocal # Add this if not already present

class ChatRequest(BaseModel):
    document_id: int
    question: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI(
    title="AI Research Assistant API",
    description="API for the AI Research Assistant application.",
    version="0.1.0",
)

origins = ["http://localhost:3000", "http://localhost:5173", "https://ai-research-assistant-eight.vercel.app"]

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

@app.post("/upload")
async def upload_pdf(
    file: Annotated[UploadFile, File(description="A PDF file to process.")],
    db: Session = Depends(get_db)
):
    # a. Validate file type
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF.")

    try:
        file_bytes = await file.read()
        
        # 1. Extract text from the PDF
        extracted_text = extract_text_from_pdf(file_bytes)
        if not extracted_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from PDF. It may be empty or image-based."
            )

        # 2. Save document metadata to the database
        new_document = Document(filename=file.filename)
        db.add(new_document)
        db.commit()
        db.refresh(new_document)

        # 3. Chunk the extracted text, passing the model
        text_chunks = chunk_text(extracted_text, model=embedding_model)

        # 4. Generate embeddings for all text chunks
        embeddings = generate_embeddings(text_chunks)
        
        # 5. Save chunks and their embeddings to the database
        for i, chunk in enumerate(text_chunks):
            new_chunk = TextChunk(
                document_id=new_document.id,
                chunk_text=chunk,
                embedding=embeddings[i]
            )
            db.add(new_chunk)
            
        db.commit()

        # Return a success message with the new document ID
        return {"message": "File uploaded and processed successfully.", "document_id": new_document.id}

    except HTTPException as e:
        db.rollback() # Rollback the transaction on known errors
        raise e
    except Exception as e:
        db.rollback() # Rollback on any unexpected errors
        # Catch any other unexpected errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@app.post("/chat")
async def chat_with_document(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Accepts a user question for a specific document and returns a context-aware AI answer.
    """
    try:
        # a. Call find_relevant_chunks() to get the necessary context
        relevant_chunks = find_relevant_chunks(
            document_id=request.document_id,
            question=request.question,
            db=db
        )

        if not relevant_chunks:
            # Handle case where no relevant chunks are found
            raise HTTPException(
                status_code=404,
                detail="Could not find relevant information in the document to answer the question."
            )

        # Combine the chunks into a single context string
        context_str = "\n---\n".join(relevant_chunks)

        # b. & c. Construct prompt and call Gemini API
        answer = await get_answer_from_gemini(context=context_str, question=request.question)

        # d. Return the LLM's answer
        return {"answer": answer}

    except HTTPException as e:
        # Re-raise known HTTP exceptions
        raise e
    except Exception as e:
        # Catch any other unexpected errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during chat processing: {e}")
