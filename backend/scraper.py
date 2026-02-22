"""Web scraper — validates URLs and extracts legal page text."""

import logging
import re

import httpx
import trafilatura

logger = logging.getLogger(__name__)

# Realistic browser user-agent
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

# Max text length (~12k tokens ≈ 48k chars)
MAX_TEXT_LENGTH = 48000


async def validate_url(url: str, timeout: float = 10.0) -> bool:
    """Check if a URL is reachable. Tries HEAD first, falls back to GET."""
    try:
        async with httpx.AsyncClient(
            follow_redirects=True, timeout=timeout, headers=HEADERS
        ) as client:
            resp = await client.head(url)
            if resp.status_code == 405:
                # Some sites (e.g. Amazon) reject HEAD — try GET
                resp = await client.get(url)
            return resp.status_code < 400
    except Exception as e:
        logger.warning(f"URL validation failed for {url}: {e}")
        return False


async def fetch_html(url: str, timeout: float = 20.0) -> str:
    """Fetch the raw HTML from a URL."""
    async with httpx.AsyncClient(
        follow_redirects=True, timeout=timeout, headers=HEADERS
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text


def extract_text(html: str, url: str | None = None) -> str:
    """
    Extract main text content from HTML, stripping boilerplate.
    Uses trafilatura for best results.
    """
    text = trafilatura.extract(
        html,
        url=url,
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        favor_precision=False,
        favor_recall=True,
    )

    if not text or len(text.strip()) < 200:
        # Fallback: basic HTML stripping
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        # Remove script, style, nav, footer
        for tag in soup.find_all(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)

    if not text:
        return ""

    # Clean up excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)

    # Truncate
    if len(text) > MAX_TEXT_LENGTH:
        text = text[:MAX_TEXT_LENGTH]

    return text.strip()


async def scrape_page(url: str) -> str:
    """
    Full pipeline: fetch URL → extract text.
    Returns extracted text or empty string on failure.
    """
    try:
        html = await fetch_html(url)
        text = extract_text(html, url=url)
        logger.info(f"Scraped {url}: {len(text)} chars")
        return text
    except Exception as e:
        logger.error(f"Failed to scrape {url}: {e}")
        return ""


async def scrape_policies(
    terms_url: str, privacy_url: str
) -> str:
    """
    Scrape both terms and privacy pages, combine into one text block.
    Validates URLs first and skips any that fail.
    """
    sections = []

    for label, url in [("TERMS OF SERVICE", terms_url), ("PRIVACY POLICY", privacy_url)]:
        if not url:
            continue

        is_valid = await validate_url(url)
        if not is_valid:
            logger.warning(f"URL invalid/unreachable, skipping: {url}")
            sections.append(f"=== {label} ===\n[Could not access {url}]\n")
            continue

        text = await scrape_page(url)
        if text:
            sections.append(f"=== {label} ===\n{text}\n")
        else:
            sections.append(f"=== {label} ===\n[Failed to extract text from {url}]\n")

    combined = "\n\n".join(sections)

    # Final truncation if combined text is too long
    if len(combined) > MAX_TEXT_LENGTH:
        combined = combined[:MAX_TEXT_LENGTH]

    return combined
