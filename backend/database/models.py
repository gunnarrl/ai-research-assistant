from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, LargeBinary
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from backend.database.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # Establish a one-to-many relationship with Document
    documents = relationship("Document", back_populates="owner")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    # Add the file_content column below
    file_content = Column(LargeBinary, nullable=True) # Use nullable=True for the migration
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, nullable=False, default="PENDING")
    structured_data = Column(JSON, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))


    # Establish a many-to-one relationship with User
    owner = relationship("User", back_populates="documents")
    
    # Establish a one-to-many relationship with TextChunk
    chunks = relationship("TextChunk", back_populates="document", cascade="all, delete-orphan")

class TextChunk(Base):
    __tablename__ = "text_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    
    # Define the vector column with 384 dimensions.
    embedding = Column(Vector(384))
    
    # Establish a many-to-one relationship with Document
    document = relationship("Document", back_populates="chunks")