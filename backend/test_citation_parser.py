# backend/test_citation_parser.py

import asyncio
from backend.utils.pdf_parser import extract_text_from_pdf
from backend.services.citation_service import extract_citations_from_text

# IMPORTANT: Make sure the ESEM2025_LLM.pdf file is in the root of the `ai-research-assistant-phase-4-lit-review` directory
PDF_PATH = "ESEM2025_LLM.pdf"

async def main():
    print(f"--- Testing Citation Extraction for {PDF_PATH} ---")
    
    try:
        with open(PDF_PATH, "rb") as f:
            pdf_bytes = f.read()
        
        print("Step 1: Extracting text from PDF...")
        full_text = extract_text_from_pdf(pdf_bytes)
        
        if not full_text:
            print("Failed to extract text from PDF. Cannot proceed.")
            return

        print("Step 2: Calling the citation extraction service...")
        citations = await extract_citations_from_text(full_text)
        
        print("\n--- Results ---")
        if citations and "error" not in citations[0]:
            print(f"Successfully extracted {len(citations)} citations.")
            # Print the first two citations for verification
            for i, citation in enumerate(citations[:2]):
                print(f"\nCitation {i+1}:")
                print(f"  Title: {citation.get('title')}")
                print(f"  Authors: {citation.get('authors')}")
                print(f"  Year: {citation.get('year')}")
        else:
            print("Failed to extract citations or an error occurred.")
            print(citations)

    except FileNotFoundError:
        print(f"Error: The file '{PDF_PATH}' was not found.")
        print("Please ensure it is in the correct directory before running the test.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())