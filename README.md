# ResearchMind — Agentic AI for Automated Literature Review

> **What takes a researcher 2-4 weeks, ResearchMind does in under 2 minutes.**

ResearchMind is a **full-stack Agentic AI system** that automates the complete academic literature review process. It features a **beautiful web frontend** connected to a **FastAPI backend** running a **6-agent AI pipeline** powered by Google Gemini, arXiv, and Semantic Scholar.

Type a topic → AI searches real papers → reads, analyses, summarises, synthesises → finds research gaps → writes a full report. All automatically, with **live progress tracking** in the browser.

---

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                     ResearchMind System                        │
│                                                                │
│   ┌───────────────────────────────────────────────────────┐   │
│   │              Frontend (HTML/CSS/JS)                    │   │
│   │  Search Input → Progress Pipeline → Report Viewer     │   │
│   └──────────────────────┬────────────────────────────────┘   │
│                          │ REST API                            │
│   ┌──────────────────────▼────────────────────────────────┐   │
│   │              Backend (FastAPI + Python)                │   │
│   │                                                        │   │
│   │  ┌──────────┐   ┌──────────┐   ┌──────────┐          │   │
│   │  │  Search   │──▶│ Analysis │──▶│ Summary  │          │   │
│   │  │  Agent    │   │  Agent   │   │  Agent   │          │   │
│   │  └──────────┘   └──────────┘   └──────────┘          │   │
│   │       │              │              │                  │   │
│   │       ▼              ▼              ▼                  │   │
│   │  ┌─────────────────────────────────────────────┐      │   │
│   │  │         ResearchMemory (Shared Store)        │      │   │
│   │  └─────────────────────────────────────────────┘      │   │
│   │       │              │              │                  │   │
│   │       ▼              ▼              ▼                  │   │
│   │  ┌──────────┐   ┌──────────┐   ┌──────────┐          │   │
│   │  │Synthesis │──▶│Opportunity│──▶│  Report  │          │   │
│   │  │  Agent   │   │  Agent   │   │  Agent   │          │   │
│   │  │(+Reflect)│   │          │   │          │          │   │
│   │  └──────────┘   └──────────┘   └──────────┘          │   │
│   └───────────────────────────────────────────────────────┘   │
│            │                              │                    │
│       ┌────┴────┐                    ┌────┴────┐              │
│       │  arXiv  │                    │ Gemini  │              │
│       │Semantic │                    │  API    │              │
│       │Scholar  │                    │ (Free)  │              │
│       └─────────┘                    └─────────┘              │
└────────────────────────────────────────────────────────────────┘
```

---

## The 6 Agents

| Agent | Job |
|---|---|
| **Search Agent** | Generates smart queries → searches arXiv & Semantic Scholar → picks best papers |
| **Analysis Agent** | Reads each paper → extracts problem, method, results, scores (async parallel) |
| **Summary Agent** | Writes clean human-readable summary per paper |
| **Synthesis Agent** | Finds themes across all papers → **self-reflects** on own output → improves |
| **Opportunity Agent** | Identifies research gaps, future directions, experiments |
| **Report Agent** | Compiles everything → saves JSON and Markdown report |

---

## Key Agentic Properties

| Property | How It Works |
|---|---|
| **Autonomous Agents** | 6 separate Python classes, each runs independently |
| **Tool Use** | Agents use arXiv API, Semantic Scholar API, file writer, Gemini API |
| **Shared Memory** | `ResearchMemory` — a common store all agents read and write |
| **Self-Reflection** | Synthesis Agent critiques and improves its own output |
| **RAG Pipeline** | Retrieves real papers first → AI reasons on actual data |

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Your Gemini API Key

Get a free key from [Google AI Studio](https://aistudio.google.com/app/apikey).

```bash
# Create a .env file (see .env.example)
GEMINI_API_KEY=your_actual_api_key_here
```

### 3. Start the Web App

```bash
uvicorn researchmind.api:app --reload --port 8000
```

Open **http://localhost:8000** in your browser.

### 4. Or Use the CLI

```bash
python -m researchmind.main --query "transformer architecture in NLP"
```

Results are saved to:

```
output/
├── research_report.md    ← Human-readable report
└── research_output.json  ← Structured data
```

---

## Web Frontend

The frontend provides a modern, dark-themed UI with:

- **Search Input** — type any research topic or use suggestion chips
- **Live Pipeline Progress** — 6 animated cards showing each agent's status in real-time
- **Report Viewer** — collapsible sections for paper summaries, synthesis, research gaps, and references

---

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | Serves the web frontend |
| `POST` | `/api/research` | Starts a research task (returns `task_id`) |
| `GET` | `/api/research/{task_id}` | Polls progress and result |
| `GET` | `/api/health` | Health check |

**Example:**

```bash
curl -X POST http://localhost:8000/api/research \
  -H "Content-Type: application/json" \
  -d '{"query": "reinforcement learning in robotics"}'
```

---

## Technologies

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| Gemini API | The AI brain — agents send prompts, get intelligent responses |
| arXiv API | Search and retrieve real research papers |
| Semantic Scholar API | Backup paper source (200M+ papers) |
| asyncio | Run multiple analyses in parallel |
| FastAPI | REST API server + serves frontend |
| HTML / CSS / JS | Web frontend with dark glassmorphism theme |
| ResearchMemory | Custom shared memory connecting all agents |

---

## Project Structure

```
ai-agent-for-research-final/
├── .env                        # Gemini API key (not tracked by git)
├── .env.example                # Template for env vars
├── .gitignore                  # Git ignore rules
├── requirements.txt            # Python dependencies
├── README.md
│
├── frontend/                   # Web UI
│   ├── index.html              # Main page
│   ├── style.css               # Dark glassmorphism theme
│   └── script.js               # API connection & rendering
│
├── researchmind/               # Backend
│   ├── __init__.py
│   ├── llm.py                  # Direct Gemini API wrapper
│   ├── memory.py               # ResearchMemory — shared store
│   ├── orchestrator.py         # 6-agent pipeline with progress callbacks
│   ├── main.py                 # CLI entry point
│   ├── api.py                  # FastAPI server (serves frontend + API)
│   ├── tools/
│   │   ├── search_tools.py     # arXiv + Semantic Scholar APIs
│   │   └── scrape_tools.py     # Content fetcher
│   └── agents/
│       ├── search_agent.py
│       ├── analysis_agent.py
│       ├── summary_agent.py
│       ├── synthesis_agent.py  # Self-reflection here
│       ├── opportunity_agent.py
│       └── report_agent.py
│
└── output/                     # Generated reports (gitignored)
```

---

## What We Did NOT Use (By Design)

| Framework | Why Skipped |
|---|---|
| LangChain | Built everything from scratch |
| CrewAI | Shows deeper understanding |
| AutoGen | No hidden complexity |
| LangGraph | Full control over architecture |

> *"We built every component from scratch — agents, memory, tools, orchestration — to demonstrate agentic AI concepts without hiding complexity behind frameworks."*

---

## License

MIT License — Built for academic/educational purposes.
