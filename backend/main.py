"""Seasaw TrustScore — FastAPI backend.

Works in two modes:
1. WITH Ollama: Uses LLM for service resolution + attribute extraction (most accurate)
2. WITHOUT Ollama: Uses known-services database + keyword heuristics (works immediately)
"""

import logging
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import AnalyzeRequest, AnalyzeResponse
from known_services import lookup_service
from scraper import scrape_policies
from scoring import compute_score
from extractor import extract_attributes_heuristic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import LLM module — optional dependency
try:
    from llm import resolve_service, extract_attributes, check_connection
    HAS_LLM = True
except Exception:
    HAS_LLM = False

app = FastAPI(
    title="Seasaw TrustScore API",
    description="Analyze Terms of Service & Privacy Policies",
    version="1.0.0",
)

# Allow Next.js dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _check_ollama() -> bool:
    """Check if Ollama LLM is available."""
    if not HAS_LLM:
        return False
    try:
        return check_connection()
    except Exception:
        return False


@app.get("/health")
async def health():
    """Health check."""
    ollama_ok = _check_ollama()
    return {
        "status": "ok",
        "mode": "llm" if ollama_ok else "heuristic",
        "ollama": "connected" if ollama_ok else "unavailable (using keyword heuristics)",
    }


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    """
    Full analysis pipeline:
    1. Resolve service name → domain + policy URLs
    2. Scrape Terms & Privacy pages
    3. Extract policy attributes from text
    4. Compute deterministic TrustScore
    5. Return structured JSON
    """
    query = request.query.strip()
    logger.info(f"Analyzing: {query}")
    
    use_llm = _check_ollama()
    logger.info(f"Mode: {'LLM' if use_llm else 'Heuristic'}")

    # Step 1: Resolve service
    service = None
    
    # Try known services first (faster, more reliable)
    service = lookup_service(query)
    if service:
        logger.info(f"Found in known services: {service['service_name']}")
    elif use_llm:
        try:
            service = resolve_service(query)
            logger.info(f"LLM resolved: {service}")
        except Exception as e:
            logger.error(f"LLM resolution failed: {e}")
    
    if not service:
        raise HTTPException(
            status_code=422,
            detail=f"Could not identify the service '{query}'. Try one of: Netflix, Spotify, Google, Amazon, Discord, TikTok, Instagram, Uber, etc.",
        )

    # Step 2: Scrape policies
    try:
        policy_text = await scrape_policies(
            terms_url=service.get("terms_url", ""),
            privacy_url=service.get("privacy_url", ""),
        )
        logger.info(f"Scraped {len(policy_text)} chars of policy text")
        
        if len(policy_text.strip()) < 50:
            raise ValueError("Scraped text too short — pages may be blocked or empty")
            
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Could not scrape policy pages for {service.get('service_name', query)}. The site may be blocking automated access.",
        )

    # Step 3: Extract attributes
    try:
        if use_llm:
            raw_attributes = extract_attributes(policy_text)
        else:
            raw_attributes = extract_attributes_heuristic(policy_text)
        logger.info(f"Extracted {len(raw_attributes)} attributes")
    except Exception as e:
        logger.error(f"Attribute extraction failed: {e}")
        raise HTTPException(
            status_code=502,
            detail="Failed to analyze the policy text. Please try again.",
        )

    # Step 4: Compute score
    score, grade, enriched_attributes = compute_score(raw_attributes)
    logger.info(f"Score: {score} ({grade})")

    # Step 5: Build response
    return AnalyzeResponse(
        service_name=service.get("service_name", query),
        domain=service.get("domain", ""),
        terms_url=service.get("terms_url", ""),
        privacy_url=service.get("privacy_url", ""),
        trust_score=score,
        grade=grade,
        analyzed_at=datetime.now(timezone.utc).isoformat(),
        attributes=[
            {
                "id": a["id"],
                "label": a["label"],
                "value": a["value"],
                "severity": a["severity"],
                "evidence": a["evidence"],
                "weight": a["weight"],
                "points_earned": a["points_earned"],
            }
            for a in enriched_attributes
        ],
    )
