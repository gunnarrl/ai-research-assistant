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
from .services.processing_service import process_pdf_and_extract_data, process_pdf_background

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
        
        ingestion_tasks = []
        newly_created_docs = []

        for paper in final_papers:
            print(f"[{review_id}] Starting ingestion for: '{paper['title']}'")
            
            # 1. Download the paper and create the initial DB record.
            new_doc, file_bytes = await download_and_create_document(
                pdf_url=paper['pdf_url'], title=paper['title'], owner_id=review.owner_id, db=db
            )
            
            # 2. Instead of processing here, dispatch the standard background task.
            #    We need a new session for each task.
            db_for_task = SessionLocal()
            task = asyncio.to_thread(
                process_pdf_background, 
                file_bytes, 
                new_doc.filename, 
                new_doc.id, 
                db_for_task
            )
            ingestion_tasks.append(task)
            newly_created_docs.append(new_doc)

        # 3. Wait for all the independent ingestion tasks to complete.
        await asyncio.gather(*ingestion_tasks)

        # 4. Gather the results. The data is now in the database.
        summaries = []
        for doc in newly_created_docs:
            db.refresh(doc) 
            if doc.status == "COMPLETED" and doc.structured_data:
                summary_with_source = doc.structured_data
                summary_with_source['source_filename'] = doc.filename
                summaries.append(summary_with_source)
            else:
                print(f"[{review_id}] WARNING: Document '{doc.filename}' failed processing or has no structured data.")

        # --- FIX: Add a check for an empty summaries list ---
        if not summaries:
            raise Exception("No papers could be successfully processed to generate the review.")

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