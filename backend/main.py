# main.py

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status
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
from .database.database import SessionLocal 
from backend.auth import hash_password, verify_password, create_access_token, verify_token

# Pydantic Models for API requests and responses
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


@app.get("/health")
def read_health_check():
    return {"status": "ok"}

# --- User Authentication Endpoints ---

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
    current_user: Annotated[User, Depends(get_current_user)],
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

        # 2. Save document metadata to the database, now with owner_id
        new_document = Document(filename=file.filename, owner_id=current_user.id)
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
    