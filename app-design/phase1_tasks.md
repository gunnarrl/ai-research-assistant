AI Research Assistant: Phase 1 Task List
The Core AI Upgrade: Interactive Document Analysis (RAG)
This document outlines the sequential tasks required to upgrade the MVP from a simple summarizer to an interactive "Chat with Your Document" application. This phase implements a full Retrieval-Augmented Generation (RAG) pipeline.

Part 1: Foundational Backend Changes (Database & Vector Store) 🐘
☐ Task 1: Set Up Local PostgreSQL with Docker
Goal: Create a reliable, local database environment that mirrors a production setup.

Actions:

Create a docker-compose.yml file in the project's root directory.

Define a service for PostgreSQL (e.g., using the postgres:15 image).

Define a service for a vector-enabled version of Postgres (e.g., using the pgvector/pgvector:pg16 image).

Configure the service to use a persistent volume for the database data, so it isn't lost when the container stops.

Set environment variables for the default user, password, and database name.

Definition of Done: You can run docker-compose up -d and connect to the local PostgreSQL server using a database tool like DBeaver or psql.

☐ Task 2: Integrate SQLAlchemy and Define Models
Goal: Connect the FastAPI application to the new database and define the data structures.

Actions:

Add sqlalchemy, psycopg2-binary, and alembic to your backend/requirements.txt and install them.

Create a new database.py module in the backend to handle the database connection logic and session management.

Create a models.py module. Inside, define a Document table to store metadata about uploaded PDFs (e.g., id, filename, upload_date).

In models.py, also define a TextChunk table. It should include columns for id, document_id (a foreign key to the Document table), the chunk_text itself, and an embedding column of type VECTOR.

Use Alembic to initialize a migration script and apply it to create the tables in your database.

Definition of Done: The FastAPI application successfully connects to the PostgreSQL database on startup, and the documents and text_chunks tables are created and visible in your database.

Part 2: The RAG Pipeline (Document Ingestion) 🧠
☐ Task 3: Implement Text Chunking
Goal: Break down the large text extracted from a PDF into smaller, meaningful pieces for embedding.

Actions:

Create a new utility module, e.g., backend/utils/text_processing.py.

Inside, write a function chunk_text(text: str) -> list[str].

Implement a chunking strategy. A good starting point is a simple recursive character splitter that aims for chunks of about 500-1000 characters with some overlap.

Definition of Done: The chunk_text function can be tested independently and correctly splits a large block of text into a list of smaller, overlapping strings.

☐ Task 4: Integrate an Embedding Model
Goal: Set up the capability to convert text chunks into vector embeddings.

Actions:

Add the sentence-transformers library to requirements.txt and install it.

In your gemini_service.py (or a new embedding_service.py), create a function that initializes and loads a pre-trained embedding model (e.g., all-MiniLM-L6-v2).

Create a function generate_embeddings(texts: list[str]) -> list[list[float]] that takes a list of text chunks and returns a list of their corresponding vector embeddings.

Definition of Done: You can pass a list of text strings to generate_embeddings and receive a list of vectors as output.

☐ Task 5: Re-architect the Upload Endpoint
Goal: Replace the old /summarize logic with the new RAG ingestion pipeline.

Actions:

Rename the POST /summarize endpoint to POST /upload.

When a PDF is uploaded, the endpoint should now perform the following sequence:
a. Extract the full text from the PDF.
b. Save the document's metadata to the documents table in PostgreSQL and get its new id.
c. Use your utility to chunk the extracted text.
d. Use your service to generate embeddings for all text chunks.
e. Save each text chunk and its corresponding embedding to the text_chunks table, linking them to the document_id.

The endpoint should return a success message including the new document_id.

Definition of Done: Uploading a PDF successfully populates both the documents and text_chunks tables in the database. The text_chunks table contains the text and the vector embeddings.

Part 3: The AI Chat Logic (Retrieval & Generation) 💬
☐ Task 6: Implement Vector Search
Goal: Create a function that can find the most relevant text chunks from a document based on a user's question.

Actions:

In a new backend service module, create a function find_relevant_chunks(document_id: int, question: str).

Inside this function:
a. Generate an embedding for the user's question.
b. Write a SQLAlchemy query that uses pgvector's distance functions (e.g., L2 distance or cosine similarity) to find the top 3-5 text chunks from the database that are closest to the question's embedding for the given document_id.

The function should return the chunk_text of these relevant chunks.

Definition of Done: Calling this function with a question returns a list of the most semantically similar text passages from the correct document in the database.

☐ Task 7: Create the /chat Endpoint
Goal: Build the API endpoint that will power the interactive chat.

Actions:

Create a new POST /chat endpoint in main.py. It should accept a request body containing the document_id and the user's question.

This endpoint will orchestrate the full RAG process:
a. Call find_relevant_chunks() to get the necessary context.
b. Construct a detailed prompt for the Gemini LLM, including the retrieved chunks as context and the user's question. (e.g., "Using the following context, please answer the question. Context: [chunks...] Question: [question...]").
c. Call the Gemini API with this prompt.
d. Return the LLM's answer in the response.

Definition of Done: Sending a request to the /chat endpoint with a document_id and a question successfully returns a contextually relevant answer from the LLM.

Part 4: Frontend Transformation 🎨
☐ Task 8: Redesign UI for Chat
Goal: Convert the static summary display into a functional chat interface.

Actions:

In App.jsx, remove the old ResultsDisplay component logic.

Create a new component, ChatWindow.jsx. This component should have a scrollable div to display a list of messages (from both the user and the AI).

Create a new component, ChatInput.jsx. This will be a form with a text input and a "Send" button.

In App.jsx, manage the state for the entire chat history (an array of message objects).

Definition of Done: The frontend renders a chat-like interface. The user can type a message, but it is not yet connected to the backend.

☐ Task 9: Connect Frontend to Backend
Goal: Make the chat interface fully interactive by connecting it to the new backend endpoints.

Actions:

The file upload form should now call the POST /upload endpoint. After a successful upload, store the returned document_id in the App.jsx state.

When the user submits a message in the ChatInput component:
a. Add the user's message to the chat history state to immediately display it.
b. Make a fetch call to the POST /chat endpoint, sending the document_id and the question.
c. While waiting for the response, display a loading indicator.
d. When the response is received, add the AI's message to the chat history state.

Definition of Done: The entire Phase 1 loop is complete. A user can upload a PDF, which gets processed and stored in the database. The user can then ask questions about the PDF in a chat interface and receive accurate, context-aware answers from the AI.