from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

DATABASE_URL = "postgresql+psycopg://admin:password@localhost:5433/ai_research_db"

print("Attempting to connect to the database...")
print(f"Connection URL: {DATABASE_URL}")

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as connection:
        print("\nSUCCESS: Connection to the database was successful!")

        # Optional: Run a simple query to be 100% sure
        result = connection.execute(text("SELECT version()"))
        db_version = result.scalar()
        print(f"PostgreSQL Version: {db_version}")

except OperationalError as e:
    print("\nFAILED: Could not connect to the database.")
    print("This confirms the issue is NOT specific to Alembic.")
    print("The error is with the fundamental connection from Python to the database.")
    print("\n--- Error Details ---")
    print(e)
except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")