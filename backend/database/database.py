from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Define the database URL using credentials from our docker-compose file
DATABASE_URL = "postgresql+psycopg://admin:password@localhost:5432/ai_research_db"

# Create the SQLAlchemy engine
# The engine is the entry point to the database.
engine = create_engine(DATABASE_URL)

# Create a SessionLocal class
# Each instance of SessionLocal will be a database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class
# We will inherit from this class to create each of the ORM models.
Base = declarative_base()