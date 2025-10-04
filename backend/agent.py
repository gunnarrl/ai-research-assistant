# backend/agent.py
import asyncio
import time # 
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks 

from .database.database import SessionLocal
from .database.models import LiteratureReview, Document
from .services.arxiv_service import perform_arxiv_search
from .services.gemini_service import filter_relevant_papers
from .services.importer_service import import_paper_from_url


def run_literature_review_agent(review_id: int, topic: str):
    """
    The main function for the agentic workflow, run as a background task.
    """
    db = SessionLocal()
    try:
        print(f"Starting literature review agent for review_id: {review_id} on topic: '{topic}'")
        
        review = db.query(LiteratureReview).filter(LiteratureReview.id == review_id).first()
        if not review:
            print(f"Error: LiteratureReview with id {review_id} not found.")
            return

        # --- STEP 1: Search & Filter ---
        review.status = "SEARCHING"
        db.commit()
        print(f"[{review_id}] Agent Status: SEARCHING")

        # Call the arXiv service to get an initial list of papers
        initial_papers = perform_arxiv_search(topic, max_results=10)
        if not initial_papers:
            raise Exception("No papers found on arXiv for the topic.")
        
        print(f"[{review_id}] Found {len(initial_papers)} initial papers from arXiv.")

        # Use the LLM to filter the list down to the most relevant ones
        print(f"[{review_id}] Asking LLM to filter for relevance...")
        filtered_titles = asyncio.run(filter_relevant_papers(topic, initial_papers))
        
        if not filtered_titles:
            raise Exception("LLM failed to filter relevant papers.")

        # Create the final list of paper objects based on the titles
        final_papers = [p for p in initial_papers if p['title'] in filtered_titles]
        print(f"[{review_id}] LLM selected {len(final_papers)} relevant papers:")
        for paper in final_papers:
            print(f"  - {paper['title']}")
            
        # --- STEP 2: Ingestion & Summarization ---
        review.status = "SUMMARIZING"
        db.commit()
        print(f"[{review_id}] Agent Status: SUMMARIZING")
        
        summaries = []
        # The agent needs its own BackgroundTasks instance to run the ingestion
        background_tasks = BackgroundTasks()

        for paper in final_papers:
            print(f"[{review_id}] Importing paper: '{paper['title']}'")
            
            # Use a separate async function to handle the async import call
            new_doc = asyncio.run(import_paper_from_url(
                pdf_url=paper['pdf_url'],
                title=paper['title'],
                owner_id=review.owner_id,
                db=db,
                background_tasks=background_tasks
            ))
            
            # Poll for completion status
            timeout = 300  # 5 minutes timeout
            start_time = time.time()
            while time.time() - start_time < timeout:
                db.refresh(new_doc)
                if new_doc.status == "COMPLETED":
                    print(f"[{review_id}] Successfully processed document ID: {new_doc.id}")
                    if new_doc.structured_data and not new_doc.structured_data.get('error'):
                        # Add filename for context in the final synthesis step
                        summary_with_source = new_doc.structured_data
                        summary_with_source['source_filename'] = new_doc.filename
                        summaries.append(summary_with_source)
                    break
                elif new_doc.status == "FAILED":
                    print(f"[{review_id}] WARNING: Processing failed for document ID: {new_doc.id}")
                    break
                
                print(f"[{review_id}] Waiting for document ID {new_doc.id} to be processed... (Status: {new_doc.status})")
                time.sleep(10) # Wait 10 seconds before checking again
            else:
                print(f"[{review_id}] WARNING: Timeout reached for document ID: {new_doc.id}")

        if not summaries:
            raise Exception("Failed to process and summarize any of the selected papers.")
        # ------------------------------------

        # Task 12: Synthesis (placeholder)
        review.status = "SYNTHESIZING"
        db.commit()
        print(f"[{review_id}] Agent Status: SYNTHESIZING")
        
        # Simulate remaining work
        import time
        time.sleep(5) 

        review.result = f"This is a placeholder. The agent found {len(final_papers)} relevant papers for the topic '{topic}'."
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