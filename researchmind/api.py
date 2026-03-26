"""
api.py — FastAPI Backend for ResearchMind

Provides:
  POST /api/research        — Start a research task (returns task_id)
  GET  /api/research/{id}   — Poll task progress & results
  GET  /api/health          — Health check
  GET  /                    — Serves the frontend

Usage:
    uvicorn researchmind.api:app --reload --port 8000
"""

import asyncio
import os
import uuid
from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from researchmind.orchestrator import run_research, AGENT_LABELS

# ── App Setup ─────────────────────────────────────────────────

app = FastAPI(
    title="ResearchMind API",
    description="AI-Powered Academic Literature Review — Agentic AI System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Serve Frontend Static Files ───────────────────────────────

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


# ── In-Memory Task Store ──────────────────────────────────────

tasks: dict[str, dict[str, Any]] = {}


class ResearchRequest(BaseModel):
    query: str
    output_dir: str = "output"


# ── Helper: progress callback factory ─────────────────────────

def _make_progress_cb(task_id: str):
    """Returns a callback that updates the task store on each agent step."""

    def cb(step: int, label: str, status: str, detail: str = ""):
        task = tasks.get(task_id)
        if task is None:
            return
        task["current_step"] = step
        task["current_label"] = label
        # Update the per-agent status list
        task["agents"][step - 1] = {
            "step": step,
            "label": label,
            "status": status,
            "detail": detail,
        }

    return cb


# ── Background runner ─────────────────────────────────────────

async def _run_task(task_id: str, query: str, output_dir: str):
    """Runs the full research pipeline in the background."""
    task = tasks[task_id]
    try:
        memory = await run_research(
            topic=query,
            output_dir=output_dir,
            progress_callback=_make_progress_cb(task_id),
        )
        task["status"] = "completed"
        task["result"] = memory.to_dict()
        task["completed_at"] = datetime.now().isoformat()
    except Exception as exc:
        task["status"] = "failed"
        task["error"] = str(exc)
        task["completed_at"] = datetime.now().isoformat()


# ── API Routes ────────────────────────────────────────────────

@app.get("/")
async def serve_frontend():
    """Serve the frontend index.html."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    return {"message": "ResearchMind API is running. Frontend not found — place files in /frontend."}


@app.post("/api/research")
async def start_research(req: ResearchRequest):
    """Start a new research task. Returns a task_id for polling."""
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    task_id = uuid.uuid4().hex[:12]
    tasks[task_id] = {
        "task_id": task_id,
        "query": req.query,
        "status": "running",
        "current_step": 0,
        "current_label": "",
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "error": None,
        "result": None,
        "agents": [
            {"step": i + 1, "label": lbl, "status": "pending", "detail": ""}
            for i, lbl in enumerate(AGENT_LABELS)
        ],
    }

    # Fire-and-forget background task
    asyncio.create_task(_run_task(task_id, req.query, req.output_dir))

    return {"task_id": task_id, "status": "running"}


@app.get("/api/research/{task_id}")
async def get_task(task_id: str):
    """Poll the progress / result of a research task."""
    task = tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "agents": 6,
        "tools": ["arXiv", "Semantic Scholar", "Gemini"],
    }
