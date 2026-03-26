"""
search_tools.py — arXiv + Semantic Scholar API Tools

These are the "tools" that agents use to find real academic papers.
No scraping, no Google Scholar — just official free APIs.
"""

import xml.etree.ElementTree as ET
from typing import Any
import aiohttp


# ── arXiv API ─────────────────────────────────────────────────

ARXIV_API_URL = "http://export.arxiv.org/api/query"


async def search_arxiv(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """
    Search arXiv for papers matching the query.

    Uses the official arXiv Atom API (free, no key needed).
    Returns structured paper metadata.
    """
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }

    papers = []

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(ARXIV_API_URL, params=params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    print(f"  ⚠ arXiv API returned status {resp.status}")
                    return papers

                text = await resp.text()

        # Parse Atom XML
        root = ET.fromstring(text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        for entry in root.findall("atom:entry", ns):
            title_el = entry.find("atom:title", ns)
            summary_el = entry.find("atom:summary", ns)
            published_el = entry.find("atom:published", ns)
            id_el = entry.find("atom:id", ns)

            # Get authors
            authors = []
            for author in entry.findall("atom:author", ns):
                name_el = author.find("atom:name", ns)
                if name_el is not None and name_el.text:
                    authors.append(name_el.text.strip())

            # Get PDF link
            pdf_url = ""
            for link in entry.findall("atom:link", ns):
                if link.get("title") == "pdf":
                    pdf_url = link.get("href", "")

            paper = {
                "title": title_el.text.strip().replace("\n", " ") if title_el is not None and title_el.text else "Unknown",
                "authors": authors,
                "abstract": summary_el.text.strip().replace("\n", " ") if summary_el is not None and summary_el.text else "",
                "year": published_el.text[:4] if published_el is not None and published_el.text else "Unknown",
                "url": id_el.text.strip() if id_el is not None and id_el.text else "",
                "pdf_url": pdf_url,
                "source": "arXiv",
            }
            papers.append(paper)

    except Exception as e:
        print(f"  ⚠ arXiv search error: {e}")

    return papers


# ── Semantic Scholar API ──────────────────────────────────────

SEMANTIC_SCHOLAR_URL = "https://api.semanticscholar.org/graph/v1/paper/search"


async def search_semantic_scholar(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """
    Search Semantic Scholar for papers matching the query.

    Uses the free API (no key needed, 200M+ papers).
    Backup source to arXiv.
    """
    params = {
        "query": query,
        "limit": max_results,
        "fields": "title,authors,abstract,year,url,citationCount",
    }

    papers = []

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                SEMANTIC_SCHOLAR_URL,
                params=params,
                timeout=aiohttp.ClientTimeout(total=30),
                headers={"Accept": "application/json"},
            ) as resp:
                if resp.status != 200:
                    print(f"  ⚠ Semantic Scholar API returned status {resp.status}")
                    return papers

                data = await resp.json()

        for item in data.get("data", []):
            authors = [
                a.get("name", "Unknown")
                for a in item.get("authors", [])
            ]

            paper = {
                "title": item.get("title", "Unknown"),
                "authors": authors,
                "abstract": item.get("abstract", "") or "",
                "year": str(item.get("year") or "Unknown"),
                "url": item.get("url", ""),
                "citation_count": item.get("citationCount", 0),
                "source": "Semantic Scholar",
            }
            papers.append(paper)

    except Exception as e:
        print(f"  ⚠ Semantic Scholar search error: {e}")

    return papers


# ── Combined Search ───────────────────────────────────────────

async def search_papers(query: str, max_per_source: int = 5) -> list[dict[str, Any]]:
    """
    Search both arXiv and Semantic Scholar, deduplicate, return combined results.
    """
    import asyncio

    # Run both searches in parallel
    arxiv_results, ss_results = await asyncio.gather(
        search_arxiv(query, max_per_source),
        search_semantic_scholar(query, max_per_source),
        return_exceptions=True,
    )

    # Handle exceptions
    if isinstance(arxiv_results, Exception):
        print(f"  ⚠ arXiv search failed: {arxiv_results}")
        arxiv_results = []
    if isinstance(ss_results, Exception):
        print(f"  ⚠ Semantic Scholar search failed: {ss_results}")
        ss_results = []

    # Combine and deduplicate by title (case-insensitive)
    seen_titles = set()
    combined = []

    for paper in arxiv_results + ss_results:
        title_lower = paper["title"].lower().strip()
        if title_lower not in seen_titles:
            seen_titles.add(title_lower)
            combined.append(paper)

    return combined
