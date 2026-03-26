"""
opportunity_agent.py — Opportunity Agent

Job: Identify research gaps, future directions, and potential experiments.
"""

from researchmind.llm import call_gemini
from researchmind.memory import ResearchMemory


class OpportunityAgent:
    """
    Autonomous agent that identifies research opportunities.

    1. Reads synthesis and analyses from shared memory
    2. Identifies gaps in the current research landscape
    3. Suggests future research directions
    4. Proposes potential experiments or studies
    5. Writes opportunities to shared memory
    """

    def __init__(self, memory: ResearchMemory):
        self.memory = memory
        self.name = "OpportunityAgent"

    async def run(self) -> None:
        """Execute the opportunity identification pipeline."""
        synthesis = self.memory.get_synthesis()
        analyses = self.memory.get_analyses()

        self.memory.log(self.name, "Identifying research gaps and opportunities...")

        if not synthesis and not analyses:
            self.memory.log(self.name, "⚠ No synthesis or analyses available")
            return

        # Build context
        synthesis_text = synthesis.get("final_synthesis", synthesis.get("initial_synthesis", ""))
        analysis_text = ""
        for a in analyses:
            analysis_text += f"\n- {a['paper_title']}: {a.get('full_analysis', '')[:200]}\n"

        prompt = f"""Based on the research synthesis and individual paper analyses about "{self.memory.topic}":

--- SYNTHESIS ---
{synthesis_text}
--- END SYNTHESIS ---

--- INDIVIDUAL ANALYSES (excerpts) ---
{analysis_text}
--- END ANALYSES ---

As a research strategist, identify:

1. **RESEARCH GAPS** (3-5 specific gaps):
   - What questions remain unanswered?
   - What areas have been underexplored?
   - What assumptions have not been tested?

2. **FUTURE DIRECTIONS** (3-5 directions):
   - Where should research head next?
   - What emerging trends could be explored?
   - What interdisciplinary connections could be made?

3. **PROPOSED EXPERIMENTS/STUDIES** (2-3 proposals):
   - Describe a specific study that could address a gap
   - What data would be needed?
   - What methodology would you suggest?

4. **HIGH-IMPACT OPPORTUNITIES**:
   - Which gap, if addressed, would have the most impact?
   - Why is this the most impactful opportunity?

Be specific and actionable — a researcher should be able to read this and start working on these ideas."""

        system_instruction = (
            "You are a research strategist with deep expertise. "
            "Identify concrete, actionable research opportunities. "
            "Be specific — vague suggestions are useless. "
            "Think about what would actually advance the field."
        )

        try:
            response = await call_gemini(prompt, system_instruction=system_instruction, temperature=0.6)

            opportunities = {
                "topic": self.memory.topic,
                "opportunities_text": response,
                "based_on_papers": len(analyses),
            }

            self.memory.set_opportunities(opportunities)
            self.memory.log(self.name, "✅ Research opportunities identified")

        except Exception as e:
            self.memory.log(self.name, f"⚠ Error identifying opportunities: {e}")
            self.memory.set_opportunities({
                "topic": self.memory.topic,
                "opportunities_text": f"[Error: {e}]",
                "based_on_papers": 0,
            })
