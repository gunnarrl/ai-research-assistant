# backend/services/processing_service.py

import asyncio
from sqlalchemy.orm import Session
from backend.database.models import Document, TextChunk, Citation
from backend.utils.pdf_parser import extract_text_from_pdf
from backend.utils.text_processing import chunk_text
from backend.services.embedding_service import generate_embeddings, model as embedding_model
from backend.services.gemini_service import extract_structured_data_sync, parse_references_from_text

async def process_pdf_and_extract_data(file_bytes: bytes) -> dict:
    """
    Processes PDF bytes to extract all necessary data, but does not interact with the database.
    
    Returns:
        A dictionary containing all extracted data.
    """
    try:
        extracted_text = extract_text_from_pdf(file_bytes)
        if not extracted_text.strip():
            return {"error": "Extracted text is empty."}

        # Run async/sync Gemini calls correctly
        structured_data = await asyncio.to_thread(extract_structured_data_sync, extracted_text)
        citations = await parse_references_from_text(extracted_text)
        
        # CPU-bound tasks
        text_chunks = chunk_text(extracted_text, model=embedding_model)
        embeddings = generate_embeddings(text_chunks)
        
        return {
            "structured_data": structured_data,
            "citations": citations,
            "text_chunks": text_chunks,
            "embeddings": embeddings,
            "error": None
        }
    except Exception as e:
        print(f"An error occurred during data extraction: {e}")
        return {"error": str(e)}