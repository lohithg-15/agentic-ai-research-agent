"""
memory.py — ResearchMemory: Shared Memory Store

This is the "common whiteboard" all 6 agents read from and write to.
No database needed — just a Python class holding structured data.
"""

import json
from datetime import datetime
from typing import Any


class ResearchMemory:
    """
    Shared memory connecting all agents.

    Stores papers, analyses, summaries, synthesis, opportunities, and the final report.
    Each agent reads what it needs and writes its output back here.
    """

    def __init__(self, topic: str):
        self.topic = topic
        self.created_at = datetime.now().isoformat()

        # Data stores — each agent fills one section
        self.papers: list[dict[str, Any]] = []          # SearchAgent writes
        self.analyses: list[dict[str, Any]] = []        # AnalysisAgent writes
        self.summaries: list[dict[str, Any]] = []       # SummaryAgent writes
        self.synthesis: dict[str, Any] = {}             # SynthesisAgent writes
        self.opportunities: dict[str, Any] = {}         # OpportunityAgent writes
        self.report: dict[str, Any] = {}                # ReportAgent writes

        # Metadata
        self.agent_logs: list[str] = []

    # ── Paper Management ──────────────────────────────────────

    def add_paper(self, paper: dict[str, Any]) -> None:
        """Add a paper found by the Search Agent."""
        paper["added_at"] = datetime.now().isoformat()
        self.papers.append(paper)

    def get_papers(self) -> list[dict[str, Any]]:
        """Get all papers."""
        return self.papers

    # ── Analysis Management ───────────────────────────────────

    def add_analysis(self, analysis: dict[str, Any]) -> None:
        """Add an analysis produced by the Analysis Agent."""
        analysis["analyzed_at"] = datetime.now().isoformat()
        self.analyses.append(analysis)

    def get_analyses(self) -> list[dict[str, Any]]:
        """Get all analyses."""
        return self.analyses

    # ── Summary Management ────────────────────────────────────

    def add_summary(self, summary: dict[str, Any]) -> None:
        """Add a summary produced by the Summary Agent."""
        summary["summarized_at"] = datetime.now().isoformat()
        self.summaries.append(summary)

    def get_summaries(self) -> list[dict[str, Any]]:
        """Get all summaries."""
        return self.summaries

    # ── Synthesis ─────────────────────────────────────────────

    def set_synthesis(self, synthesis: dict[str, Any]) -> None:
        """Set the synthesis output (themes, trends, contradictions)."""
        synthesis["synthesized_at"] = datetime.now().isoformat()
        self.synthesis = synthesis

    def get_synthesis(self) -> dict[str, Any]:
        """Get synthesis."""
        return self.synthesis

    # ── Opportunities ─────────────────────────────────────────

    def set_opportunities(self, opportunities: dict[str, Any]) -> None:
        """Set the research opportunities/gaps."""
        opportunities["identified_at"] = datetime.now().isoformat()
        self.opportunities = opportunities

    def get_opportunities(self) -> dict[str, Any]:
        """Get opportunities."""
        return self.opportunities

    # ── Report ────────────────────────────────────────────────

    def set_report(self, report: dict[str, Any]) -> None:
        """Set the final compiled report."""
        self.report = report

    def get_report(self) -> dict[str, Any]:
        """Get the final report."""
        return self.report

    # ── Logging ───────────────────────────────────────────────

    def log(self, agent_name: str, message: str) -> None:
        """Log an action by an agent."""
        entry = f"[{datetime.now().strftime('%H:%M:%S')}] {agent_name}: {message}"
        self.agent_logs.append(entry)
        print(f"  📝 {entry}")

    # ── Export ────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """Export entire memory as a dictionary."""
        return {
            "topic": self.topic,
            "created_at": self.created_at,
            "papers_found": len(self.papers),
            "papers": self.papers,
            "analyses": self.analyses,
            "summaries": self.summaries,
            "synthesis": self.synthesis,
            "opportunities": self.opportunities,
            "report": self.report,
            "agent_logs": self.agent_logs,
        }

    def to_json(self, indent: int = 2) -> str:
        """Export entire memory as JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def __repr__(self) -> str:
        return (
            f"ResearchMemory(topic='{self.topic}', "
            f"papers={len(self.papers)}, "
            f"analyses={len(self.analyses)}, "
            f"summaries={len(self.summaries)})"
        )
