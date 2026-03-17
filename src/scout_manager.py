"""Scout Manager — async orchestrator that runs the full pipeline."""

import asyncio
import traceback
from typing import AsyncGenerator

from agents import Runner, trace

from src.scout_agents.planner_agent import planner_agent, SearchPlan
from src.scout_agents.search_agent import search_agent, SearchResult
from src.scout_agents.synthesis_agent import synthesis_agent


async def _run_single_search(search_term: str, reasoning: str) -> SearchResult | None:
    """Run a single search agent for one sub-topic. Returns None on failure."""
    try:
        prompt = (
            f"Search for papers on: {search_term}\n"
            f"Context: {reasoning}"
        )
        result = await asyncio.wait_for(
            Runner.run(search_agent, input=prompt, max_turns=25),
            timeout=120,  # 2 min max per search
        )
        return result.final_output
    except asyncio.TimeoutError:
        print(f"[TIMEOUT] Search timed out for '{search_term}'")
        return None
    except Exception as e:
        print(f"[ERROR] Search failed for '{search_term}': {e}")
        traceback.print_exc()
        return None


async def run_pipeline(query: str) -> AsyncGenerator[str, None]:
    """Run the full literature scout pipeline, yielding status updates.

    Stages:
    1. Planner — decompose query into 5 sub-topics
    2. Search  — run 5 search agents in parallel
    3. Synthesize — produce a structured research brief
    """
    with trace("Literature Scout Pipeline"):

        # --- Stage 1: Planning ---
        yield "🔍 **Stage 1/3 — Planning search strategy...**"

        plan_result = await Runner.run(planner_agent, input=query)
        search_plan: SearchPlan = plan_result.final_output

        plan_summary = "\n".join(
            f"  {i}. {item.search_term}" for i, item in enumerate(search_plan.items, 1)
        )
        yield f"📋 **Search plan ready:**\n{plan_summary}"

        # --- Stage 2: Parallel search ---
        yield "🔎 **Stage 2/3 — Searching PubMed & ArXiv (5 parallel searches)...**"

        tasks = [
            asyncio.create_task(_run_single_search(item.search_term, item.reasoning))
            for item in search_plan.items
        ]

        all_results: list[SearchResult] = []
        for coro in asyncio.as_completed(tasks):
            result = await coro
            if result is not None:
                all_results.append(result)
                yield f"  ✅ Completed search: *{result.search_term}* — found {len(result.papers)} papers"
            else:
                yield "  ⚠️ One search failed — continuing with remaining results"

        total_papers = sum(len(r.papers) for r in all_results)
        yield f"📚 **All searches complete — {total_papers} papers found total**"

        if not all_results:
            yield "❌ **All searches failed. Please check API keys and try again.**"
            return

        # --- Stage 3: Synthesis ---
        yield "✍️ **Stage 3/3 — Synthesizing research brief...**"

        # Build context for synthesis agent
        context_parts = [f"# Original Research Query\n{query}\n"]
        for sr in all_results:
            context_parts.append(f"\n## Sub-topic: {sr.search_term}")
            for p in sr.papers:
                context_parts.append(
                    f"- **{p.title}** ({p.source}, relevance: {p.relevance_score}/10)\n"
                    f"  Abstract: {p.abstract[:300]}...\n"
                    f"  DOI: {p.doi} | URL: {p.url}"
                )

        synthesis_input = "\n".join(context_parts)
        synthesis_result = await Runner.run(synthesis_agent, input=synthesis_input)
        brief: str = synthesis_result.final_output

        yield "---\n"
        yield brief
