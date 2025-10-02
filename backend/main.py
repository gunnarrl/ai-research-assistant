# main.py

import os
import httpx
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Annotated, List
from pydantic import BaseModel
from datetime import datetime

# Import your models and utility functions
from backend.database.models import Document, TextChunk, User
from backend.utils.pdf_parser import extract_text_from_pdf
from backend.utils.text_processing import chunk_text
from backend.services.embedding_service import generate_embeddings, model as embedding_model
from backend.services.search_service import find_relevant_chunks
from backend.services.gemini_service import get_answer_from_gemini
from .database.database import SessionLocal, engine
from backend.auth import hash_password, verify_password, create_access_token, verify_token

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
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str
    
class DocumentResponse(BaseModel):
    id: int
    filename: str
    upload_date: datetime
    status: str

    class Config:
        orm_mode = True

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


app = FastAPI(
    title="AI Research Assistant API",
    description="API for the AI Research Assistant application.",
    version="0.1.0",
)

# CORS configuration
origins = ["http://localhost:3000", "http://localhost:5173", "https://ai-research-assistant-eight.vercel.app"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def process_pdf_background(file_bytes: bytes, filename: str, document_id: int, db: Session):
    """
    This function contains the logic to process the PDF in the background.
    """
    try:
        # Fetch the document to update its status
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            print(f"Document with ID {document_id} not found for background processing.")
            return

        # 1. Extract text, chunk, and generate embeddings
        extracted_text = extract_text_from_pdf(file_bytes)
        if not extracted_text.strip():
            print(f"Could not extract text from PDF {filename}.")
            doc.status = "FAILED"
            db.commit()
            return

        text_chunks = chunk_text(extracted_text, model=embedding_model)
        embeddings = generate_embeddings(text_chunks)
        
        # 2. Save chunks and their embeddings
        for i, chunk in enumerate(text_chunks):
            new_chunk = TextChunk(
                document_id=document_id,
                chunk_text=chunk,
                embedding=embeddings[i]
            )
            db.add(new_chunk)
        
        # 3. Update document status to COMPLETED
        doc.status = "COMPLETED"
        db.commit()
        print(f"Successfully processed and saved chunks for document_id: {document_id}")

    except Exception as e:
        print(f"An error occurred during background PDF processing for doc ID {document_id}: {e}")
        db.rollback()
        # Update status to FAILED on error
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
    REDIRECT_URI = "http://localhost:5173"

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

# --- Document and Chat Endpoints ---

@app.get("/documents", response_model=List[DocumentResponse])
async def read_user_documents(
    current_user: Annotated[User, Depends(get_current_user)], 
    db: Session = Depends(get_db)
):
    """
    Retrieves a list of all documents uploaded by the current user.
    """
    return db.query(Document).filter(Document.owner_id == current_user.id).all()

@app.post("/upload")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    file: Annotated[UploadFile, File(description="A PDF file to process.")],
    db: Session = Depends(get_db)
):
    # a. Validate file type
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF.")

    try:
        file_bytes = await file.read()
        
        # 1. Save document metadata with "PROCESSING" status
        new_document = Document(
            filename=file.filename, 
            owner_id=current_user.id, 
            status="PROCESSING" # Set initial status
        )
        db.add(new_document)
        db.commit()
        db.refresh(new_document)

        # 2. Add the processing task to the background
        db_for_task = SessionLocal()
        background_tasks.add_task(
            process_pdf_background, 
            file_bytes, 
            file.filename, 
            new_document.id, 
            db_for_task
        )

        # 3. Return a success message immediately
        return {"message": "File upload started. Processing in the background.", "document_id": new_document.id}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during file upload: {e}")

@app.post("/chat")
async def chat_with_document(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Accepts a user question for a specific document and returns a context-aware AI answer as a stream.
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
    