"""
report_agent.py — Report Agent

Job: Compile everything → save as JSON and Markdown.
Final agent in the pipeline.
"""

import json
import os
from datetime import datetime
from researchmind.llm import call_gemini
from researchmind.memory import ResearchMemory


class ReportAgent:
    """
    Autonomous agent that compiles the final research report.

    1. Reads all data from shared memory
    2. Uses Gemini to write a polished introduction and conclusion
    3. Saves as structured JSON (research_output.json)
    4. Saves as formatted Markdown (research_report.md)
    """

    def __init__(self, memory: ResearchMemory, output_dir: str = "output"):
        self.memory = memory
        self.name = "ReportAgent"
        self.output_dir = output_dir

    async def run(self) -> None:
        """Execute the report compilation pipeline."""
        self.memory.log(self.name, "Compiling final research report...")

        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

        # Step 1: Generate introduction and conclusion
        intro = await self._generate_introduction()
        conclusion = await self._generate_conclusion()

        # Step 2: Build the full report
        report = self._build_report(intro, conclusion)
        self.memory.set_report(report)

        # Step 3: Save as JSON
        json_path = os.path.join(self.output_dir, "research_output.json")
        self._save_json(json_path)
        self.memory.log(self.name, f"Saved JSON: {json_path}")

        # Step 4: Save as Markdown
        md_path = os.path.join(self.output_dir, "research_report.md")
        self._save_markdown(md_path, intro, conclusion)
        self.memory.log(self.name, f"Saved Markdown: {md_path}")

        self.memory.log(self.name, "✅ Report compilation complete")

    async def _generate_introduction(self) -> str:
        """Use Gemini to write a polished introduction."""
        papers_count = len(self.memory.get_papers())

        prompt = f"""Write a professional introduction for a research literature review report on the topic:
"{self.memory.topic}"

This report covers {papers_count} academic papers from arXiv and Semantic Scholar.

The introduction should:
1. Explain why this topic is important
2. Briefly describe what the report covers
3. Mention the methodology (automated AI-powered literature review)
4. Be 150-200 words
5. Sound professional and academic"""

        try:
            return await call_gemini(prompt, temperature=0.6)
        except Exception:
            return f"This report presents a comprehensive literature review on **{self.memory.topic}**, covering {papers_count} recent academic papers."

    async def _generate_conclusion(self) -> str:
        """Use Gemini to write a conclusion based on synthesis and opportunities."""
        synthesis = self.memory.get_synthesis()
        opportunities = self.memory.get_opportunities()

        synthesis_text = synthesis.get("final_synthesis", "")[:500] if synthesis else ""
        opp_text = opportunities.get("opportunities_text", "")[:500] if opportunities else ""

        prompt = f"""Write a professional conclusion for a research literature review on:
"{self.memory.topic}"

Key synthesis findings:
{synthesis_text}

Research opportunities identified:
{opp_text}

The conclusion should:
1. Summarize the key findings across all papers
2. Highlight the most important research gaps
3. Suggest the most promising future directions
4. Be 150-200 words
5. End with a strong closing statement"""

        try:
            return await call_gemini(prompt, temperature=0.6)
        except Exception:
            return "This literature review has identified key themes, research gaps, and opportunities for future investigation."

    def _build_report(self, intro: str, conclusion: str) -> dict:
        """Build the structured report dictionary."""
        return {
            "title": f"Literature Review: {self.memory.topic}",
            "generated_at": datetime.now().isoformat(),
            "topic": self.memory.topic,
            "introduction": intro,
            "papers_reviewed": len(self.memory.get_papers()),
            "papers": self.memory.get_papers(),
            "analyses": self.memory.get_analyses(),
            "summaries": [
                {
                    "title": s["paper_title"],
                    "authors": s.get("paper_authors", []),
                    "year": s.get("paper_year", ""),
                    "summary": s.get("summary_text", ""),
                    "relevance_score": s.get("relevance_score", 0),
                }
                for s in self.memory.get_summaries()
            ],
            "synthesis": self.memory.get_synthesis(),
            "research_opportunities": self.memory.get_opportunities(),
            "conclusion": conclusion,
        }

    def _save_json(self, path: str) -> None:
        """Save the full research data as JSON."""
        data = self.memory.to_dict()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _save_markdown(self, path: str, intro: str, conclusion: str) -> None:
        """Save a formatted Markdown report."""
        report = self.memory.get_report()
        summaries = self.memory.get_summaries()
        synthesis = self.memory.get_synthesis()
        opportunities = self.memory.get_opportunities()

        md = f"""# 📚 Literature Review: {self.memory.topic}

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Papers Reviewed:** {len(self.memory.get_papers())}
**Powered by:** ResearchMind — Agentic AI System

---

## 1. Introduction

{intro}

---

## 2. Paper Summaries

"""
        for i, s in enumerate(summaries):
            md += f"""### Paper {i + 1}: {s['paper_title']}
**Authors:** {', '.join(s.get('paper_authors', ['Unknown']))}
**Year:** {s.get('paper_year', 'N/A')} | **Relevance:** {s.get('relevance_score', 'N/A')}/10
**Source:** {s.get('paper_url', 'N/A')}

{s.get('summary_text', 'No summary available')}

---

"""

        # Synthesis section
        md += "## 3. Cross-Paper Synthesis\n\n"
        if synthesis:
            md += synthesis.get("final_synthesis", synthesis.get("initial_synthesis", "No synthesis available"))
            md += "\n\n"

            # Self-reflection note
            if synthesis.get("self_reflection_applied"):
                md += "> **🔄 Self-Reflection Applied:** The synthesis agent reviewed and improved its own analysis.\n\n"
                md += "<details>\n<summary>View Self-Reflection</summary>\n\n"
                md += synthesis.get("self_reflection", "")
                md += "\n\n</details>\n\n"
        else:
            md += "No synthesis available.\n\n"

        md += "---\n\n"

        # Opportunities section
        md += "## 4. Research Gaps & Future Directions\n\n"
        if opportunities:
            md += opportunities.get("opportunities_text", "No opportunities identified")
        else:
            md += "No opportunities identified.\n"

        md += "\n\n---\n\n"

        # Conclusion
        md += f"""## 5. Conclusion

{conclusion}

---

## 6. References

"""
        for i, p in enumerate(self.memory.get_papers()):
            authors = ", ".join(p.get("authors", ["Unknown"]))
            md += f"{i + 1}. {authors} ({p.get('year', 'N/A')}). *{p['title']}*. [{p.get('source', 'Source')}]({p.get('url', '#')})\n"

        md += f"""
---

*This report was automatically generated by ResearchMind, an Agentic AI system.*
*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

        with open(path, "w", encoding="utf-8") as f:
            f.write(md)
