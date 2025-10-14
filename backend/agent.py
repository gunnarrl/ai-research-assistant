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
from .services.processing_service import process_pdf_and_extract_data, process_pdf_background, process_pdf_for_lit_review

async def _agent_workflow(review_id: int, topic: str):
    """The core asynchronous workflow for the agent."""
    db = SessionLocal()
    
    try:
        review = db.query(LiteratureReview).filter(LiteratureReview.id == review_id).first()
        if not review: return

        # STEP 1: Search & Filter (uses a synchronous library, so we run it in a thread)
        review.status = "SEARCHING"
        db.commit()
        initial_papers = await asyncio.to_thread(perform_arxiv_search, topic, 20)
        asyncio.sleep(2)
        filtered_titles = await filter_relevant_papers(topic, initial_papers)
        asyncio.sleep(15)
        final_papers = [p for p in initial_papers if p['title'] in filtered_titles]
        print(f"[{review_id}] LLM selected {len(final_papers)} relevant papers.")

        # STEP 2: Ingestion & Summarization
        review.status = "SUMMARIZING"
        db.commit()

        doc_id_to_paper_map = {}
        newly_created_docs = []
        papers_to_process = []
        
        for paper in final_papers:
            new_doc, file_bytes = await download_and_create_document(
                pdf_url=paper['pdf_url'], title=paper['title'], owner_id=review.owner_id, db=db
            )
            newly_created_docs.append(new_doc)
            doc_id_to_paper_map[new_doc.id] = paper
            papers_to_process.append({'doc': new_doc, 'bytes': file_bytes})
        
        # --- BATCHING AND DELAY LOGIC ---
        batch_size = 5 # Each paper makes 2 API calls, so 5 * 2 = 10 requests per batch.
        num_batches = -(-len(papers_to_process) // batch_size) # Ceiling division to get total number of batches

        for i in range(num_batches):
            start_index = i * batch_size
            end_index = start_index + batch_size
            batch = papers_to_process[start_index:end_index]
            
            print(f"[{review_id}] Starting processing for batch {i+1}/{num_batches}...")

            batch_tasks = []
            for item in batch:
                task = asyncio.to_thread(
                    process_pdf_for_lit_review,
                    item['bytes'],
                    item['doc'].id
                )
                batch_tasks.append(task)
            
            # Concurrently run all tasks within the current batch
            await asyncio.gather(*batch_tasks)
            
            print(f"[{review_id}] Finished batch {i+1}/{num_batches}.")

            # If it's not the last batch, wait for 60 seconds before starting the next one.
            if i < num_batches - 1:
                print(f"[{review_id}] Rate limit cool-down: waiting 60 seconds...")
                await asyncio.sleep(60)
        
        # --- Gather results using the map ---
        synthesis_data = []
        for doc in newly_created_docs:
            db.refresh(doc)
            if doc.status == "COMPLETED" and doc.structured_data:
                # Use the map to get the original paper's citation info
                source_paper_info = doc_id_to_paper_map[doc.id]
                synthesis_data.append({
                    "filename": doc.filename,
                    "structured_data": doc.structured_data,
                    "source_citation": {
                        "title": source_paper_info['title'],
                        "authors": source_paper_info['authors'],
                        "year": source_paper_info['year']
                    }
                })
            else:
                print(f"[{review_id}] WARNING: Document '{doc.filename}' failed processing.")

        if not synthesis_data:
            raise Exception("No papers could be successfully processed.")

        # STEP 3: Synthesis
        review.status = "SYNTHESIZING"
        db.commit()
        # Pass the enhanced data structure to the synthesis function
        final_review_text = await synthesize_literature_review(topic, synthesis_data)
   
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
