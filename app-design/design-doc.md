1.0 Introduction
This document outlines the technical design for the AI Research Paper Analyzer, a full-stack web application. The primary goal of the Minimum Viable Product (MVP) is to provide users with an AI-generated summary of an uploaded PDF research paper. This system is designed as a portfolio piece, emphasizing modern, scalable, and production-ready software engineering practices, including containerization and cloud deployment.

2.0 System Architecture
The application follows a decoupled, service-oriented architecture. The frontend is a single-page application (SPA) that communicates with a containerized backend API. The backend orchestrates the core logic of text extraction and interfacing with an external AI service for summarization.

2.1 Architectural Diagram
The following diagram illustrates the flow of data and the interaction between system components:

1. Upload: The user uploads a PDF via the React frontend.

2. API Request: The frontend sends the PDF in a multipart/form-data request to the FastAPI backend hosted on Google Cloud Run.

3. Text Extraction: The backend uses the PyMuPDF library to extract the full text from the PDF.

4. AI Service Call: The backend sends the extracted text to the Google Gemini API for summarization.

5. AI Response: The Gemini API returns the generated summary as a text string.

6. API Response: The backend forwards the summary to the frontend in a JSON response.

7. Display: The React frontend displays the summary to the user.

2.2 Component Breakdown
Frontend: A React.js single-page application hosted on Vercel (or Netlify). It is responsible for providing the user interface for file uploads and displaying the final summary. It is a static build, served globally via a CDN for low latency.

Backend: A Python FastAPI application responsible for all business logic.

It exposes a single API endpoint to handle file uploads.

It performs text extraction from PDF files.

It communicates with the Google Gemini API.

It is packaged as a Docker container and deployed on Google Cloud Run, a serverless platform that automatically scales based on incoming traffic.

AI Service: The Google Gemini API is used as an external service. It takes a text input and a prompt and returns a generated summary. Communication occurs via a secure REST API call authenticated with an API key.

Container Registry: Google Artifact Registry is used to store and manage the backend's Docker images. It serves as the private, secure source from which Cloud Run pulls the container image for deployment.

3.0 Data Models
For the MVP, data is not persisted. The data models describe the structure of the data in transit between services.

3.1 API Request/Response
File Upload Request: The request from the frontend to the backend is a multipart/form-data POST request containing the PDF file.

file: The PDF document (<filename>.pdf).

Summary Response (Success): A JSON object containing the summary.

JSON

{
  "summary": "This is the AI-generated summary of the research paper..."
}
Error Response: A JSON object detailing the error.

JSON

{
  "detail": "A human-readable error message."
}
3.2 Gemini API Integration
Request to Gemini API: A JSON payload sent from our backend to the Google Gemini API.

JSON

{
  "contents": [
    {
      "parts": [
        {
          "text": "Summarize the following research paper: [EXTRACTED_TEXT_FROM_PDF]"
        }
      ]
    }
  ]
}
Response from Gemini API: The response from Gemini will contain the generated text, which our backend will parse to extract the summary.

4.0 API Contracts
The backend exposes a single RESTful API endpoint.

POST /summarize
Description: Accepts a PDF file, extracts its text, generates a summary, and returns it.

Method: POST

URL: /summarize

Request Header:

Content-Type: multipart/form-data

Request Body:

file: The research paper in .pdf format.

Responses:

200 OK: Successful summarization. The body contains the summary JSON object.

400 Bad Request: The uploaded file is invalid, not a PDF, or missing. The body contains an error JSON object.

422 Unprocessable Entity: The file is a valid type but cannot be processed by the server.

500 Internal Server Error: An unexpected error occurred on the backend, such as a failure to connect to the Gemini API.

5.0 Deployment & DevOps
The project will use Git and GitHub for version control. Continuous Integration and Continuous Deployment (CI/CD) pipelines will be established for both the frontend and backend.

5.1 Backend Deployment (Google Cloud Run)
Trigger: A push or merge to the main branch on GitHub.

Build: A GitHub Actions workflow builds the FastAPI application into a Docker image.

Push: The newly built Docker image is tagged and pushed to Google Artifact Registry.

Deploy: The GitHub Actions workflow then triggers a new deployment on Google Cloud Run, instructing it to pull the latest image version from the Artifact Registry. Environment variables, including the GEMINI_API_KEY, will be managed as secrets within Cloud Run.

5.2 Frontend Deployment (Vercel)
Trigger: A push or merge to the main branch on GitHub.

Build & Deploy: The Vercel platform automatically detects the code change, runs the npm run build command to create a production build of the React app, and deploys the resulting static files to its global CDN.

6.0 Security Considerations
API Key Management: The Google Gemini API key is sensitive. It will be managed using a .env file locally (and included in .gitignore). For deployment, it will be stored as a secret in Google Cloud Run's environment variable settings, ensuring it is never exposed in source code or build artifacts.

Input Validation: The backend will strictly validate file uploads to ensure they are of the application/pdf MIME type. It will also implement error handling to gracefully manage corrupted or unreadable PDFs to prevent server crashes.

Cross-Origin Resource Sharing (CORS): The FastAPI backend will be configured with a CORS policy to only accept requests from the deployed frontend's domain, preventing unauthorized websites from using the API.