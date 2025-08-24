ai-paper-analyzer/
│
├── .github/
│   └── workflows/
│       ├── backend-deploy.yml    # GitHub Actions for backend CI/CD
│       └── frontend-deploy.yml    # GitHub Actions for frontend CI/CD (optional if using Vercel's integration)
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI application, endpoints
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── gemini_service.py # Logic for calling the Gemini API
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── pdf_parser.py     # Logic for extracting text from PDFs
│   │
│   ├── .dockerignore             # Specifies files to exclude from the Docker image
│   ├── .env                      # Local environment variables (e.g., GEMINI_API_KEY). DO NOT COMMIT.
│   ├── Dockerfile                # Instructions to build the backend Docker container
│   └── requirements.txt          # Python dependencies
│
├── frontend/
│   ├── public/
│   │   ├── favicon.ico           # Application icon
│   │   └── index.html            # Main HTML template for the React app
│   │
│   ├── src/
│   │   ├── components/
│   │   │   ├── FileUploader.jsx  # Component for the file input and button
│   │   │   ├── LoadingSpinner.jsx# A simple loading indicator
│   │   │   └── SummaryDisplay.jsx# Component to display the result or error
│   │   │
│   │   ├── App.css               # Main styles for the application
│   │   ├── App.jsx               # Main application component, state management
│   │   └── main.jsx              # Entry point for the React application
│   │
│   ├── .eslintrc.cjs             # ESLint configuration
│   ├── .gitignore                # Specifies files to exclude from Git (e.g., node_modules)
│   ├── index.html                # Vite's entry HTML file (often moved to root by create-vite)
│   ├── package.json              # Project metadata and npm dependencies
│   ├── package-lock.json         # Exact versions of npm dependencies
│   └── vite.config.js            # Vite build and development server configuration
│
├── .gitignore                    # Global gitignore for the entire project (e.g., .idea/, .vscode/)
├── README.md                     # Project overview, setup instructions, and deployment notes
└── tasks.md                      # The task list for building the MVP