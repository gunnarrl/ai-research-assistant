# main.py

import os
import httpx
import asyncio
from contextlib import asynccontextmanager
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status, BackgroundTasks, Response
from fastapi.responses import StreamingResponse, JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Annotated, List, Optional, Dict
from pydantic import BaseModel
from sqlalchemy import or_
import arxiv
from datetime import datetime

# Import your models and utility functions

from backend.database.models import Document, TextChunk, User, Citation, Project, LiteratureReview
from backend.utils.pdf_parser import extract_text_from_pdf
from backend.services.processing_service import process_pdf_background
from backend.services.citation_service import extract_citations_from_text, extract_citations_from_text_sync
from backend.utils.text_processing import chunk_text
from backend.services.importer_service import download_and_create_document
from backend.services.arxiv_service import perform_arxiv_search
from backend.services.embedding_service import generate_embeddings, model as embedding_model
from backend.services.search_service import find_relevant_chunks, find_relevant_chunks_multi
from backend.services.gemini_service import get_answer_from_gemini, extract_structured_data_sync, generate_bibtex_from_text_sync
from backend.services.importer_service import download_and_create_document
from .database.database import SessionLocal, engine
from backend.auth import hash_password, verify_password, create_access_token, verify_token
from backend.agent import _agent_workflow


# Pydantic Models for API requests and responses
class GoogleLoginRequest(BaseModel):
    code: str

class ChatRequest(BaseModel):
    document_id: int
    question: str

class UserCreate(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class ArxivArticle(BaseModel):
    title: str
    authors: List[str]
    summary: str
    pdf_url: str

class ImportFromUrlRequest(BaseModel):
    pdf_url: str
    title: str

class MultiChatRequest(BaseModel):
    document_ids: List[int]
    question: str

class DocumentResponse(BaseModel):
    id: int
    filename: str
    upload_date: datetime
    status: str
    structured_data: Optional[Dict] = None

    class Config:
        from_attributes = True

class CitationResponse(BaseModel):
    id: int
    document_id: int
    data: Dict

    class Config:
        from_attributes = True

class LitReviewRequest(BaseModel):
    topic: str

class LitReviewResponse(BaseModel):
    id: int
    topic: str
    status: str
    result: Optional[str] = None

    class Config:
        from_attributes = True


# --- Pydantic Models for Projects ---

class ProjectCreate(BaseModel):
    name: str

class ProjectMemberAdd(BaseModel):
    email: str

class ProjectDocumentAdd(BaseModel):
    document_id: int

class ProjectResponse(BaseModel):
    id: int
    name: str
    members: List[UserResponse]
    documents: List[DocumentResponse]

    class Config:
        from_attributes = True

# OAuth2 Scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency to get the current user
def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    email = verify_token(token, credentials_exception)
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

def get_document_if_user_has_access(
    document_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
) -> Document:
    """
    Dependency to get a document and verify user access.
    A user has access if they are the owner or a member of a project containing the document.
    """
    # Query for the document
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Check for ownership
    if document.owner_id == current_user.id:
        return document

    # Check for project membership
    for project in document.projects:
        if current_user in project.members:
            return document

    # If neither condition is met, deny access
    raise HTTPException(status_code=403, detail="You do not have permission to access this document.")

# --- NEW LIFESPAN EVENT HANDLER ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # This code runs on startup
    print("Application startup: Cleaning up stale literature reviews...")
    db = SessionLocal()
    try:
        # Find any reviews that were in a processing state when the server shut down
        stale_reviews = db.query(LiteratureReview).filter(
            LiteratureReview.status.notin_(['COMPLETED', 'FAILED', 'PENDING'])
        ).all()

        if stale_reviews:
            for review in stale_reviews:
                print(f"Found stale literature review (ID: {review.id}). Marking as FAILED.")
                review.status = "FAILED"
                review.result = "The server was restarted during the review process."
            db.commit()
    finally:
        db.close()
    
    yield
    # This code runs on shutdown (not needed for this fix, but good practice to have)
    print("Application shutdown.")
# --------------------------------


app = FastAPI(
    title="AI Research Assistant API",
    description="API for the AI Research Assistant application.",
    version="0.1.0",
    lifespan=lifespan
)

# CORS configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(',')

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        
        # --- ADD CITATION EXTRACTION LOGIC ---
        print(f"Extracting citations for document_id: {document_id}")
        # Use the new synchronous function instead of the async one
        citations = extract_citations_from_text_sync(extracted_text)
        if citations and "error" not in citations[0]:
            for citation_data in citations:
                new_citation = Citation(document_id=document_id, data=citation_data)
                db.add(new_citation)
        # ------------------------------------

        print(f"Chunking and embedding document_id: {document_id}")
        text_chunks = chunk_text(extracted_text, model=embedding_model)
        embeddings = generate_embeddings(text_chunks)
        
        for i, chunk in enumerate(text_chunks):
            new_chunk = TextChunk(document_id=document_id, chunk_text=chunk, embedding=embeddings[i])
            db.add(new_chunk)
        
        doc.status = "COMPLETED"
        db.commit()
        print(f"Successfully processed and saved document_id: {document_id}")

    except Exception as e:
        print(f"An error occurred during background PDF processing for doc ID {document_id}: {e}")
        db.rollback()
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.status = "FAILED"
            db.commit()
    finally:
        db.close()

@app.get("/health")
def read_health_check():
    return {"status": "ok"}

# --- User Authentication Endpoints ---

@app.post("/auth/google", response_model=Token)
async def auth_google(request: GoogleLoginRequest, db: Session = Depends(get_db)):
    """
    Handles the Google OAuth 2.0 authorization code flow.
    """
    # This is the URL your frontend is running on
    # For the code exchange to work, this MUST match the "Authorized redirect URIs"
    # you configured in your Google Cloud project.
    REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

    try:
        # Step 1: Exchange the authorization code for an ID token
        async with httpx.AsyncClient() as client:
            response = await client.post("https://oauth2.googleapis.com/token", data={
                "code": request.code,
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "redirect_uri": REDIRECT_URI,
                "grant_type": "authorization_code",
            })
            response.raise_for_status()
            token_data = response.json()
            google_id_token = token_data.get("id_token")

            if not google_id_token:
                raise HTTPException(status_code=400, detail="Could not retrieve ID token from Google.")

        # Step 2: Verify the ID token and get user info
        try:
            id_info = id_token.verify_oauth2_token(
                google_id_token, google_requests.Request(), os.getenv("GOOGLE_CLIENT_ID")
            )
            user_email = id_info.get("email")
            if not user_email:
                raise HTTPException(status_code=400, detail="Email not found in Google token.")

        except ValueError as e:
            raise HTTPException(status_code=401, detail=f"Invalid Google token: {e}")

        # Step 3: Log in or register the user in your database
        user = db.query(User).filter(User.email == user_email).first()

        if not user:
            # User doesn't exist, create a new one.
            # We add a placeholder for the password hash since it's required by the model,
            # but this user will never log in with a password.
            new_user = User(
                email=user_email,
                hashed_password=hash_password("PLACEHOLDER_PASSWORD_FOR_OAUTH") # Or generate a random string
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            user = new_user

        # Step 4: Create a JWT for the user and return it
        access_token = create_access_token(data={"sub": user.email})
        return {"access_token": access_token, "token_type": "bearer"}

    except httpx.HTTPStatusError as e:
        # Handle errors from the request to Google
        print(f"Error exchanging code with Google: {e.response.text}")
        raise HTTPException(status_code=400, detail="Error communicating with Google.")
    except Exception as e:
        print(f"An unexpected error occurred during Google auth: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred.")


@app.post("/users/register", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Registers a new user.
    """
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pass = hash_password(user.password)
    new_user = User(email=user.email, hashed_password=hashed_pass)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    """
    Logs in a user and returns an access token.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    """
    Gets the details of the currently authenticated user.
    """
    return current_user

@app.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """
    Creates a new project for the current user. The creator is automatically added as the first member.
    """
    new_project = Project(name=project.name)
    new_project.members.append(current_user)  # Add the creator as a member
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project

@app.get("/projects", response_model=List[ProjectResponse])
async def read_user_projects(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Retrieves a list of all projects the current user is a member of.
    """
    return current_user.projects

@app.post("/projects/{project_id}/members", response_model=ProjectResponse)
async def add_project_member(
    project_id: int,
    member: ProjectMemberAdd,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """
    Adds another user to a project by their email. Only members of the project can add new members.
    """
    # Query the project and ensure the current user is a member
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project or current_user not in project.members:
        raise HTTPException(status_code=404, detail="Project not found or you do not have permission to modify it.")

    # Find the user to add
    user_to_add = db.query(User).filter(User.email == member.email).first()
    if not user_to_add:
        raise HTTPException(status_code=404, detail="User with the specified email not found.")

    # Add the user if they are not already a member
    if user_to_add not in project.members:
        project.members.append(user_to_add)
        db.commit()
        db.refresh(project)

    return project

@app.post("/projects/{project_id}/documents", response_model=ProjectResponse)
async def add_document_to_project(
    project_id: int,
    doc_to_add: ProjectDocumentAdd,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """
    Adds an existing document (owned by the current user) to a project.
    """
    # Verify the current user is a member of the project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project or current_user not in project.members:
        raise HTTPException(status_code=404, detail="Project not found or you do not have permission to modify it.")

    # Verify the current user owns the document they are trying to add
    document = db.query(Document).filter(
        Document.id == doc_to_add.document_id,
        Document.owner_id == current_user.id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found or you do not own it.")

    # Add the document to the project if it's not already there
    if document not in project.documents:
        project.documents.append(document)
        db.commit()
        db.refresh(project)

    return project

@app.get("/projects/{project_id}", response_model=ProjectResponse)
async def read_project_details(
    project_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """
    Retrieves the full details of a single project, including members and documents.
    Ensures the current user is a member of the project.
    """
    project = db.query(Project).filter(Project.id == project_id).first()

    # Verify project exists and user is a member
    if not project or current_user not in project.members:
        raise HTTPException(status_code=404, detail="Project not found or you do not have permission to view it.")

    return project

# --- Document and Chat Endpoints ---

@app.get("/documents", response_model=List[DocumentResponse])
async def read_user_documents(
    current_user: Annotated[User, Depends(get_current_user)], 
    db: Session = Depends(get_db)
):
    """
    Retrieves a list of all documents the current user owns OR has access to via project membership.
    This is a corrected version to handle DISTINCT on complex column types like JSON.
    """
    # Get IDs of projects the user is a member of
    project_ids = [p.id for p in current_user.projects]

    # Step 1: Create a subquery to select the unique IDs of all accessible documents.
    # It's efficient to apply DISTINCT only on the ID column.
    subquery = db.query(Document.id).filter(
        or_(
            Document.owner_id == current_user.id,
            Document.projects.any(Project.id.in_(project_ids))
        )
    ).distinct().subquery()



    # Step 2: Query the full Document objects based on the unique IDs found in the subquery.
    documents = db.query(Document).filter(
        Document.id.in_(subquery),
        Document.is_interactive == True
    ).all()
    
    return documents

@app.post("/upload")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    file: Annotated[UploadFile, File(description="A PDF file to process.")],
    db: Session = Depends(get_db)
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF.")

    try:
        file_bytes = await file.read()
        
        # Now, include the file_bytes in the new document record
        new_document = Document(
            filename=file.filename, 
            owner_id=current_user.id, 
            status="PROCESSING",
            file_content=file_bytes # Save the file content
        )
        db.add(new_document)
        db.commit()
        db.refresh(new_document)

        db_for_task = SessionLocal()
        background_tasks.add_task(
            process_pdf_background, 
            file_bytes, 
            file.filename, 
            new_document.id, 
            db_for_task
        )

        return {"message": "File upload started. Processing in the background.", "document_id": new_document.id}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during file upload: {e}")

@app.get("/documents/{document_id}/file")
async def get_document_file(
    document: Annotated[Document, Depends(get_document_if_user_has_access)]
):
    """
    Retrieves the raw PDF file for a given document, checking for user access.
    """
    if not document.file_content:
        raise HTTPException(status_code=404, detail="File content is missing for this document.")

    return Response(content=document.file_content, media_type="application/pdf")

@app.post("/chat")
async def chat_with_document(
    request: ChatRequest, 
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """
    Accepts a user question for a specific document and returns a context-aware AI answer as a stream.
    Access is verified before processing.
    """

    document = get_document_if_user_has_access(
        document_id=request.document_id,
        current_user=current_user,
        db=db
    )
    # The 'document' variable from the dependency is already the validated document object.
    # We can now proceed with the original logic.
    try:
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

        # b. Define the async generator for the streaming response
        async def stream_generator():
            try:
                # c. Call the modified Gemini service and yield each chunk
                async for chunk in get_answer_from_gemini(context=context_str, question=request.question):
                    yield chunk
            except Exception as e:
                # This will catch errors during the streaming process
                print(f"An error occurred during streaming: {e}")
                yield "Error: Could not generate a streaming answer."

        # d. Return the StreamingResponse
        return StreamingResponse(stream_generator(), media_type="text/plain")

    except HTTPException as e:
        # Re-raise known HTTP exceptions
        raise e
    except Exception as e:
        # Catch any other unexpected errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during chat processing: {e}")

@app.get("/arxiv/search", response_model=List[ArxivArticle])
def search_arxiv(query: str, max_results: int = 5):
    """
    Searches the arXiv API for papers matching the query using the shared service.
    """
    results = perform_arxiv_search(query, max_results)
    if not results:
        raise HTTPException(status_code=500, detail="An error occurred while searching arXiv.")
    return results
    
@app.post("/import-from-url")
async def import_from_url(
    request: ImportFromUrlRequest,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """
    Downloads a PDF and starts the processing task in the background.
    """
    try:
        new_document, file_bytes = await download_and_create_document(
            pdf_url=request.pdf_url,
            title=request.title,
            owner_id=current_user.id,
            db=db
        )
        # The endpoint is responsible for adding the task now
        db_for_task = SessionLocal()
        background_tasks.add_task(
            process_pdf_background, 
            file_bytes, 
            new_document.filename, 
            new_document.id, 
            db_for_task
        )
        return {"message": "File import started. Processing in the background.", "document_id": new_document.id}

    except httpx.HTTPStatusError as e:
        error_detail = f"Could not download file. The server responded with status {e.response.status_code}."
        raise HTTPException(status_code=400, detail=error_detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


@app.post("/chat/multi")
async def chat_with_multiple_documents(request: MultiChatRequest, db: Session = Depends(get_db)):
    """
    Accepts a user question for multiple documents and returns a context-aware AI answer as a stream.
    """
    try:
        # This will be fully implemented in Task 11
        relevant_chunks = find_relevant_chunks_multi(
            document_ids=request.document_ids,
            question=request.question,
            db=db
        )

        if not relevant_chunks:
            raise HTTPException(
                status_code=404,
                detail="Could not find relevant information in the selected documents to answer the question."
            )

        context_str = "\n---\n".join(relevant_chunks)

        async def stream_generator():
            try:
                async for chunk in get_answer_from_gemini(context=context_str, question=request.question, is_multi_doc=True):
                    yield chunk
            except Exception as e:
                print(f"An error occurred during streaming: {e}")
                yield "Error: Could not generate a streaming answer."

        return StreamingResponse(stream_generator(), media_type="text/plain")

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during multi-chat processing: {e}")
    
@app.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """
    Deletes a document and all its associated data for the current user.
    """
    # Find the document ensuring it belongs to the current user
    doc_to_delete = db.query(Document).filter(
        Document.id == document_id,
        Document.owner_id == current_user.id
    ).first()

    if not doc_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or you do not have permission to delete it."
        )

    try:
        db.delete(doc_to_delete)
        db.commit()
        # Return a 204 No Content response, which is standard for successful DELETE operations
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred while deleting the document: {e}")
    
@app.get("/documents/{document_id}/citations", response_model=List[CitationResponse])
async def get_document_citations(
    document: Annotated[Document, Depends(get_document_if_user_has_access)],
    db: Session = Depends(get_db)
):
    """
    Retrieves a list of all citations extracted from a specific document, checking for user access.
    """
    # The dependency already verified access, so we can just query the citations.
    citations = db.query(Citation).filter(Citation.document_id == document.id).all()
    return citations

def format_citations_to_bibtex(citations: List[Citation]) -> str:
    """
    Converts a list of Citation objects into a single BibTeX formatted string.
    """
    bibtex_string = ""
    for i, citation in enumerate(citations):
        data = citation.data
        
        # --- ROBUST AUTHOR HANDLING ---
        authors_list = data.get("authors", [])
        if authors_list:
            # If the list is not empty, get the first author's last name
            first_author = authors_list[0]
            # Handle cases where an author might just be a single name
            author_last_name = first_author.split(" ")[-1].lower()
        else:
            # If the authors list is empty, use a default
            author_last_name = "unknown"
        # ---------------------------

        # Create a unique key for the BibTeX entry
        key = f"{author_last_name}{data.get('year', '')}_{i}"

        bibtex_entry = f"@article{{{key},\n"
        
        authors = " and ".join(authors_list) # Use the authors_list we already fetched
        if authors:
            bibtex_entry += f"  author = \"{{{authors}}}\",\n"
        
        title = data.get("title", "No Title")
        if title:
            bibtex_entry += f"  title = \"{{{title}}}\",\n"
            
        year = data.get("year", "")
        if year:
            bibtex_entry += f"  year = \"{year}\",\n"
            
        bibtex_entry += "}\n\n"
        bibtex_string += bibtex_entry
        
    return bibtex_string

@app.get("/documents/{document_id}/citations/export")
async def export_document_citations(
    format: str,
    document: Annotated[Document, Depends(get_document_if_user_has_access)],
    db: Session = Depends(get_db)
):
    """
    Exports citations for a document in a specified format, checking for user access.
    """
    if format.lower() != 'bibtex':
        raise HTTPException(status_code=400, detail="Invalid format. Only 'bibtex' is supported.")

    citations = db.query(Citation).filter(Citation.document_id == document.id).all()
    
    if not citations:
        return PlainTextResponse("", media_type="application/x-bibtex")

    bibtex_content = format_citations_to_bibtex(citations)
    
    return PlainTextResponse(bibtex_content, media_type="application/x-bibtex", headers={
        "Content-Disposition": f"attachment; filename={document.filename}_citations.bib"
    })

@app.get("/documents/{document_id}/generate-bibtex")
async def generate_bibtex_for_document(
    document: Annotated[Document, Depends(get_document_if_user_has_access)],
    db: Session = Depends(get_db)
):
    """
    Generates a BibTeX citation for a single uploaded document on-demand.
    """
    if not document.file_content:
        raise HTTPException(status_code=404, detail="File content not found for this document.")

    try:
        # Extract text and generate BibTeX
        text = extract_text_from_pdf(document.file_content)
        bibtex_content = generate_bibtex_from_text_sync(text)
        
        # Sanitize filename for the download
        sanitized_filename = "".join(c if c.isalnum() else "_" for c in document.filename.replace('.pdf', ''))

        return PlainTextResponse(bibtex_content, media_type="application/x-bibtex", headers={
            "Content-Disposition": f"attachment; filename={sanitized_filename}.bib"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate BibTeX: {e}")


# --- Agent Endpoints ---

@app.post("/agent/literature-review", response_model=LitReviewResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_literature_review(
    request: LitReviewRequest,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """
    Kicks off the literature review agent as a background task.
    """
    new_review = LiteratureReview(
        topic=request.topic,
        owner_id=current_user.id,
        status="PENDING"
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)

    # Add the long-running agent task to the background
    background_tasks.add_task(_agent_workflow, new_review.id, new_review.topic)

    return new_review

@app.get("/agent/literature-reviews", response_model=List[LitReviewResponse])
async def get_literature_reviews(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """
    Retrieves a list of all literature reviews for the current user.
    """
    reviews = db.query(LiteratureReview).filter(
        LiteratureReview.owner_id == current_user.id
    ).order_by(desc(LiteratureReview.id)).limit(5).all()
    return reviews

@app.get("/agent/literature-review/active", response_model=Optional[LitReviewResponse])
async def get_active_literature_review(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """
    Finds the most recent, non-completed literature review for the current user.
    """
    # Find the latest review that isn't COMPLETED or FAILED for this user
    active_review = db.query(LiteratureReview).filter(
        LiteratureReview.owner_id == current_user.id,
        LiteratureReview.status.notin_(['COMPLETED', 'FAILED'])
    ).order_by(desc(LiteratureReview.id)).first()
    
    return active_review

@app.get("/agent/literature-review/{review_id}", response_model=LitReviewResponse)
async def get_literature_review_status(
    review_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """
    Retrieves the status and result of a specific literature review task.
    """
    review = db.query(LiteratureReview).filter(
        LiteratureReview.id == review_id,
        LiteratureReview.owner_id == current_user.id
    ).first()

    if not review:
        raise HTTPException(status_code=404, detail="Literature review not found.")
    
    return review