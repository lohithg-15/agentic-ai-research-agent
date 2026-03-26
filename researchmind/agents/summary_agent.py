"""
summary_agent.py — Summary Agent

Job: Read analyses from memory → generate clean human-readable summary per paper.
"""

import asyncio
from researchmind.llm import call_gemini
from researchmind.memory import ResearchMemory


class SummaryAgent:
    """
    Autonomous agent that writes clean summaries.

    1. Reads analyses from shared memory
    2. For each analysis, generates a human-readable summary
    3. Summaries are clear, structured, and include key takeaways
    4. Writes summaries back to shared memory
    """

    def __init__(self, memory: ResearchMemory):
        self.memory = memory
        self.name = "SummaryAgent"

    async def run(self) -> None:
        """Execute the summary agent pipeline."""
        analyses = self.memory.get_analyses()
        self.memory.log(self.name, f"Starting summarization of {len(analyses)} analyses")

        if not analyses:
            self.memory.log(self.name, "⚠ No analyses to summarize")
            return

        # Summarize all in parallel
        tasks = [self._summarize(analysis, i) for i, analysis in enumerate(analyses)]
        summaries = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = 0
        for result in summaries:
            if isinstance(result, dict):
                self.memory.add_summary(result)
                success_count += 1
            elif isinstance(result, Exception):
                self.memory.log(self.name, f"⚠ Summary failed: {result}")

        self.memory.log(self.name, f"✅ Summarization complete: {success_count}/{len(analyses)} papers summarized")

    async def _summarize(self, analysis: dict, index: int) -> dict:
        """Generate a human-readable summary for one paper analysis."""
        self.memory.log(self.name, f"Summarizing paper {index + 1}: {analysis['paper_title'][:60]}...")

        prompt = f"""Based on this academic paper analysis, write a clear, human-readable summary.

Paper Title: {analysis['paper_title']}
Authors: {', '.join(analysis.get('paper_authors', ['Unknown']))}
Year: {analysis.get('paper_year', 'Unknown')}

Full Analysis:
{analysis.get('full_analysis', 'No analysis available')}

Write a summary that includes:
1. **What this paper is about** (1-2 sentences)
2. **Key methodology** (how they approached the problem)
3. **Main findings** (what they discovered)
4. **Why it matters** (significance and implications)
5. **Key takeaway** (one sentence a reader should remember)

Keep the summary concise but informative (150-250 words).
Use clear, accessible language — avoid unnecessary jargon."""

        system_instruction = (
            "You are a skilled academic writer. Write clear, well-structured summaries "
            "that make complex research accessible. Use bullet points where helpful."
        )

        try:
            response = await call_gemini(prompt, system_instruction=system_instruction, temperature=0.5)

            return {
                "paper_title": analysis["paper_title"],
                "paper_authors": analysis.get("paper_authors", []),
                "paper_year": analysis.get("paper_year", "Unknown"),
                "paper_url": analysis.get("paper_url", ""),
                "relevance_score": analysis.get("relevance_score", 5),
                "summary_text": response,
                "paper_index": analysis.get("paper_index", index),
            }

        except Exception as e:
            self.memory.log(self.name, f"⚠ Error summarizing '{analysis['paper_title'][:40]}': {e}")
            return {
                "paper_title": analysis["paper_title"],
                "paper_authors": analysis.get("paper_authors", []),
                "paper_year": analysis.get("paper_year", "Unknown"),
                "paper_url": analysis.get("paper_url", ""),
                "relevance_score": analysis.get("relevance_score", 5),
                "summary_text": f"[Summary unavailable: {e}]",
                "paper_index": analysis.get("paper_index", index),
            }
