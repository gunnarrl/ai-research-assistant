# backend/services/arxiv_service.py
import arxiv
from typing import List, Dict

def perform_arxiv_search(query: str, max_results: int = 10) -> List[Dict]:
    """
    Performs a search on the arXiv API and returns formatted results.
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
                "pdf_url": r.pdf_url,
                "year": r.published.year
            })
        return results
    except Exception as e:
        print(f"An error occurred during arXiv search: {e}")
        return []