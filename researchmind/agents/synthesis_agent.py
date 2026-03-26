"""
synthesis_agent.py — Synthesis Agent (with Self-Reflection)

Job: Read all summaries → find themes, contradictions, trends.
MOST ADVANCED FEATURE: Self-reflects on its own output and improves it.
"""

from researchmind.llm import call_gemini
from researchmind.memory import ResearchMemory


class SynthesisAgent:
    """
    Autonomous agent that synthesizes across all papers.

    This is the most advanced agent — it implements SELF-REFLECTION:
    1. Reads all summaries from shared memory
    2. Identifies common themes, contradictions, and trends
    3. Reviews its OWN output → finds weaknesses
    4. Improves the synthesis based on self-critique
    5. Writes final synthesis to shared memory
    """

    def __init__(self, memory: ResearchMemory):
        self.memory = memory
        self.name = "SynthesisAgent"

    async def run(self) -> None:
        """Execute the synthesis agent pipeline with self-reflection."""
        summaries = self.memory.get_summaries()
        self.memory.log(self.name, f"Starting synthesis of {len(summaries)} summaries")

        if not summaries:
            self.memory.log(self.name, "⚠ No summaries to synthesize")
            return

        # Step 1: Initial synthesis
        self.memory.log(self.name, "Phase 1: Generating initial synthesis...")
        initial_synthesis = await self._generate_synthesis(summaries)

        # Step 2: Self-reflection — review own output
        self.memory.log(self.name, "Phase 2: Self-reflecting on synthesis quality...")
        reflection = await self._self_reflect(initial_synthesis, summaries)

        # Step 3: Improve based on reflection
        self.memory.log(self.name, "Phase 3: Improving synthesis based on self-critique...")
        improved_synthesis = await self._improve_synthesis(initial_synthesis, reflection, summaries)

        # Store the synthesis with reflection metadata
        synthesis_data = {
            "topic": self.memory.topic,
            "initial_synthesis": initial_synthesis,
            "self_reflection": reflection,
            "final_synthesis": improved_synthesis,
            "papers_synthesized": len(summaries),
            "self_reflection_applied": True,
        }

        self.memory.set_synthesis(synthesis_data)
        self.memory.log(self.name, "✅ Synthesis complete (with self-reflection)")

    async def _generate_synthesis(self, summaries: list[dict]) -> str:
        """Generate initial cross-paper synthesis."""
        # Build context from all summaries
        summary_text = ""
        for i, s in enumerate(summaries):
            summary_text += f"\n--- Paper {i + 1}: {s['paper_title']} ({s.get('paper_year', 'N/A')}) ---\n"
            summary_text += f"{s.get('summary_text', 'No summary')}\n"

        prompt = f"""You are analyzing research on the topic: "{self.memory.topic}"

Here are summaries of {len(summaries)} academic papers:
{summary_text}

Write a comprehensive synthesis that covers:

1. **COMMON THEMES**: What ideas, methods, or findings appear across multiple papers?
2. **KEY TRENDS**: How has research in this area evolved? What direction is it heading?
3. **CONTRADICTIONS**: Do any papers disagree or present conflicting results?
4. **METHODOLOGICAL PATTERNS**: What approaches dominate? Are there underexplored methods?
5. **CONSENSUS FINDINGS**: What do most papers agree on?
6. **OVERALL NARRATIVE**: What story do these papers tell together about the state of this field?

Be specific — reference individual papers by name when making claims.
Aim for thoroughness and depth (400-600 words)."""

        system_instruction = (
            "You are a senior academic researcher writing a literature review synthesis. "
            "Be analytical, identify patterns, and connect ideas across papers. "
            "Always cite specific papers when making claims."
        )

        return await call_gemini(prompt, system_instruction=system_instruction, temperature=0.5)

    async def _self_reflect(self, synthesis: str, summaries: list[dict]) -> str:
        """
        Self-reflection: The agent critiques its own synthesis.
        This is the CORE AGENTIC BEHAVIOUR — the agent evaluates itself.
        """
        prompt = f"""You just wrote this synthesis about "{self.memory.topic}":

--- YOUR SYNTHESIS ---
{synthesis}
--- END SYNTHESIS ---

Now critique your own work. Be honest and thorough:

1. **GAPS**: What important aspects of the papers did you miss or underemphasize?
2. **ACCURACY**: Did you misrepresent any paper's findings or draw unsupported conclusions?
3. **CONNECTIONS**: Are there cross-paper connections you failed to identify?
4. **BALANCE**: Is the synthesis balanced or does it overweight certain papers?
5. **DEPTH**: Where could the analysis be deeper or more nuanced?
6. **CLARITY**: Is the writing clear and well-organized?

Score your synthesis from 1-10 and explain why.
List specific improvements you would make."""

        system_instruction = (
            "You are a critical academic reviewer. Be brutally honest about weaknesses. "
            "Your job is to find flaws and suggest concrete improvements. "
            "Do not be generous — hold yourself to the highest standard."
        )

        return await call_gemini(prompt, system_instruction=system_instruction, temperature=0.4)

    async def _improve_synthesis(self, original: str, reflection: str, summaries: list[dict]) -> str:
        """Improve the synthesis based on self-reflection."""
        summary_text = ""
        for i, s in enumerate(summaries):
            summary_text += f"\n--- Paper {i + 1}: {s['paper_title']} ---\n"
            summary_text += f"{s.get('summary_text', 'No summary')[:300]}\n"

        prompt = f"""You previously wrote a synthesis about "{self.memory.topic}" and then critiqued your own work.

--- ORIGINAL SYNTHESIS ---
{original}
--- END ORIGINAL ---

--- YOUR SELF-CRITIQUE ---
{reflection}
--- END CRITIQUE ---

--- PAPER SUMMARIES FOR REFERENCE ---
{summary_text}
--- END PAPERS ---

Now write an IMPROVED synthesis that addresses all the weaknesses you identified.
Make it more thorough, accurate, balanced, and insightful.
This is your final version — make it excellent.

Structure:
1. **Common Themes & Patterns**
2. **Evolution & Trends**
3. **Points of Agreement & Disagreement**
4. **Methodological Landscape**
5. **State of the Field**

Target 500-700 words. Reference specific papers."""

        system_instruction = (
            "You are a senior researcher writing the definitive synthesis. "
            "This is the improved version after self-reflection — make it significantly better. "
            "Be thorough, nuanced, and well-organized."
        )

        return await call_gemini(prompt, system_instruction=system_instruction, temperature=0.5)
