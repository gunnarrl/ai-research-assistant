# backend/services/processing_service.py

import asyncio
from sqlalchemy.orm import Session
from backend.database.database import SessionLocal
from backend.database.models import Document, TextChunk, Citation
from backend.utils.pdf_parser import extract_text_from_pdf
from backend.utils.text_processing import chunk_text
from backend.services.embedding_service import generate_embeddings, model as embedding_model
from backend.services.gemini_service import extract_structured_data_sync, parse_references_from_text_sync, parse_references_from_text
from backend.services.citation_service import extract_citations_from_text


def process_pdf_background(file_bytes: bytes, filename: str, document_id: int, db: Session):
    """
    This function contains the logic to process the PDF in the background.
    """
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            print(f"Document with ID {document_id} not found for background processing.")
            return

        extracted_text = extract_text_from_pdf(file_bytes)
        if not extracted_text.strip():
            doc.status = "FAILED"
            db.commit()
            return

        print(f"Extracting structured data for document_id: {document_id}")
        structured_data = extract_structured_data_sync(extracted_text)
        doc.structured_data = structured_data
        
        print(f"Extracting citations for document_id: {document_id}")
        # FIX: Call the synchronous version of the function
        citations = parse_references_from_text_sync(extracted_text) 
        if citations and "error" not in citations[0]:
            for citation_data in citations:
                new_citation = Citation(document_id=document_id, data=citation_data)
                db.add(new_citation)

        print(f"Chunking and embedding document_id: {document_id}")
        text_chunks = chunk_text(extracted_text, model=embedding_model)
        embeddings = generate_embeddings(text_chunks)
        
        for i, chunk in enumerate(text_chunks):
            new_chunk = TextChunk(document_id=document_id, chunk_text=chunk, embedding=embeddings[i])
            db.add(new_chunk)
        
        doc.status = "COMPLETED"
        doc.is_interactive = True

        db.commit()
        print(f"Successfully processed and saved document_id: {document_id}")

    except Exception as e:
        print(f"An error occurred during background PDF processing for doc ID {document_id}: {e}")
        db.rollback()
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.is_interactive = False
            doc.status = "FAILED"
            db.commit()
    finally:
        db.close()


async def process_pdf_and_extract_data(file_bytes: bytes) -> dict:
    """
    Processes PDF bytes to extract all necessary data, but does not interact with the database.
    
    Returns:
        A dictionary containing all extracted data.
    """
    try:
        # Run blocking CPU-bound functions in a separate thread
        extracted_text = await asyncio.to_thread(extract_text_from_pdf, file_bytes)
        
        if not extracted_text.strip():
            return {"error": "Extracted text is empty."}

        structured_data_task = asyncio.to_thread(extract_structured_data_sync, extracted_text)
        citations_task = parse_references_from_text(extracted_text)
        
        # Run text chunking and embedding in threads
        text_chunks = await asyncio.to_thread(chunk_text, extracted_text, model=embedding_model)
        embeddings = await asyncio.to_thread(generate_embeddings, text_chunks)
        
        structured_data, citations = await asyncio.gather(
            structured_data_task,
            citations_task
        )
        
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

def process_pdf_for_lit_review(file_bytes: bytes, document_id: int):
    """
    A lightweight processing function for the literature review agent.
    It creates its own database session to be thread-safe.
    """
    # FIX: Create a new, independent session for this thread.
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            print(f"[Lit Review] Document {document_id} not found.")
            return

        doc.is_interactive = False
        db.commit()

        extracted_text = extract_text_from_pdf(file_bytes)
        if not extracted_text.strip():
            doc.status = "FAILED"
            db.commit()
            return

        # 1. Get structured data
        doc.structured_data = extract_structured_data_sync(extracted_text)
        
        # 2. Get citations
        citations = parse_references_from_text_sync(extracted_text)
        if citations and "error" not in citations[0]:
            for citation_data in citations:
                new_citation = Citation(document_id=document_id, data=citation_data)
                db.add(new_citation)
        
        # 3. Mark as completed
        doc.status = "COMPLETED"
        db.commit()
        print(f"[Lit Review] Successfully processed document_id: {document_id}")

    except Exception as e:
        print(f"[Lit Review] An error occurred for doc ID {document_id}: {e}")
        db.rollback()
        # You might need to refetch the 'doc' here if the session was rolled back
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.status = "FAILED"
            db.commit()
    finally:
        db.close()