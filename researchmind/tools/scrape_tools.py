"""
scrape_tools.py — Paper Content Fetcher

Fetches additional paper content when needed.
Primary source: arXiv abstracts (already available from search).
Backup: basic URL content fetcher.
"""

import aiohttp


async def fetch_paper_content(url: str) -> str:
    """
    Fetch content from a paper URL.

    For arXiv papers, the abstract is already retrieved during search.
    This is a backup for fetching additional content from URLs.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=20),
                headers={
                    "User-Agent": "ResearchMind/1.0 (Academic Research Tool)"
                },
            ) as resp:
                if resp.status != 200:
                    return f"[Could not fetch content: HTTP {resp.status}]"

                content_type = resp.headers.get("Content-Type", "")
                if "text/html" in content_type or "text/plain" in content_type:
                    text = await resp.text()
                    # Basic cleanup — remove HTML tags
                    import re
                    clean = re.sub(r"<[^>]+>", " ", text)
                    clean = re.sub(r"\s+", " ", clean).strip()
                    # Limit length
                    return clean[:5000]
                else:
                    return "[Content is not text-based (likely PDF)]"

    except Exception as e:
        return f"[Error fetching content: {e}]"


async def fetch_arxiv_abstract(arxiv_id: str) -> str:
    """
    Fetch the abstract of an arXiv paper by its ID.

    Args:
        arxiv_id: The arXiv paper ID (e.g., '2301.12345')
    """
    import xml.etree.ElementTree as ET

    api_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                if resp.status != 200:
                    return ""

                text = await resp.text()

        root = ET.fromstring(text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entry = root.find("atom:entry", ns)

        if entry is not None:
            summary = entry.find("atom:summary", ns)
            if summary is not None and summary.text:
                return summary.text.strip()

    except Exception as e:
        print(f"  ⚠ arXiv abstract fetch error: {e}")

    return ""
