from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, LargeBinary, Table, Boolean
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from backend.database.database import Base

project_members = Table(
    'project_members', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('project_id', Integer, ForeignKey('projects.id'), primary_key=True)
)

project_documents = Table(
    'project_documents', Base.metadata,
    Column('document_id', Integer, ForeignKey('documents.id'), primary_key=True),
    Column('project_id', Integer, ForeignKey('projects.id'), primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # Establish a one-to-many relationship with Document
    documents = relationship("Document", back_populates="owner")

    # Establish a many-to-many relationship with Project
    projects = relationship("Project", secondary=project_members, back_populates="members")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    # Relationship to users (members)
    members = relationship("User", secondary=project_members, back_populates="projects")
    
    # Relationship to documents
    documents = relationship("Document", secondary=project_documents, back_populates="projects")

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
    is_interactive = Column(Boolean, default=True, nullable=False)


    # Establish a many-to-one relationship with User
    owner = relationship("User", back_populates="documents")
    
    # Establish a one-to-many relationship with TextChunk
    chunks = relationship("TextChunk", back_populates="document", cascade="all, delete-orphan")

    citations = relationship("Citation", back_populates="document", cascade="all, delete-orphan")

    projects = relationship("Project", secondary=project_documents, back_populates="documents")

class Citation(Base):
    __tablename__ = "citations"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    data = Column(JSON, nullable=False)

    # Establish a many-to-one relationship with Document
    document = relationship("Document", back_populates="citations")

class LiteratureReview(Base):
    __tablename__ = "literature_reviews"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, nullable=False)
    status = Column(String, nullable=False, default="PENDING") # PENDING, SEARCHING, SUMMARIZING, SYNTHESIZING, COMPLETED, FAILED
    result = Column(Text, nullable=True) # To store the final literature review text
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User")
    
class TextChunk(Base):
    __tablename__ = "text_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    
    # Define the vector column with 384 dimensions.
    embedding = Column(Vector(384))
    
    # Establish a many-to-one relationship with Document
    document = relationship("Document", back_populates="chunks")