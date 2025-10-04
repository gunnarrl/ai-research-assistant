# backend/services/citation_service.py

import re
from typing import List, Dict, Optional
from backend.services.gemini_service import parse_references_from_text

def find_references_section(text: str) -> Optional[str]:
    """
    Finds the 'References' or 'Bibliography' section in a text.

    Args:
        text: The full text of the document.

    Returns:
        The text content of the references section, or None if not found.
    """
    # MODIFIED REGEX: Look for the keyword at the start of a line,
    # but don't require it to be the *only* thing on the line.
    match = re.search(r'^\s*(?:REFERENCES||Bibliography|Citations)\s*', text, re.MULTILINE | re.IGNORECASE)
    
    if match:
        # Return the text from the start of the match to the end of the string
        return text[match.start():]
    
    return None

async def extract_citations_from_text(text: str) -> List[Dict]:
    """
    Extracts structured bibliographic information from a paper's full text.

    This function first locates the references section and then uses an LLM
    to parse it into a structured list of citations.

    Args:
        text: The full text of the paper.

    Returns:
        A list of dictionaries, where each dictionary represents a parsed citation.
    """
    references_text = find_references_section(text)
    
    if not references_text:
        print("Could not find a 'References' or 'Bibliography' section.")
        return []
    
    try:
        structured_citations = await parse_references_from_text(references_text)
        return structured_citations
    except Exception as e:
        print(f"An error occurred during citation parsing: {e}")
        return [{"error": "Failed to parse citations from text."}]