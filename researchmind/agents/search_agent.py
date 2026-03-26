"""
search_agent.py — Search Agent

Job: Generate smart search queries → search arXiv + Semantic Scholar → pick best papers.
Writes found papers to ResearchMemory.
"""

import json
from researchmind.llm import call_gemini, call_gemini_json
from researchmind.memory import ResearchMemory
from researchmind.tools.search_tools import search_papers


class SearchAgent:
    """
    Autonomous agent that finds relevant academic papers.

    1. Uses Gemini to generate smart search queries from user topic
    2. Calls arXiv + Semantic Scholar APIs (tool use)
    3. Picks the most relevant papers
    4. Writes results to shared memory
    """

    def __init__(self, memory: ResearchMemory):
        self.memory = memory
        self.name = "SearchAgent"

    async def run(self) -> None:
        """Execute the search agent pipeline."""
        self.memory.log(self.name, f"Starting search for topic: '{self.memory.topic}'")

        # Step 1: Generate smart search queries using Gemini
        queries = await self._generate_queries()
        self.memory.log(self.name, f"Generated {len(queries)} search queries")

        # Step 2: Search for papers using each query
        all_papers = []
        for query in queries:
            self.memory.log(self.name, f"Searching: '{query}'")
            papers = await search_papers(query, max_per_source=5)
            all_papers.extend(papers)
            self.memory.log(self.name, f"Found {len(papers)} papers for this query")

        # Step 3: Deduplicate
        unique_papers = self._deduplicate(all_papers)
        self.memory.log(self.name, f"Total unique papers found: {len(unique_papers)}")

        # Step 4: Rank and select best papers
        selected = await self._rank_papers(unique_papers)
        self.memory.log(self.name, f"Selected top {len(selected)} most relevant papers")

        # Step 5: Write to memory
        for paper in selected:
            self.memory.add_paper(paper)

        self.memory.log(self.name, "✅ Search complete")

    async def _generate_queries(self) -> list[str]:
        """Use Gemini to generate multiple search queries for the topic."""
        prompt = f"""Given the research topic: "{self.memory.topic}"

Generate 3 different search queries that would help find the most relevant academic papers.
Each query should approach the topic from a slightly different angle.

Respond as a JSON array of strings. Example:
["query 1", "query 2", "query 3"]"""

        try:
            response = await call_gemini_json(prompt)
            # Clean response — remove markdown formatting if present
            response = response.strip()
            if response.startswith("```"):
                response = response.split("\n", 1)[-1].rsplit("```", 1)[0]
            queries = json.loads(response)
            if isinstance(queries, list) and len(queries) > 0:
                return queries[:3]
        except Exception as e:
            self.memory.log(self.name, f"Query generation fallback: {e}")

        # Fallback: use the topic directly
        return [self.memory.topic]

    async def _rank_papers(self, papers: list[dict]) -> list[dict]:
        """Use Gemini to rank papers by relevance. Select top papers."""
        if len(papers) <= 8:
            return papers

        # Build a compact list for Gemini to rank
        paper_list = ""
        for i, p in enumerate(papers):
            paper_list += f"{i}. {p['title']} ({p['year']}) - {p['abstract'][:150]}...\n"

        prompt = f"""Given the research topic: "{self.memory.topic}"

Here are {len(papers)} papers found. Select the 8 most relevant ones.
Return ONLY a JSON array of the paper indices (numbers).

Papers:
{paper_list}

Example response: [0, 2, 5, 7, 1, 3, 6, 4]"""

        try:
            response = await call_gemini_json(prompt)
            response = response.strip()
            if response.startswith("```"):
                response = response.split("\n", 1)[-1].rsplit("```", 1)[0]
            indices = json.loads(response)
            if isinstance(indices, list):
                selected = []
                for idx in indices[:8]:
                    if isinstance(idx, int) and 0 <= idx < len(papers):
                        selected.append(papers[idx])
                if selected:
                    return selected
        except Exception as e:
            self.memory.log(self.name, f"Ranking fallback: {e}")

        # Fallback: return first 8
        return papers[:8]

    def _deduplicate(self, papers: list[dict]) -> list[dict]:
        """Remove duplicate papers by title."""
        seen = set()
        unique = []
        for p in papers:
            title_lower = p["title"].lower().strip()
            if title_lower not in seen:
                seen.add(title_lower)
                unique.append(p)
        return unique
