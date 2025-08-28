# backend/services/search_service.py

from sqlalchemy.orm import Session
from backend.database.models import TextChunk
from backend.services.embedding_service import model as embedding_model

def find_relevant_chunks(document_id: int, question: str, db: Session, top_k: int = 5) -> list[str]:
    """
    Finds the most relevant text chunks from a document based on a user's question.

    Args:
        document_id: The ID of the document to search within.
        question: The user's question.
        db: The SQLAlchemy database session.
        top_k: The number of top relevant chunks to return.

    Returns:
        A list of the most relevant text chunk strings.
    """
    # a. Generate an embedding for the user's question using the same model
    question_embedding = embedding_model.encode(question).tolist()

    # b. Write a query to find the top_k closest text chunks
    # We use cosine_distance, a pgvector function, to find the chunks with the
    # smallest distance (i.e., highest similarity) to the question's embedding.
    relevant_chunks = (
        db.query(TextChunk)
        .filter(TextChunk.document_id == document_id)
        .order_by(TextChunk.embedding.cosine_distance(question_embedding))
        .limit(top_k)
        .all()
    )
    
    # The function should return the actual text of the chunks
    return [chunk.chunk_text for chunk in relevant_chunks]

# --- Testing Block ---
# This allows us to test the function independently.
if __name__ == '__main__':
    # NOTE: To run this test, you must have first successfully run Task 5
    # and have a document with chunks in your database.
    
    # Manually create a database session for testing
    from backend.database.database import SessionLocal
    
    test_db_session = SessionLocal()
    
    # --- !! IMPORTANT !! ---
    # --- Change these values to match your data ---
    TEST_DOCUMENT_ID = 2  # The ID of a document you have uploaded
    TEST_QUESTION = "How can LLMS help with code review?" # A question about your document
    # ----------------------------------------------

    print(f"Finding relevant chunks for Document ID: {TEST_DOCUMENT_ID}")
    print(f"Question: '{TEST_QUESTION}'")
    
    try:
        # Call the function
        chunks = find_relevant_chunks(
            document_id=TEST_DOCUMENT_ID,
            question=TEST_QUESTION,
            db=test_db_session
        )
        
        print("\n--- Found Relevant Chunks ---")
        if chunks:
            for i, chunk_text in enumerate(chunks):
                print(f"Chunk {i+1}:")
                print(f'"{chunk_text}..."\n')
        else:
            print(f"No chunks found for Document ID {TEST_DOCUMENT_ID}. "
                  "Please ensure you have uploaded a document and set the correct TEST_DOCUMENT_ID.")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        # Always close the session
        test_db_session.close()