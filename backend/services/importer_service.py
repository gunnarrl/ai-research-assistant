# backend/services/importer_service.py

import httpx
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks

from backend.database.models import Document
from backend.main import process_pdf_background

async def import_paper_from_url(
    pdf_url: str,
    title: str,
    owner_id: int,
    db: Session,
    background_tasks: BackgroundTasks
) -> Document:
    """
    Downloads a PDF from a URL, creates a document record, and starts the background processing task.

    Args:
        pdf_url: The URL of the PDF to download.
        title: The title to use for the document's filename.
        owner_id: The ID of the user who will own this document.
        db: The SQLAlchemy database session.
        background_tasks: The FastAPI BackgroundTasks instance to add the processing job to.

    Returns:
        The newly created Document object.
    """
    print(f"Importer service: Downloading from {pdf_url}")
    async with httpx.AsyncClient() as client:
        response = await client.get(pdf_url, follow_redirects=True, timeout=30.0)
        response.raise_for_status()
        file_bytes = response.content

    new_document = Document(
        filename=title,
        owner_id=owner_id,
        status="PROCESSING",
        file_content=file_bytes
    )
    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    # Note: We pass the db session from the background task context, not the API context
    background_tasks.add_task(
        process_pdf_background,
        file_bytes,
        title,
        new_document.id,
        db
    )
    
    print(f"Importer service: Created document ID {new_document.id} and started background processing.")
    return new_document