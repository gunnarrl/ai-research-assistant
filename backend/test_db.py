import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv

# Load environment variables from backend/.env
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("\nFAILED: DATABASE_URL environment variable not found.")
    print("Please ensure your backend/.env file is in the correct directory and contains the DATABASE_URL.")
else:
    print("Attempting to connect to the database...")
    print(f"Connection URL from environment: {DATABASE_URL}")

    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            print("\nSUCCESS: Connection to the database was successful!")
            result = connection.execute(text("SELECT version()"))
            db_version = result.scalar()
            print(f"PostgreSQL Version: {db_version}")

    except OperationalError as e:
        print("\nFAILED: Could not connect to the database.")
        print("This confirms the issue is NOT specific to Alembic or FastAPI.")
        print("\n--- Error Details ---")
        print(e)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")