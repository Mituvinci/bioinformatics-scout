"""Planner Agent — decomposes a research query into 5 targeted sub-topic searches."""

from pydantic import BaseModel, Field
from agents import Agent


class SearchItem(BaseModel):
    search_term: str = Field(description="A precise search query for PubMed/ArXiv")
    reasoning: str = Field(description="Why this sub-topic is important for the overall query")


class SearchPlan(BaseModel):
    items: list[SearchItem] = Field(
        description="Exactly 5 targeted search items covering different aspects of the query",
        min_length=5,
        max_length=5,
    )


PLANNER_INSTRUCTIONS = """\
You are a bioinformatics research strategist. Given a research query, decompose it into \
exactly 5 targeted sub-topic searches that together provide comprehensive coverage.

Guidelines:
- Each search term should be specific enough to return relevant papers from PubMed or ArXiv.
- Cover different facets: methods, applications, datasets, benchmarks, and recent advances.
- Include relevant domain keywords (e.g., gene names, model architectures, data modalities).
- Avoid overly broad or duplicate searches.
- Provide a brief reasoning for each sub-topic explaining what aspect it covers.
"""

planner_agent = Agent(
    name="Planner",
    instructions=PLANNER_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=SearchPlan,
)
