Part 1: Integration - arXiv API Search & Ingestion 📚
☐ Task 1: Backend - Create arXiv Search Endpoint

Goal: Allow users to search for papers on the arXiv database directly from your application.

Actions:

Add the arxiv library to your backend/requirements.txt and install it.

Create a new GET /arxiv/search endpoint in backend/main.py that accepts a search query string.

In this endpoint, use the arxiv library to query the arXiv API.

Format the results into a clean JSON response, including fields like title, authors, summary, and pdf_url for each paper.

Definition of Done: Making a GET request to /arxiv/search?query=<your_topic> returns a JSON list of relevant research papers from arXiv.

☐ Task 2: Frontend - Build arXiv Search Interface

Goal: Create a user interface on the dashboard for searching arXiv.

Actions:

In frontend/src/components/dashboard/DashboardPage.jsx, add a new component or section for "Search arXiv".

Include a text input for the search query and a "Search" button.

When the user searches, make a fetch call to your new GET /arxiv/search backend endpoint.

Display the search results in a clear, scrollable list. Show the title, authors, and summary for each paper.

Definition of Done: A user can type a research topic into the dashboard, click "Search", and see a list of papers from arXiv displayed on the page.

☐ Task 3: Backend - Create "Import from URL" Endpoint

Goal: Develop a backend endpoint that can download a PDF from a given URL and process it.

Actions:

Create a new POST /import-from-url endpoint in backend/main.py that requires authentication.

The request body should contain the pdf_url and title of the paper to import.

The endpoint will use a library like httpx to download the PDF content into memory as bytes.

Once downloaded, it should trigger the exact same background processing task used by the direct upload endpoint (process_pdf_background), passing it the file bytes, filename, and user ID.

Definition of Done: Sending a POST request to /import-from-url with a valid PDF URL and title successfully starts the background processing and creates a new entry in the documents table with a "PROCESSING" status.

☐ Task 4: Frontend - Add "Import" Functionality to UI

Goal: Allow users to import a paper from the arXiv search results into their personal library.

Actions:

In the arXiv search results list on the dashboard, add an "Import" button to each paper.

When a user clicks "Import", make a fetch call to your new POST /import-from-url endpoint, sending the paper's pdf_url and title.

After the import is successfully initiated, refresh the user's document list. The newly imported paper should appear with a "Processing..." status indicator.

Definition of Done: A user can click the "Import" button on an arXiv search result, and the paper will be added to their "My Documents" list, where it will be processed just like a manually uploaded file.

Part 2: AI - Structured Data Extraction 📊
☐ Task 5: Backend - Enhance Document Model

Goal: Add a place in the database to store structured, extracted information about a document.

Actions:

In backend/database/models.py, add a new column to the Document model called structured_data of type JSON (from sqlalchemy.dialects.postgresql). Allow it to be nullable.

Generate a new Alembic migration (alembic revision --autogenerate -m "add_structured_data_to_documents") and apply it (alembic upgrade head).

Definition of Done: The documents table in your PostgreSQL database now has a structured_data column of type jsonb.

☐ Task 6: Backend - Create Structured Extraction Service

Goal: Use the LLM to extract key information (like methodology, datasets, and key findings) into a structured format.

Actions:

In backend/services/gemini_service.py, create a new async function extract_structured_data(context: str) -> dict.

Craft a specific prompt that instructs the Gemini model to act as a research analyst and extract key information from the provided text. The prompt should explicitly ask for the output in a JSON format (e.g., {"methodology": "...", "dataset": "...", "key_findings": ["...", "..."]}).

This function will call the Gemini API with the specialized prompt and parse the JSON string response into a Python dictionary.

Definition of Done: The extract_structured_data function can be called with a block of text and returns a Python dictionary containing the extracted information.

☐ Task 7: Backend - Integrate Extraction into Processing Task

Goal: Automatically extract structured data whenever a new document is processed.

Actions:

Modify the process_pdf_background function in backend/main.py.

After the text has been successfully extracted (extracted_text), make a call to your new extract_structured_data function, passing in the full text (or a representative sample).

Store the resulting dictionary in the structured_data column of the Document record before committing the final "COMPLETED" status.

Definition of Done: After a new document is successfully processed, its structured_data column in the database is populated with the JSON object extracted by the LLM.

☐ Task 8: Frontend - Display Extracted Data

Goal: Show the extracted key information in the UI to give the user a quick overview of the paper.

Actions:

When a user selects a document, fetch the document details, including the structured_data field.

In the ChatPane.jsx or a new component, display this structured data in a clean, readable format above the chat window (e.g., using definition lists or cards for Methodology, Dataset, etc.).

Definition of Done: When a user opens the chat view for a document, they can immediately see the key extracted information without having to ask for it.

Part 3: AI - Cross-Document Analysis 🔄
☐ Task 9: Frontend - Update Dashboard for Multi-Select

Goal: Allow users to select multiple documents to chat with simultaneously.

Actions:

In frontend/src/components/dashboard/DashboardPage.jsx, modify the document list to include checkboxes next to each document.

Manage the list of selected document IDs in the component's state.

Add a new "Chat with Selected (#)" button that becomes active when one or more documents are selected.

Definition of Done: The user can check multiple documents on their dashboard, and a button to initiate a multi-document chat becomes enabled.

☐ Task 10: Backend - Create Multi-Document Chat Endpoint

Goal: Build a new API endpoint that can handle questions across a set of documents.

Actions:

Create a new POST /chat/multi endpoint in backend/main.py.

The request body should be a JSON object containing a list of document_ids and the user's question.

This endpoint will need to perform a vector search across all TextChunk tables associated with the provided document_ids.

Definition of Done: A new /chat/multi endpoint exists that can accept a list of document IDs and a question.

☐ Task 11: Backend - Implement Cross-Document Search

Goal: Modify the vector search logic to retrieve relevant chunks from multiple documents.

Actions:

In backend/services/search_service.py, create a new function find_relevant_chunks_multi(document_ids: list[int], question: str, db: Session).

Inside this function, generate the question embedding as before.

Write a SQLAlchemy query that searches for the most relevant chunks where the document_id is IN the provided list of IDs.

The function should return the most relevant chunks from across all specified documents. You might also want to include the source document's filename with each chunk to inform the LLM of its origin.

Definition of Done: The find_relevant_chunks_multi function returns a list of the most relevant text chunks from all specified documents combined.

☐ Task 12: Frontend - Connect Multi-Chat to Backend

Goal: Wire up the multi-document chat interface to the new backend endpoint.

Actions:

When the user clicks the "Chat with Selected" button, navigate them to the chat view. The chat view should now be aware that it is in "multi-document" mode.

When the user sends a message, the handleSendMessage function should call the new POST /chat/multi endpoint, sending the list of selected document_ids and the question.

The response should be streamed and displayed in the chat window just like the single-document chat.

Definition of Done: A user can select multiple documents, ask a question, and receive a single, synthesized answer from the LLM based on context retrieved from all selected papers.