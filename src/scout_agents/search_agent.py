"""Search Agent — searches PubMed and ArXiv for a single sub-topic."""

from pydantic import BaseModel, Field
from agents import Agent

from src.tools.pubmed_tool import pubmed_search
from src.tools.arxiv_tool import arxiv_search


class PaperResult(BaseModel):
    title: str = Field(description="Paper title")
    abstract: str = Field(description="Paper abstract (truncated)")
    doi: str = Field(default="", description="DOI if available")
    url: str = Field(description="Link to the paper")
    source: str = Field(description="'PubMed' or 'ArXiv'")
    relevance_score: float = Field(
        description="Relevance to the search term on a scale of 1-10",
        ge=1.0,
        le=10.0,
    )


class SearchResult(BaseModel):
    search_term: str = Field(description="The search term that was used")
    papers: list[PaperResult] = Field(description="Top papers found for this search term")


SEARCH_INSTRUCTIONS = """\
You are a literature search specialist for bioinformatics and ML research.

Your task:
1. Call pubmed_search ONCE with the provided search term.
2. Call arxiv_search ONCE with the provided search term.
3. From the combined results, select the top papers (up to 3 from each source).
4. Rate each paper's relevance to the search term on a scale of 1-10.
5. Return your structured output immediately — do NOT run additional searches.

IMPORTANT: Only call each tool ONCE. Do not retry or refine searches. \
After getting results from both tools, immediately return your final output.
"""

search_agent = Agent(
    name="Searcher",
    instructions=SEARCH_INSTRUCTIONS,
    model="gpt-4o-mini",
    tools=[pubmed_search, arxiv_search],
    output_type=SearchResult,
)
