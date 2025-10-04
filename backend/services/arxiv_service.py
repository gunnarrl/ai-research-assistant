# backend/services/arxiv_service.py
import arxiv
from typing import List, Dict

def perform_arxiv_search(query: str, max_results: int = 10) -> List[Dict]:
    """
    Performs a search on the arXiv API and returns formatted results.

    Args:
        query: The search topic.
        max_results: The maximum number of results to fetch from arXiv.

    Returns:
        A list of dictionaries, each representing a found paper.
    """
    try:
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        results = []
        for r in search.results():
            results.append({
                "title": r.title,
                "authors": [a.name for a in r.authors],
                "summary": r.summary,
                "pdf_url": r.pdf_url
            })
        return results
    except Exception as e:
        print(f"An error occurred during arXiv search: {e}")
        # In the context of the agent, we don't want to raise an HTTPException.
        # Returning an empty list is a safe fallback.
        return []