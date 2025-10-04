# backend/services/importer_service.py

import httpx
from sqlalchemy.orm import Session
from backend.database.models import Document

async def download_and_create_document(
    pdf_url: str,
    title: str,
    owner_id: int,
    db: Session
) -> (Document, bytes):
    """
    Downloads a PDF from a URL and creates the initial Document record.
    It does NOT start the background processing.

    Returns:
        A tuple containing the newly created Document object and the file's content in bytes.
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
    
    print(f"Importer service: Created document record with ID {new_document.id}.")
    return new_document, file_bytes