# AI Research Assistant

[![Backend](https://github.com/gunnarrl/ai-research-assistant/actions/workflows/deploy-backend.yml/badge.svg)](https://github.com/gunnarrl/ai-research-assistant/actions/workflows/deploy-backend.yml)

[![Frontend](https://github.com/gunnarrl/ai-research-assistant/actions/workflows/deploy-frontend.yml/badge.svg)](https://github.com/gunnarrl/ai-research-assistant/actions/workflows/deploy-frontend.yml)

## Visit the Site

**[🚀 Try the AI Research Assistant live here!](https://ai-research-assistant-eight.vercel.app)**
---
The AI Research Assistant is a full-stack web application designed to help researchers, students, and professionals accelerate their work by leveraging the power of Large Language Models (LLMs). The application allows users to upload PDF documents, engage in interactive chats about their content, create collaborative projects, and even automate the process of writing a literature review.

This project is built with a modern, decoupled architecture, featuring a FastAPI backend, a React frontend, and a PostgreSQL database with vector capabilities.

## Cloud Hosting & Architecture

The application is deployed using a modern cloud infrastructure:

* **Frontend (React):** Hosted on **Vercel** for fast, reliable, and serverless distribution of the static assets.
* **Backend (FastAPI):** Deployed as a containerized service on **Google Cloud Run**, providing auto-scaling and cost-efficiency for the API and long-running background tasks.
* **Database (PostgreSQL with pgvector):** Hosted on **Neon**, a serverless Postgres platform, which offers branching, autoscaling, and a robust environment for both the relational data and the vector embeddings required for the RAG pipeline.

---

## Features

* **Interactive Document Chat (RAG):** Upload your own PDF documents and ask specific questions about their content. The application uses a Retrieval-Augmented Generation (RAG) pipeline to provide context-aware, accurate answers based solely on the document's text.
* **Multi-Document Analysis:** Select multiple documents and ask comparative or synthesizing questions. The AI will retrieve context from all selected papers to provide a comprehensive answer.
* **User Authentication:** Secure user registration and login system, supporting both traditional email/password and Google OAuth 2.0 for easy sign-in.
* **Collaborative Projects:** Create projects, invite other users by email, and add documents to a shared workspace. All project members can view and chat with the documents in the project.
* **Automated Literature Review Agent:** Kick off an AI agent that takes a research topic, searches the arXiv academic database for relevant papers, reads and analyzes them, and generates a complete, formatted literature review with citations and a bibliography.
* **Citation Management:**
    * Automatically generate a BibTeX citation for any uploaded document.
    * For literature reviews, the agent extracts the bibliography from the source papers and includes a formatted reference list.
* **Third-Party Integration:** Seamlessly search for and import papers directly from the arXiv database into your personal library.
* **Asynchronous & Scalable:** The backend is built to handle long-running tasks, like document processing and agent workflows, without blocking the user interface, using a robust background task architecture.

## Tech Stack

* **Backend:**
    * **Framework:** FastAPI
    * **Database:** PostgreSQL with the `pgvector` extension for vector similarity search.
    * **AI Orchestration:** Google Gemini API
    * **Authentication:** JWT (JSON Web Tokens), `passlib`, `python-jose`
    * **Data Models & Migrations:** SQLAlchemy, Alembic
* **Frontend:**
    * **Framework:** React (with Vite)
    * **Styling:** Tailwind CSS (with the Typography plugin for Markdown rendering)
    * **Authentication:** Google OAuth Provider
* **DevOps & Deployment:**
    * **Containerization:** Docker & Docker Compose
    * **Deployment Target (Backend):** Google Cloud Run (or any container service)
    * **Deployment Target (Frontend):** Vercel (or any static host)

## System Architecture

The application uses a Retrieval-Augmented Generation (RAG) pipeline to provide accurate, context-aware answers from user documents.

1.  **Ingestion Flow:** When a user uploads a PDF, the backend extracts the text, splits it into smaller chunks, converts each chunk into a vector embedding, and stores it in the PostgreSQL/pgvector database.
2.  **Chat Flow:** When a user asks a question, the backend generates an embedding for the question, performs a vector similarity search in the database to find the most relevant text chunks, and then passes those chunks along with the original question to the Gemini LLM to generate a final answer.

## Setup and Local Development

Follow these steps to get the project running on your local machine.

### Prerequisites

* **Docker** and **Docker Compose:** To run the PostgreSQL database.
* **Python 3.10+** and `pip`: For the backend.
* **Node.js** and `npm`: For the frontend.

### 1. Clone the Repository

```bash
git clone [https://github.com/your-username/ai-research-assistant.git](https://github.com/your-username/ai-research-assistant.git)
cd ai-research-assistant
```

### 2. Configure Environment Variables

You will need to create two `.env` files for this project.

#### **Backend `.env` file:**

Create a file at `backend/.env` and add the following keys. **Do not commit this file to Git.**

```
# backend/.env

# A strong, randomly generated string for signing JWTs
SECRET_KEY=your_super_secret_key_here

# Your Google Cloud Project credentials for OAuth
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Your API key for the Google Gemini API
GEMINI_API_KEY=your_gemini_api_key
```

#### **Frontend `.env` file:**

The frontend uses Vite's environment variable system. Create a file at `frontend/.env.local`.

```
# frontend/.env.local

VITE_GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
```

### 3. Run the Database

The project includes a `docker-compose.yml` file to easily start the required PostgreSQL database with the `pgvector` extension.

```bash
docker-compose up -d
```

This will start the database container in the background. The data will be persisted in a Docker volume.

### 4. Set Up the Backend

1.  **Navigate to the backend directory and create a virtual environment:**
    ```bash
    cd backend
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

2.  **Install the Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the database migrations:**
    This command will create all the necessary tables in your database.
    ```bash
    alembic upgrade head
    ```

4.  **Start the FastAPI server:**
    ```bash
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
    ```
    The backend API should now be running at `http://localhost:8000`.

### 5. Set Up the Frontend

1.  **Open a new terminal** and navigate to the frontend directory:
    ```bash
    cd frontend
    ```

2.  **Install the Node.js dependencies:**
    ```bash
    npm install
    ```

3.  **Start the Vite development server:**
    ```bash
    npm run dev
    ```
    The React application should now be running at `http://localhost:5173`.

## Usage

* **Register/Login:** Create an account or sign in using your Google account.
* **Upload Documents:** On the dashboard, you can upload PDF files for analysis.
* **Chat with a Document:** Click on an uploaded document to open the chat view, where you can ask questions about its content.
* **Create a Literature Review:** Use the "Literature Review Agent" on the dashboard to enter a topic. The agent will find relevant papers and write a review for you.
* **Manage Projects:** Create a project, add documents to it, and invite other users to collaborate.