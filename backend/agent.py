# backend/agent.py
# backend/agent.py

import asyncio
import time
from sqlalchemy.orm import Session
from .database.database import SessionLocal
from .database.models import LiteratureReview, Document, Citation, TextChunk
from .services.arxiv_service import perform_arxiv_search
# Import the original async functions
from .services.gemini_service import filter_relevant_papers, synthesize_literature_review
from .services.importer_service import download_and_create_document
# Import the new async processing function
from .services.processing_service import process_pdf_and_extract_data

async def _agent_workflow(review_id: int, topic: str):
    """The core asynchronous workflow for the agent."""
    db = SessionLocal()
    try:
        review = db.query(LiteratureReview).filter(LiteratureReview.id == review_id).first()
        if not review: return

        # STEP 1: Search & Filter (uses a synchronous library, so we run it in a thread)
        review.status = "SEARCHING"
        db.commit()
        initial_papers = await asyncio.to_thread(perform_arxiv_search, topic, 10)
        filtered_titles = await filter_relevant_papers(topic, initial_papers)
        final_papers = [p for p in initial_papers if p['title'] in filtered_titles]
        print(f"[{review_id}] LLM selected {len(final_papers)} relevant papers.")

        # STEP 2: Ingestion & Summarization
        review.status = "SUMMARIZING"
        db.commit()
        
        summaries = []
        for paper in final_papers:
            print(f"[{review_id}] Processing paper: '{paper['title']}'")
            
            # Download and create the initial DB record for the document
            new_doc, file_bytes = await download_and_create_document(
                pdf_url=paper['pdf_url'], title=paper['title'], owner_id=review.owner_id, db=db
            )
            
            # Get all processed data from the pure function
            processed_data = await process_pdf_and_extract_data(file_bytes)

            if processed_data.get("error"):
                print(f"[{review_id}] WARNING: Failed to process '{paper['title']}'. Error: {processed_data['error']}")
                new_doc.status = "FAILED"
                db.commit()
                continue # Skip to the next paper

            # --- All database writes happen here, in the main agent thread ---
            new_doc.structured_data = processed_data["structured_data"]
            
            citations = processed_data["citations"]
            if citations and "error" not in citations[0]:
                for citation_data in citations:
                    db.add(Citation(document_id=new_doc.id, data=citation_data))

            text_chunks = processed_data["text_chunks"]
            embeddings = processed_data["embeddings"]
            for i, chunk_text in enumerate(text_chunks):
                db.add(TextChunk(document_id=new_doc.id, chunk_text=chunk_text, embedding=embeddings[i]))
            
            new_doc.status = "COMPLETED"
            db.commit() # Commit all new data for this document at once
            # -------------------------------------------------------------

            if new_doc.structured_data:
                summary_with_source = new_doc.structured_data
                summary_with_source['source_filename'] = new_doc.filename
                summaries.append(summary_with_source)


        # STEP 3: Synthesis
        review.status = "SYNTHESIZING"
        db.commit()
        final_review_text = await synthesize_literature_review(topic, summaries)
        review.result = final_review_text
        review.status = "COMPLETED"
        db.commit()
        print(f"Agent finished successfully for review_id: {review_id}")

    except Exception as e:
        print(f"Agent failed for review_id: {review_id}. Error: {e}")
        db.rollback()
        review = db.query(LiteratureReview).filter(LiteratureReview.id == review_id).first()
        if review:
            review.status = "FAILED"
            review.result = str(e)
            db.commit()
    finally:
        db.close()

def run_literature_review_agent(review_id: int, topic: str):
    """Synchronous entrypoint that starts the async agent workflow."""
    asyncio.run(_agent_workflow(review_id, topic))