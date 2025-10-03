Part 1: Utility - Citation Management 📚
Goal: Automatically extract bibliographic information from papers and provide export functionality for citation managers.

☐ Task 1: Backend - Bibliography Parsing Service

Goal: Create a service that can find and parse the "References" or "Bibliography" section of a research paper.

Actions:

Choose and install a Python library for parsing citation strings (e.g., pybtex for BibTeX or a custom regex/LLM-based approach).

In a new backend/services/citation_service.py, create a function extract_citations_from_text(text: str) -> List[dict].

This function should identify the bibliography section of the paper's full text and parse each entry into a structured format (e.g., a list of dictionaries with keys like title, authors, year).

Definition of Done: The extract_citations_from_text function can be called with the full text of a paper and returns a structured list of its citations.

☐ Task 2: Backend - Data Model & Integration

Goal: Store the extracted citations in the database.

Actions:

In backend/database/models.py, create a new Citation model with columns like id, document_id (foreign key), and data (JSON type to store the parsed citation).

Generate and apply a new Alembic migration (alembic revision --autogenerate -m "add_citations_table", alembic upgrade head).

Modify the process_pdf_background task in backend/main.py to call your new citation service and save the extracted citations to the new table after text extraction is complete.

Definition of Done: After a document is processed, the citations table is populated with structured data corresponding to the bibliography found in the PDF.

☐ Task 3: Backend - API for Citations

Goal: Expose the extracted citations through the API.

Actions:

Create a new GET /documents/{document_id}/citations endpoint that requires authentication.

This endpoint should query the citations table for all entries linked to the specified document_id and return them as a JSON list.

Create a GET /documents/{document_id}/citations/export endpoint that takes a format query parameter (e.g., ?format=bibtex).

This endpoint will fetch the citations and convert them into the requested format string. For BibTeX, you'll format the dictionary data into a valid .bib file string.

Definition of Done: You can successfully fetch a list of citations for a document and download a formatted BibTeX file via the API endpoints.

☐ Task 4: Frontend - Display Citations

Goal: Show the extracted bibliography in the user interface.

Actions:

In the ChatPane.jsx, add a new tab or expandable section titled "Bibliography".

When a document is selected, make a new API call to the GET /documents/{document_id}/citations endpoint.

Render the list of citations in a clean, readable format.

Add an "Export as BibTeX" button that, when clicked, triggers a download of the file from the GET /documents/{document_id}/citations/export?format=bibtex endpoint.

Definition of Done: A user can view the full, parsed bibliography of a selected paper and download it as a .bib file.

Part 2: Collaboration - Shared Workspaces 🤝
Goal: Allow multiple users to share, view, and chat with a common set of documents.

☐ Task 5: Backend - Data Models for Collaboration

Goal: Design the database schema to support multi-user projects.

Actions:

In backend/database/models.py, create a Project model with id and name.

Create an association table, project_members, to link User and Project models (many-to-many).

Create another association table, project_documents, to link Document and Project models (many-to-many).

Generate and apply a new Alembic migration to create these tables.

Definition of Done: The projects, project_members, and project_documents tables are created in your database.

☐ Task 6: Backend - Project Management API

Goal: Create endpoints for creating projects and managing their contents.

Actions:

Create a POST /projects endpoint that allows an authenticated user to create a new project. The creator should automatically become the first member.

Create a GET /projects endpoint to list all projects a user is a member of.

Create a POST /projects/{project_id}/members endpoint to invite/add another user to a project by their email.

Create a POST /projects/{project_id}/documents endpoint to add an existing document (that the current user owns) to a project.

Definition of Done: A user can create a project, see it in their list, add another user, and add one of their documents to it via API calls.

☐ Task 7: Backend - Update Access Controls

Goal: Modify existing endpoints to respect project permissions.

Actions:

Modify the GET /documents endpoint to return not only the user's own documents but also all documents belonging to projects they are a member of.

Update the security logic for the GET /documents/{document_id}/file and /chat endpoints. A user should be able to access a document if they either own it directly OR are a member of a project that contains the document.

Definition of Done: A user can successfully chat with a document owned by another user if they are both members of the same project containing that document.

☐ Task 8: Frontend - Projects UI

Goal: Build the interface for users to interact with their projects.

Actions:

In DashboardPage.jsx, add a new "Projects" section or tab.

Fetch and display the user's projects from the GET /projects endpoint.

Add a "Create Project" button and a form.

When a user clicks on a project, navigate them to a project-specific view that lists the documents and members for that project.

From the main document list, add an "Add to Project" option for each document.

Definition of Done: A user can create, view, and manage their projects and the documents within them through the dashboard.

Part 3: Automation - The Literature Review Agent 🤖
Goal: Build a proactive AI agent that can perform a literature review on a given topic.

☐ Task 9: Backend - Literature Review Agent Endpoint

Goal: Create an endpoint to kick off the automated literature review process.

Actions:

Create a new POST /agent/literature-review endpoint that accepts a topic string in the request body.

Since this will be a long-running process, the endpoint should immediately create a LiteratureReview record in a new database table with a "PENDING" status and return its ID.

This endpoint will then trigger a background task (Celery) to perform the actual agentic workflow, passing the literature_review_id and topic.

Definition of Done: Calling the endpoint starts the literature review process in the background and immediately returns an ID that can be used to track its status.

☐ Task 10: Backend - Agent Step 1: Search & Filter

Goal: The agent must find and select the most relevant papers.

Actions:

In the background task, the first step is to call the existing arXiv search service with the user's topic.

Take the search results (titles and summaries) and feed them into an LLM with a prompt like: "Based on the topic '[user's topic]', which of the following papers are most relevant? Return a list of their titles."

The agent will use the LLM's response to filter the initial list down to the most promising papers.

Definition of Done: The agent can programmatically search arXiv and use an LLM to select a handful of the most relevant papers for the given topic.

☐ Task 11: Backend - Agent Step 2: Ingestion & Summarization

Goal: The agent needs to process and "read" each selected paper.

Actions:

For each paper selected in the previous step, the agent will call the POST /import-from-url endpoint to trigger your application's existing ingestion pipeline.

The agent must wait for each paper's status to become "COMPLETED". This means it needs to poll the document's status via the database.

Once a paper is processed, the agent will retrieve its structured_data (methodology, key findings, etc.).

Definition of Done: The agent can take a list of papers, process them through the app's ingestion pipeline, and gather the structured summaries for each one.

☐ Task 12: Backend - Agent Step 3: Synthesis & Final Output

Goal: The agent combines all its research into a final literature review.

Actions:

Gather all the structured_data summaries from the processed papers.

Make a final call to the Gemini API with a comprehensive prompt, such as: "You are a research assistant. Based on the key findings from the following papers, write a cohesive literature review on the topic of '[user's topic]'. Synthesize the findings and cite each paper by its title when you use its information. [Paste all structured summaries here]".

Take the final generated text and save it to the LiteratureReview table in the database, updating its status to "COMPLETED".

Definition of Done: The agent can produce a final, synthesized text that summarizes the findings from multiple papers and stores it in the database.

☐ Task 13: Frontend - Literature Review UI

Goal: Create an interface for the user to start and view the results of the agent.

Actions:

On the dashboard, add a "Literature Review Agent" section with a text input for the research topic and a "Start" button.

When the user starts a review, show a loading/progress indicator. You can create a new GET /agent/literature-review/{review_id} endpoint that the frontend can poll to get the current status ("SEARCHING", "SUMMARIZING", "SYNTHESIZING", "COMPLETED").

Once the status is "COMPLETED", display the final, generated literature review text to the user.

Definition of Done: A user can input a research topic, start the agent, and see the final literature review generated by the AI on their screen.