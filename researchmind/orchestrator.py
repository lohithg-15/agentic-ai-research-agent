"""
orchestrator.py — Pipeline Orchestrator

Runs all 6 agents in sequence: Search → Analysis → Summary → Synthesis → Opportunity → Report.
Creates ResearchMemory and passes it through the pipeline.
"""

import time
import asyncio
from typing import Callable, Optional
from researchmind.memory import ResearchMemory
from researchmind.agents.search_agent import SearchAgent
from researchmind.agents.analysis_agent import AnalysisAgent
from researchmind.agents.summary_agent import SummaryAgent
from researchmind.agents.synthesis_agent import SynthesisAgent
from researchmind.agents.opportunity_agent import OpportunityAgent
from researchmind.agents.report_agent import ReportAgent


# Agent labels used by both the orchestrator and the API progress tracker
AGENT_LABELS = [
    "Search Agent",
    "Analysis Agent",
    "Summary Agent",
    "Synthesis Agent",
    "Opportunity Agent",
    "Report Agent",
]


class ResearchOrchestrator:
    """
    Orchestrates the 6-agent pipeline.

    Pipeline: Search → Analysis → Summary → Synthesis → Opportunity → Report

    Each agent reads from and writes to the shared ResearchMemory.
    Accepts an optional progress_callback(step, label, status, detail) that
    the API uses to push live updates to the frontend.
    """

    def __init__(
        self,
        topic: str,
        output_dir: str = "output",
        progress_callback: Optional[Callable] = None,
    ):
        self.topic = topic
        self.output_dir = output_dir
        self.memory = ResearchMemory(topic)
        self._progress = progress_callback or (lambda *a, **kw: None)

    async def run(self) -> ResearchMemory:
        """Execute the full research pipeline."""
        start_time = time.time()

        print("=" * 60)
        print(f"ResearchMind — Agentic AI Literature Review")
        print(f"Topic: {self.topic}")
        print("=" * 60)

        # Define the agent pipeline
        pipeline = [
            (AGENT_LABELS[0], SearchAgent(self.memory)),
            (AGENT_LABELS[1], AnalysisAgent(self.memory)),
            (AGENT_LABELS[2], SummaryAgent(self.memory)),
            (AGENT_LABELS[3], SynthesisAgent(self.memory)),
            (AGENT_LABELS[4], OpportunityAgent(self.memory)),
            (AGENT_LABELS[5], ReportAgent(self.memory, self.output_dir)),
        ]

        # Execute each agent in sequence
        for i, (label, agent) in enumerate(pipeline, 1):
            agent_start = time.time()
            print(f"\n{'_' * 50}")
            print(f"  Step {i}/6: {label}")
            print(f"{'_' * 50}")

            self._progress(step=i, label=label, status="running", detail=f"Running {label}...")

            try:
                await agent.run()
                agent_time = time.time() - agent_start
                print(f"  {label} completed in {agent_time:.1f}s")
                self._progress(step=i, label=label, status="done", detail=f"Completed in {agent_time:.1f}s")
            except Exception as e:
                agent_time = time.time() - agent_start
                print(f"\n  {label} failed after {agent_time:.1f}s: {e}")
                self.memory.log("Orchestrator", f"Agent failed: {label} -- {e}")
                self._progress(step=i, label=label, status="error", detail=str(e))
                # Can't continue without search results or analyses
                if i <= 2:
                    print("  Cannot continue -- this agent is required for downstream steps.")
                    break

        # Final summary
        total_time = time.time() - start_time
        print(f"\n{'=' * 60}")
        print(f"Research complete!")
        print(f"Papers found: {len(self.memory.get_papers())}")
        print(f"Analyses: {len(self.memory.get_analyses())}")
        print(f"Summaries: {len(self.memory.get_summaries())}")
        print(f"Total time: {total_time:.1f} seconds")
        print(f"Output saved to: {self.output_dir}/")
        print(f"{'=' * 60}")

        return self.memory


async def run_research(
    topic: str,
    output_dir: str = "output",
    progress_callback: Optional[Callable] = None,
) -> ResearchMemory:
    """Convenience function to run the full pipeline."""
    orchestrator = ResearchOrchestrator(topic, output_dir, progress_callback)
    return await orchestrator.run()
