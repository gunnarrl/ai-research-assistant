# backend/services/citation_service.py

from typing import List, Dict, Optional
from backend.services.gemini_service import parse_references_from_text # We will reuse the LLM parsing function

def find_and_isolate_references_text(text: str) -> Optional[str]:
    """
    Finds the 'References' or 'Bibliography' section by searching from the end of the document.

    Args:
        text: The full text of the document.

    Returns:
        The text content of the references section, or None if not found.
    """
    # Convert text to lowercase for case-insensitive search
    lower_text = text.lower()
    
    # Find the starting index of the last occurrence of "references" or "bibliography"
    last_ref_index = lower_text.rfind("references")
    last_bib_index = lower_text.rfind("bibliography")
    last_cit_index = lower_text.rfind("citations")
    last_works_index = lower_text.rfind("works cited")
    
    start_index = max(last_ref_index, last_bib_index, last_cit_index, last_works_index)
    
    if start_index != -1:
        # Return the slice of the original text from the found index to the end
        return text[start_index:]
        
    print("Could not programmatically find a 'References' or 'Bibliography' section.")
    return None


async def extract_citations_from_text(text: str) -> List[Dict]:
    """
    Extracts structured bibliographic information from a paper's full text using a hybrid approach.

    Args:
        text: The full text of the paper.

    Returns:
        A list of dictionaries, where each dictionary represents a parsed citation.
    """
    # Step 1: Isolate the reference text using our reliable function
    references_text = find_and_isolate_references_text(text)
    
    if not references_text:
        return []
    
    # Step 2: Pass ONLY the isolated text to the LLM for parsing
    try:
        # This re-uses the focused LLM function from our first attempt
        structured_citations = await parse_references_from_text(references_text)
        return structured_citations
    except Exception as e:
        print(f"An error occurred during citation parsing: {e}")
        return [{"error": "Failed to parse citations from text."}]