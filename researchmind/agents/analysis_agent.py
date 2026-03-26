"""
analysis_agent.py — Analysis Agent

Job: Read each paper → send to Gemini → extract problem, method, results, score.
Uses asyncio to analyze multiple papers in parallel.
"""

import asyncio
import json
from researchmind.llm import call_gemini
from researchmind.memory import ResearchMemory


class AnalysisAgent:
    """
    Autonomous agent that deeply analyzes each paper.

    1. Reads papers from shared memory
    2. Sends each paper to Gemini for analysis
    3. Extracts: problem statement, methodology, key results, relevance score
    4. Runs analysis in parallel (asyncio) for speed
    5. Writes analyses back to shared memory
    """

    def __init__(self, memory: ResearchMemory):
        self.memory = memory
        self.name = "AnalysisAgent"

    async def run(self) -> None:
        """Execute the analysis agent pipeline."""
        papers = self.memory.get_papers()
        self.memory.log(self.name, f"Starting analysis of {len(papers)} papers")

        if not papers:
            self.memory.log(self.name, "⚠ No papers to analyze")
            return

        # Analyze all papers in parallel using asyncio
        tasks = [self._analyze_paper(paper, i) for i, paper in enumerate(papers)]
        analyses = await asyncio.gather(*tasks, return_exceptions=True)

        # Write successful analyses to memory
        success_count = 0
        for result in analyses:
            if isinstance(result, dict):
                self.memory.add_analysis(result)
                success_count += 1
            elif isinstance(result, Exception):
                self.memory.log(self.name, f"⚠ Analysis failed: {result}")

        self.memory.log(self.name, f"✅ Analysis complete: {success_count}/{len(papers)} papers analyzed")

    async def _analyze_paper(self, paper: dict, index: int) -> dict:
        """Analyze a single paper using Gemini."""
        self.memory.log(self.name, f"Analyzing paper {index + 1}: {paper['title'][:60]}...")

        prompt = f"""Analyze this academic paper in detail:

Title: {paper['title']}
Authors: {', '.join(paper.get('authors', ['Unknown']))}
Year: {paper.get('year', 'Unknown')}
Abstract: {paper.get('abstract', 'No abstract available')}

Provide a thorough analysis in this exact format:

PROBLEM STATEMENT: [What problem does this paper address?]

METHODOLOGY: [What approach/method do the authors use?]

KEY RESULTS: [What are the main findings and contributions?]

STRENGTHS: [What are the paper's strengths?]

LIMITATIONS: [What are the paper's limitations?]

RELEVANCE SCORE: [Rate 1-10 how relevant this is to the topic "{self.memory.topic}"]

KEY TAKEAWAY: [One sentence summarizing the most important contribution]"""

        system_instruction = (
            "You are an expert academic researcher. Analyze papers thoroughly and objectively. "
            "Be specific about methods and results. If information is limited (only abstract available), "
            "acknowledge this but still provide the best analysis you can."
        )

        try:
            response = await call_gemini(prompt, system_instruction=system_instruction, temperature=0.3)

            # Parse the response into structured data
            analysis = {
                "paper_title": paper["title"],
                "paper_authors": paper.get("authors", []),
                "paper_year": paper.get("year", "Unknown"),
                "paper_url": paper.get("url", ""),
                "paper_source": paper.get("source", ""),
                "full_analysis": response,
                "paper_index": index,
            }

            # Try to extract relevance score
            try:
                for line in response.split("\n"):
                    if "RELEVANCE SCORE" in line.upper():
                        # Extract number from line
                        import re
                        numbers = re.findall(r'\d+', line)
                        if numbers:
                            analysis["relevance_score"] = min(int(numbers[0]), 10)
                            break
            except Exception:
                analysis["relevance_score"] = 5

            return analysis

        except Exception as e:
            self.memory.log(self.name, f"⚠ Error analyzing '{paper['title'][:40]}': {e}")
            # Return a basic analysis on error
            return {
                "paper_title": paper["title"],
                "paper_authors": paper.get("authors", []),
                "paper_year": paper.get("year", "Unknown"),
                "paper_url": paper.get("url", ""),
                "paper_source": paper.get("source", ""),
                "full_analysis": f"[Analysis failed: {e}]",
                "relevance_score": 0,
                "paper_index": index,
            }
