"""Ollama LLM client — service resolution + policy attribute extraction."""

import json
import logging
import os
import re
from typing import Any

import ollama as ollama_lib

logger = logging.getLogger(__name__)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

# Attribute IDs we expect from the extraction prompt
EXPECTED_ATTRIBUTES = [
    "data_selling",
    "data_sharing",
    "account_deletion",
    "encryption",
    "data_retention",
    "third_party_tracking",
    "government_requests",
    "arbitration_clause",
    "class_action_waiver",
    "unilateral_changes",
    "liability_limitation",
    "content_license",
]


def _get_client() -> ollama_lib.Client:
    """Create an Ollama client pointed at the configured host."""
    return ollama_lib.Client(host=OLLAMA_HOST)


def _repair_json(raw: str) -> str:
    """
    Attempt to extract and fix JSON from LLM output.
    Handles: markdown fences, trailing commas, unquoted keys, etc.
    """
    # Strip markdown fences
    raw = re.sub(r"```(?:json)?\s*", "", raw)
    raw = re.sub(r"```\s*$", "", raw)
    raw = raw.strip()

    # Find the first { or [ and last } or ]
    start_obj = raw.find("{")
    start_arr = raw.find("[")
    if start_obj == -1 and start_arr == -1:
        return raw
    if start_arr == -1 or (start_obj != -1 and start_obj < start_arr):
        start = start_obj
        end = raw.rfind("}") + 1
    else:
        start = start_arr
        end = raw.rfind("]") + 1

    if end <= start:
        return raw

    candidate = raw[start:end]

    # Remove trailing commas before } or ]
    candidate = re.sub(r",\s*([}\]])", r"\1", candidate)

    return candidate


def _parse_json(raw: str) -> Any:
    """Parse JSON from LLM output with repair attempts."""
    repaired = _repair_json(raw)
    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        # Last resort: try to find any JSON-like structure
        match = re.search(r'[{\[].*[}\]]', repaired, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        raise ValueError(f"Could not parse LLM output as JSON: {repaired[:200]}...")


def resolve_service(query: str, retries: int = 2) -> dict:
    """
    LLM call #1: Resolve a user query into service name, domain, and policy URLs.
    
    Returns dict with: service_name, domain, terms_url, privacy_url
    """
    client = _get_client()

    prompt = f"""Given the user query "{query}", identify the online service they mean and find the official Terms of Service and Privacy Policy URLs.

Return ONLY valid JSON with no additional text:
{{
  "service_name": "Official Service Name",
  "domain": "example.com",
  "terms_url": "https://example.com/terms",
  "privacy_url": "https://example.com/privacy"
}}

Rules:
- Use the most well-known official domain
- URLs must be full https:// URLs to the actual legal pages
- If you're unsure of exact URLs, use your best knowledge of where major services host their legal pages
- Do NOT wrap in markdown, do NOT add explanations"""

    last_error = None
    for attempt in range(retries + 1):
        try:
            response = client.chat(
                model=OLLAMA_MODEL,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.1, "num_predict": 300},
            )
            content = response["message"]["content"]
            logger.info(f"Resolve attempt {attempt + 1}: {content[:200]}")
            result = _parse_json(content)

            # Validate required keys
            for key in ("service_name", "domain", "terms_url", "privacy_url"):
                if key not in result:
                    raise ValueError(f"Missing key: {key}")

            return result

        except Exception as e:
            last_error = e
            logger.warning(f"Resolve attempt {attempt + 1} failed: {e}")

    raise RuntimeError(f"Failed to resolve service after {retries + 1} attempts: {last_error}")


def extract_attributes(text: str, retries: int = 2) -> list[dict]:
    """
    LLM call #2: Extract policy attributes from scraped legal text.
    
    Returns list of dicts, each with: id, value, severity, evidence
    """
    client = _get_client()

    # Truncate text to ~12k tokens (~48k chars as rough estimate)
    max_chars = 48000
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[TEXT TRUNCATED]"

    prompt = f"""Analyze the following Terms of Service / Privacy Policy text.

For each attribute below, return a JSON array of objects. Each object must have:
- "id": the attribute ID exactly as listed
- "value": factual answer (e.g. "Yes", "No", "30 days", etc.)
- "severity": exactly one of "good", "neutral", or "bad"
- "evidence": a single sentence quoted or paraphrased from the text

Severity guide:
- "good" = user-friendly (e.g. no data selling, easy deletion, encryption present)
- "bad" = user-hostile (e.g. sells data, mandatory arbitration, no deletion)
- "neutral" = ambiguous or standard industry practice

Attributes to extract:
1. data_selling — Does the service sell user data to third parties?
2. data_sharing — Does it share data with affiliates/partners beyond what's needed?
3. account_deletion — Can users fully delete their account and data?
4. encryption — Is user data encrypted at rest and in transit?
5. data_retention — How long is data kept after account deletion?
6. third_party_tracking — Are third-party trackers/analytics/ad cookies used?
7. government_requests — Does the company comply with government data requests without notifying users?
8. arbitration_clause — Is there a mandatory arbitration clause?
9. class_action_waiver — Does the user waive class-action lawsuit rights?
10. unilateral_changes — Can the company change terms without prior notice?
11. liability_limitation — Is the company's liability capped or broadly excluded?
12. content_license — Does the company claim a broad license to user-generated content?

Return ONLY a valid JSON array, no explanations, no markdown fences.

TEXT:
{text}"""

    last_error = None
    for attempt in range(retries + 1):
        try:
            response = client.chat(
                model=OLLAMA_MODEL,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.1, "num_predict": 2000},
            )
            content = response["message"]["content"]
            logger.info(f"Extract attempt {attempt + 1}: {content[:300]}")
            result = _parse_json(content)

            # Normalize: if result is a dict with a list inside, unwrap it
            if isinstance(result, dict):
                for v in result.values():
                    if isinstance(v, list):
                        result = v
                        break
                else:
                    result = [result]

            if not isinstance(result, list):
                raise ValueError("Expected a JSON array of attributes")

            # Fill in any missing attributes with defaults
            found_ids = {a.get("id") for a in result if isinstance(a, dict)}
            for attr_id in EXPECTED_ATTRIBUTES:
                if attr_id not in found_ids:
                    result.append({
                        "id": attr_id,
                        "value": "Not mentioned in policy",
                        "severity": "neutral",
                        "evidence": "This attribute was not explicitly addressed in the analyzed text.",
                    })

            # Filter to only expected attributes
            result = [a for a in result if isinstance(a, dict) and a.get("id") in EXPECTED_ATTRIBUTES]

            return result

        except Exception as e:
            last_error = e
            logger.warning(f"Extract attempt {attempt + 1} failed: {e}")

    raise RuntimeError(f"Failed to extract attributes after {retries + 1} attempts: {last_error}")


def check_connection() -> bool:
    """Check if Ollama is reachable."""
    try:
        client = _get_client()
        client.list()
        return True
    except Exception:
        return False
