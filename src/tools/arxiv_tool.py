"""ArXiv search tool wrapping the arxiv Python library."""

import arxiv
from agents import function_tool


@function_tool
def arxiv_search(query: str, max_results: int = 3) -> str:
    """Search ArXiv for papers matching the query. Returns titles, abstracts, and links.

    Args:
        query: The search query for ArXiv.
        max_results: Maximum number of papers to return (default 3).
    """
    client = arxiv.Client(page_size=max_results, delay_seconds=0.0, num_retries=2)
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    try:
        results = list(client.results(search))
    except Exception as e:
        return f"ArXiv search failed for '{query}': {e}"

    if not results:
        return f"No ArXiv results found for: {query}"

    lines = []
    for i, paper in enumerate(results, 1):
        abstract = paper.summary.replace("\n", " ")[:500]
        doi = paper.doi or ""
        lines.append(
            f"[ArXiv {i}]\n"
            f"Title: {paper.title}\n"
            f"Abstract: {abstract}\n"
            f"Published: {paper.published.strftime('%Y-%m-%d')}\n"
            f"DOI: {doi}\n"
            f"URL: {paper.entry_id}\n"
        )
    return "\n".join(lines)
