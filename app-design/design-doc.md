AI Research Assistant: Technical Design Document (V2)
1.0 Introduction
This document outlines the technical design for the AI Research Assistant, a full-stack web application. The goal of this phase is to evolve the application from a simple summarizer into an interactive research tool.

The core of this upgrade is the implementation of a Retrieval-Augmented Generation (RAG) pipeline. This will allow users to upload a PDF document and have an in-depth, context-aware conversation with an AI about its contents. This design emphasizes a scalable, production-ready architecture using a dedicated database and modern AI practices.

2.0 System Architecture
The application will use a decoupled architecture with a React frontend, a FastAPI backend, and a PostgreSQL database. The key innovation is the introduction of a vector database and a dual-flow process: one for document ingestion and one for interactive chat.

2.1 Architectural Diagram & Data Flow
Ingestion Flow (When a user uploads a PDF):
Upload: The user uploads a PDF via the React frontend.

API Request: The frontend sends the PDF to a POST /upload endpoint on the FastAPI backend.

Text Extraction: The backend uses the PyMuPDF library to extract the full text.

Chunking: The extracted text is broken down into smaller, overlapping chunks.

Embedding: Each text chunk is converted into a numerical vector representation using an embedding model.

Storage: The document's metadata is stored in a documents table, and the text chunks and their corresponding embeddings are stored in a text_chunks table within the PostgreSQL database (using the pgvector extension).

Chat Flow (When a user asks a question):
User Question: The user submits a question through the chat interface on the frontend.

API Request: The frontend sends the question and the document_id to a POST /chat endpoint.

Query Embedding: The backend generates an embedding for the user's question.

Vector Search: The backend queries the vector database to find the text chunks whose embeddings are most semantically similar to the question's embedding.

Context-Aware Prompt: The retrieved text chunks are combined with the user's question into a detailed prompt for the Gemini LLM.

LLM Generation: The LLM generates an answer based only on the provided context.

Display: The answer is streamed back to the React frontend and displayed in the chat window.

2.2 Component Breakdown
Frontend: A React.js single-page application hosted on Vercel. It is responsible for the file upload interface and the interactive chat window.

Backend: A Python FastAPI application, containerized with Docker and deployed on Google Cloud Run. It handles all business logic:

PDF processing (extraction, chunking, embedding).

Database interactions (storing and retrieving data/vectors).

Orchestrating the RAG pipeline and communicating with the Google Gemini API.

Database: A PostgreSQL server with the pgvector extension enabled. This single database serves as both the relational store for document metadata and the vector store for efficient similarity searches.

AI Services:

Google Gemini API: Used as the Large Language Model (LLM) for generating answers.

Sentence-Transformers: A library used to run the embedding model that converts text to vectors.

3.0 Data Models (PostgreSQL Schema)
The application will rely on a persistent PostgreSQL database with the following core tables.

documents Table
Stores metadata for each uploaded PDF.

Column

Type

Description

id

INTEGER

Primary Key, auto-incrementing.

filename

VARCHAR

The original name of the uploaded file.

upload_date

TIMESTAMP

The timestamp when the document was uploaded.

text_chunks Table
Stores the processed text and vector data for each document.

Column

Type

Description

id

INTEGER

Primary Key, auto-incrementing.

document_id

INTEGER

Foreign Key linking to documents.id.

chunk_text

TEXT

The actual text content of the chunk.

embedding

VECTOR

The vector embedding of chunk_text.

4.0 API Contracts
The backend will expose two primary RESTful API endpoints.

POST /upload
Description: Accepts a PDF file, processes it through the ingestion pipeline, and stores it in the database.

Request Body: multipart/form-data containing the file.

Responses:

200 OK: Successful ingestion. The body contains { "document_id": <new_id> }.

400 Bad Request: Invalid file type or unprocessable PDF.

500 Internal Server Error: An unexpected error occurred during processing.

POST /chat
Description: Accepts a user question for a specific document and returns a context-aware AI answer.

Request Body: JSON object { "document_id": <id>, "question": "<user_question>" }.

Responses:

200 OK: Successful response. The body contains the AI-generated answer as a string or a stream.

404 Not Found: The specified document_id does not exist.

500 Internal Server Error: An unexpected error occurred during the RAG process.

5.0 Deployment & DevOps
The deployment strategy remains consistent with the MVP, with the addition of database management.

Backend: The FastAPI application will be containerized using Docker and deployed to Google Cloud Run. The database connection string will be managed as a secret environment variable.

Frontend: The React application will be deployed to Vercel and connected to its GitHub repository for continuous deployment.

Database: For production, a managed PostgreSQL service (like Google Cloud SQL or Neon) will be used.

6.0 Security Considerations
API Key Management: The GEMINI_API_KEY and database credentials will be stored as secrets in Google Cloud Run's environment variable settings and never committed to source code.

Input Validation: The backend will strictly validate all inputs, including file types on upload and the structure of JSON payloads for chat requests.

CORS: The FastAPI backend will maintain a strict CORS policy to only accept requests from the deployed frontend's domain.