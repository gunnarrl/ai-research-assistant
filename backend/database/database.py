from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

print(f"--- FastAPI app is using database: {DATABASE_URL} ---")

# Create the SQLAlchemy engine
# The engine is the entry point to the database.
engine = create_engine(DATABASE_URL)

# Create a SessionLocal class
# Each instance of SessionLocal will be a database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class
# We will inherit from this class to create each of the ORM models.
Base = declarative_base()