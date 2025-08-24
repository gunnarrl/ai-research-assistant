# AI Research Paper Analyzer: MVP Task List

This document outlines the sequential tasks required to build, containerize, and deploy the Minimum Viable Product (MVP). Each task is designed to be small, modular, and result in a testable outcome.

## Phase 1: Backend API Development (FastAPI) 🐍

### ☐ Task 1: Initialize FastAPI Project

-   **Goal**: Set up the basic Python backend project structure.
-   **Actions**:
    1.  Create a project directory for the backend.
    2.  Set up a Python virtual environment and install `fastapi` and `uvicorn`.
    3.  Create a `main.py` file.
    4.  Implement a simple health check endpoint at `GET /health` that returns `{"status": "ok"}`.
-   **Definition of Done**: The server can be started with `uvicorn main:app --reload`, and navigating to `http://127.0.0.1:8000/health` in a browser returns a successful status message.

---

### ☐ Task 2: Implement PDF Upload Endpoint

-   **Goal**: Create an API endpoint that can accept a PDF file.
-   **Actions**:
    1.  In `main.py`, create a `POST /summarize` endpoint.
    2.  Use FastAPI's `UploadFile` feature to handle a `multipart/form-data` file upload.
    3.  Add validation to ensure the uploaded file has a `Content-Type` of `application/pdf`. If not, raise a `400 Bad Request` HTTP exception.
    4.  For now, on successful upload, return a JSON response like `{"filename": "<uploaded_file_name>", "content_type": "<file_content_type>"}`.
-   **Definition of Done**: The endpoint can be tested with a tool like Postman or `curl`. It successfully accepts PDF files and correctly rejects non-PDF files.

---

### ☐ Task 3: Integrate PDF Text Extraction

-   **Goal**: Extract the full text from the uploaded PDF.
-   **Actions**:
    1.  Install the `PyMuPDF` library.
    2.  Modify the `POST /summarize` endpoint. After receiving the file, read its contents in-memory.
    3.  Use `PyMuPDF` to iterate through the PDF pages and concatenate all text into a single string.
    4.  Update the success response to return a JSON object containing the extracted text: `{"text": "<extracted_text>"}`.
-   **Definition of Done**: Uploading a PDF to the `/summarize` endpoint returns a JSON response containing the complete text content of the document.

---

### ☐ Task 4: Integrate Google Gemini for Summarization

-   **Goal**: Send the extracted text to the Gemini API and get a summary.
-   **Actions**:
    1.  Install `google-generativeai` and `python-dotenv`.
    2.  Create a `.env` file to store `GEMINI_API_KEY=<your_key>` and add `.env` to `.gitignore`.
    3.  Create a separate module (e.g., `gemini_service.py`) to encapsulate the logic for calling the Gemini API.
    4.  The `/summarize` endpoint should now call the Gemini service with the extracted text and a prompt like "Summarize the following research paper: ...".
    5.  Return the summary from Gemini in the final JSON response: `{"summary": "<gemini_summary>"}`.
-   **Definition of Done**: Uploading a PDF to the `/summarize` endpoint returns a concise, AI-generated summary of the paper.

---

### ☐ Task 5: Finalize Backend (CORS & Error Handling)

-   **Goal**: Prepare the API for frontend integration and make it more robust.
-   **Actions**:
    1.  Implement FastAPI's `CORSMiddleware` to allow requests from `http://localhost:3000` (for local frontend development).
    2.  Add `try...except` blocks to handle potential errors during file processing or the Gemini API call.
    3.  Return meaningful error messages and appropriate status codes (e.g., `500 Internal Server Error`) in a consistent JSON format: `{"detail": "Error message"}`.
-   **Definition of Done**: The API can handle requests from a separate frontend application running on localhost and returns proper error responses for failures.

## Phase 2: Frontend Application Development (React) ⚛️

### ☐ Task 6: Initialize React Project

-   **Goal**: Set up the basic frontend project structure.
-   **Actions**:
    1.  In a new `/frontend` directory, initialize a React project using Vite (`npm create vite@latest`).
    2.  Clean the default `App.jsx` component, removing boilerplate content.
    3.  Ensure the development server runs successfully with `npm run dev`.
-   **Definition of Done**: A minimal React application is running and accessible at `http://localhost:3000`.

---

### ☐ Task 7: Build the UI Components

-   **Goal**: Create the user interface for file selection and summary display.
-   **Actions**:
    1.  In `App.jsx`, create a simple form.
    2.  Add a styled file input element that is restricted to `.pdf` files.
    3.  Add a "Summarize" button.
    4.  Add a designated area (e.g., a `<pre>` or `<div>` tag) below the form where the summary will be displayed.
-   **Definition of Done**: The UI is rendered on the page with a file selector, a button, and an empty area for the result.

---

### ☐ Task 8: Implement API Call Logic

-   **Goal**: Connect the frontend UI to the backend API.
-   **Actions**:
    1.  Use state management (e.g., `useState`) to store the selected file, the summary result, loading status, and any errors.
    2.  Create an `async` function that is triggered when the "Summarize" button is clicked.
    3.  This function should use the `fetch` API to send the selected file in a `FormData` object to `http://127.0.0.1:8000/summarize`.
    4.  While the request is pending, set the loading state to true (e.g., disable the button and show a "Loading..." message).
-   **Definition of Done**: Clicking the "Summarize" button successfully sends the PDF to the locally running backend, and the loading state changes appropriately.

---

### ☐ Task 9: Display Results and Handle Errors

-   **Goal**: Show the summary or any errors to the user.
-   **Actions**:
    1.  Upon receiving a successful `200 OK` response from the API, update the state with the summary text and render it in the display area.
    2.  If the API returns an error, update the state with the error message and display it to the user.
    3.  Ensure the loading state is reset after the request completes (either successfully or with an error).
-   **Definition of Done**: The full end-to-end flow is working locally. A user can upload a PDF, see a loading indicator, and then view the final summary or an error message on the screen.

## Phase 3: Containerization & Cloud Deployment ☁️

### ☐ Task 10: Dockerize the FastAPI Application

-   **Goal**: Package the backend into a portable Docker container.
-   **Actions**:
    1.  Create a `requirements.txt` file (`pip freeze > requirements.txt`).
    2.  Create a `Dockerfile` in the backend's root directory that installs dependencies and runs the Uvicorn server.
    3.  Create a `.dockerignore` file to exclude unnecessary files like `.venv` and `__pycache__`.
-   **Definition of Done**: The backend can be built (`docker build`) and run (`docker run`) as a container, and the API is accessible via the mapped port.

---

### ☐ Task 11: Deploy Backend to Google Cloud Run

-   **Goal**: Host the containerized backend on a scalable, serverless platform.
-   **Actions**:
    1.  Set up a Google Cloud project and enable the Artifact Registry and Cloud Run APIs.
    2.  Create a repository in Artifact Registry.
    3.  Push the Docker image to the Artifact Registry.
    4.  Create a Cloud Run service, select the pushed container image, and configure it to allow unauthenticated access.
    5.  Add the `GEMINI_API_KEY` as a secret environment variable in the Cloud Run service configuration.
-   **Definition of Done**: The backend API is live and accessible via its public Cloud Run URL.

---

### ☐ Task 12: Deploy Frontend and Finalize Configuration

-   **Goal**: Deploy the frontend and connect it to the live backend.
-   **Actions**:
    1.  Push the entire project (both `/frontend` and `/backend` directories) to a new GitHub repository.
    2.  Create a new Vercel project and link it to the GitHub repository, configuring the root directory to be `/frontend`.
    3.  In the React code, change the API endpoint URL from `http://localhost:8000` to the public Google Cloud Run URL. Commit and push this change to trigger a new Vercel deployment.
    4.  Update the CORS configuration on the deployed Google Cloud Run service to accept requests from your Vercel app's domain.
-   **Definition of Done**: The live web application is fully functional. Users can visit the Vercel URL, upload a PDF, and receive a summary from the production backend running on Cloud Run.