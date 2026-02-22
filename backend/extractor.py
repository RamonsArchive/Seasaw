"""Keyword-based policy attribute extraction using heuristics.

This module analyzes Terms of Service / Privacy Policy text by scanning
for keyword patterns. It works without any LLM — pure text analysis.

Key design decisions:
- Good patterns are checked FIRST and take priority when found in negation context
- Account deletion patterns require "your account" context (not just "remove content")
- Every attribute ALWAYS gets evidence — even neutral ones get a reasoned explanation
- Broader context extraction (~200 chars) ensures quotes are meaningful
"""

import re

# Attribute IDs in display order
ATTRIBUTE_IDS = [
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

# Each attribute has patterns grouped by severity
# Patterns are ordered by specificity (most specific first)
ATTRIBUTE_PATTERNS: dict[str, dict] = {
    "data_selling": {
        "good": [
            r"(do\s+not|don.t|never|will\s+not|won.t)\s+sell\s+(your\s+)?(personal\s+)?(data|information)",
            r"we\s+(do\s+not|don.t|never)\s+sell",
            r"not\s+sell\s+(or\s+rent\s+)?(your\s+)?personal",
            r"we\s+will\s+not\s+sell\s+your",
        ],
        "bad": [
            r"sell\w*\s+(your\s+)?(personal\s+)?(data|information)",
            r"share\s+(your\s+)?(personal\s+)?(data|information)\s+with\s+.{0,20}(advertis|market)",
            r"monetiz\w+\s+(your\s+)?(data|information)",
            r"(data|information)\s+(may|will|can)\s+be\s+sold",
            r"sell\s+(or\s+rent\s+)?(your\s+)?personal",
            r"share.{0,30}(advertising|marketing)\s+partner",
        ],
        "context": [
            r"(personal\s+)?(data|information).{0,80}(third.part|partner|advertis|share|collect|use|process)",
            r"(collect|gather|obtain)\s+(your\s+)?(personal\s+)?(data|information)",
        ],
    },
    "data_sharing": {
        "good": [
            r"(do\s+not|don.t|never)\s+share\s+(your\s+)?(personal\s+)?(data|information)\s+with\s+third",
            r"limit\w*\s+shar(ing|e)\s+of\s+(your\s+)?(personal\s+)?(data|information)",
            r"only\s+share.{0,30}(necessary|essential|required|needed)",
        ],
        "bad": [
            r"share\s+(your\s+)?(personal\s+)?(data|information)\s+with\s+(our\s+)?(affiliat|partner|third.part|vendor|service\s+provider)",
            r"disclose\s+(your\s+)?(personal\s+)?(data|information)\s+to\s+(our\s+)?(affiliat|partner|third.part)",
            r"provide\s+(your\s+)?(data|information)\s+to\s+(our\s+)?(affiliat|partner|third.part)",
            r"(may|will)\s+(also\s+)?share\s+(your\s+)?(personal\s+)?(data|information)",
            r"categories\s+of\s+third\s+parties\s+.{0,30}(share|disclose|provide)",
        ],
        "context": [
            r"(share|sharing|disclose|disclosure).{0,60}(data|information|personal)",
        ],
    },
    "account_deletion": {
        "good": [
            r"(delete|close|deactivate|terminate)\s+your\s+account",
            r"request\s+(the\s+)?(deletion|removal|erasure)\s+of\s+your\s+(personal\s+)?(data|information|account)",
            r"right\s+to\s+(have\s+)?(your\s+)?(personal\s+)?(data|information|account)\s+(deleted|erased|removed)",
            r"right\s+to\s+be\s+forgotten",
            r"right\s+to\s+(request\s+)?(deletion|erasure)",
            r"you\s+(can|may)\s+(request\s+)?(to\s+)?(delete|erase|remove)\s+(your\s+)?(account|personal)",
        ],
        "bad": [
            r"(cannot|can.t|unable\s+to)\s+(fully\s+)?(delete|remove|erase)\s+(your\s+)?account",
            r"(retain|keep|maintain)\s+(your\s+)?(personal\s+)?(data|information).{0,30}(even\s+after|after\s+you|after\s+account|indefinit)",
            r"(may\s+)?(retain|keep)\s+(certain|some)\s+(data|information)\s+after\s+(deletion|you\s+delete|account\s+closure)",
            r"(not\s+possible|unable)\s+to\s+(completely\s+)?(delete|remove|erase)",
        ],
        "context": [
            r"(account|data|information).{0,60}(delet|remov|eras|clos|terminat|deactivat)",
            r"(delet|remov|eras|clos|terminat).{0,60}(account|data|information|personal)",
        ],
    },
    "encryption": {
        "good": [
            r"encrypt\w+\s+(at\s+rest|in\s+transit|in\s+storage)",
            r"(data|information)\s+(is|are)\s+encrypt",
            r"(use|implement|employ)\s+encrypt",
            r"(SSL|TLS|AES|end.to.end)\s+encrypt",
            r"(secure|encrypted)\s+(connection|transmission|communication|storage)",
            r"industry.standard\s+(security|encryption|protection)",
        ],
        "bad": [
            r"(no|without|lack\s+of)\s+encrypt",
            r"unencrypt\w+\s+(data|information|transmission)",
            r"(data|information)\s+(is|are)\s+not\s+encrypt",
        ],
        "context": [
            r"(security|protect|safeguard|encrypt).{0,80}(data|information|measure|practice)",
            r"(data|information).{0,80}(security|protect|safeguard|encrypt)",
        ],
    },
    "data_retention": {
        "good": [
            r"(delete|remove|erase)\s+(your\s+)?(data|information)\s+(within|after|no\s+later\s+than)\s+\d+\s+(day|month|year)",
            r"retain\w*\s+(your\s+)?(data|information)\s+for\s+(only\s+)?(a\s+)?(\d+|limited|short|minimum)",
            r"retention\s+period\s+(of\s+)?\d+\s+(day|month|year)",
            r"(data|information).{0,30}(retained|kept|stored)\s+for\s+(no\s+longer|only|up\s+to)\s+\d+",
        ],
        "bad": [
            r"retain\w*\s+(your\s+)?(data|information)\s+(indefinit|permanent|forever|without\s+limit)",
            r"(may\s+)?(retain|keep|maintain|store)\s+(your\s+)?(data|information|personal).{0,30}(as\s+long\s+as|for\s+as\s+long|necessary|needed|required|indefinit)",
            r"retain\w*\s+(your\s+)?(data|information).{0,20}after\s+(you\s+)?(terminat|delet|close|cancel)",
            r"(continue|keep)\s+to\s+(store|retain|keep).{0,30}after.{0,20}(account|cancel|terminat|delet)",
        ],
        "context": [
            r"(retain|retention|keep|store|preserv).{0,80}(data|information|personal|record)",
            r"(data|information).{0,80}(retain|retention|keep|stor|preserv|period)",
        ],
    },
    "third_party_tracking": {
        "bad": [
            r"(third.party|3rd.party)\s+(cookie|track|analytic|beacon|pixel|tag)",
            r"(google\s+analytics|facebook\s+pixel|advertising\s+partner|ad\s+network)",
            r"(track|monitor|collect).{0,20}(your\s+)?(activity|behavior|browsing|usage|interaction)",
            r"(cookie|tracker|pixel|beacon)\s+(from|by|of|set\s+by)\s+(third|3rd|advertis|partner)",
            r"(advertising|analytics|tracking)\s+(cookie|technolog|tool|partner|provider)",
            r"interest.based\s+(advertising|ads|marketing)",
            r"targeted\s+(advertising|ads|marketing)",
        ],
        "good": [
            r"(do\s+not|don.t|never)\s+(use\s+)?(third.party|3rd.party)\s+(cookie|track|analytic)",
            r"(no|without)\s+(third.party|3rd.party)\s+(cookie|track|analytic)",
            r"(do\s+not|don.t)\s+track\s+(your\s+)?(activity|behavior|browsing)",
        ],
        "context": [
            r"(cookie|track|analytic|advertis).{0,80}(third|partner|provider|technology)",
        ],
    },
    "government_requests": {
        "bad": [
            r"(comply|cooperat|respond)\s+(with\s+)?(law\s+enforcement|government|legal|court|judicial)\s+(request|order|subpoena|warrant|demand)",
            r"disclos\w*\s+(your\s+)?(personal\s+)?(data|information)\s+(to|in\s+response\s+to|when\s+required\s+by)\s+(law\s+enforcement|government|authorit|legal|court)",
            r"(required|compelled|obligated)\s+(by|under)\s+(law|court\s+order|legal\s+process|subpoena)\s+to\s+(disclose|provide|share|reveal)",
            r"(may|will|can)\s+(be\s+required\s+to\s+)?(disclose|provide|share).{0,30}(law\s+enforcement|government|legal|authorit)",
        ],
        "good": [
            r"(notify|inform|alert)\s+(you|user|subscriber)\s+(of|about|when|before).{0,30}(government|law\s+enforcement|legal)\s+(request|order|demand)",
            r"transparency\s+report",
            r"(will|shall)\s+(attempt\s+to\s+)?(notify|inform)\s+(you|user)\s+(before|prior\s+to)\s+(disclos|comply|respond)",
        ],
        "context": [
            r"(law\s+enforcement|government|legal|court|judicial|subpoena).{0,80}(request|order|demand|disclos|comply|data|information)",
        ],
    },
    "arbitration_clause": {
        "bad": [
            r"(mandatory|binding|compulsory)\s+arbitration",
            r"(agree|consent)\s+to\s+(resolve\s+.{0,20}through\s+)?arbitrat",
            r"(dispute|claim|controversy)\s+(shall|will|must)\s+be\s+(resolved|settled|decided)\s+(by|through|in|via)\s+arbitration",
            r"waiv\w*\s+(your\s+)?right\s+to\s+(a\s+)?(jury\s+)?trial",
            r"(are\s+)?agreeing\s+to\s+(binding\s+)?arbitration",
            r"arbitration\s+(shall|will)\s+be\s+(final|binding)",
        ],
        "good": [
            r"(no\s+|without\s+)(mandatory|binding)\s+arbitration",
            r"(right|option|choice)\s+to\s+(go\s+to|bring\s+.{0,15}in|pursue\s+.{0,15}in)\s+court",
            r"(may|can)\s+bring\s+(a\s+)?(claim|dispute|action)\s+in\s+court",
        ],
        "context": [
            r"(arbitrat|dispute\s+resolution|legal\s+dispute|claim\s+resolution).{0,100}(binding|mandatory|agree|waiv|court|trial|resolve)",
        ],
    },
    "class_action_waiver": {
        "bad": [
            r"(waiv|relinquish|give\s+up)\w*\s+(your\s+)?right\s+to\s+(a\s+)?(class.action|class\s+action|collective\s+action|representative\s+action)",
            r"(agree|consent).{0,20}(not\s+to\s+)?(bring|participat|join|commence).{0,20}(class.action|class\s+action|collective|representative)",
            r"class.action\s+waiver",
            r"(only|solely)\s+(on\s+an?\s+)?individual\s+basis",
            r"(no|not\s+permitted|prohibited).{0,15}(class.action|class\s+action|collective|representative)\s+(lawsuit|action|proceeding|claim)",
        ],
        "good": [
            r"(right|option|ability)\s+to\s+(participat|join|bring|commence).{0,20}(class.action|class\s+action|collective)",
        ],
        "context": [
            r"(class.action|class\s+action|collective|representative|individual\s+basis).{0,100}(waiv|right|agree|bring|participat)",
        ],
    },
    "unilateral_changes": {
        "bad": [
            r"(may|can|reserve\s+the\s+right\s+to)\s+(change|modify|update|amend|revis)\s+(these\s+)?(terms|agreement|policy|conditions)\s+(at\s+any\s+time|without\s+(?:prior\s+)?notice|in\s+our\s+(?:sole\s+)?discretion)",
            r"(change|modif|updat)\w*\s+(these\s+)?(terms|agreement|policy).{0,20}(without\s+)?(prior\s+)?noti(ce|fy|fication)",
            r"(your\s+)?continued\s+use\s+.{0,30}(constitutes|means|indicates)\s+(your\s+)?(acceptance|agreement|consent)",
            r"(effective|binding)\s+(immediately|upon\s+posting|when\s+posted)",
        ],
        "good": [
            r"(will|shall)\s+(provide\s+)?(notify|inform|alert|give\s+.{0,10}notice)\s+(you|user)\s+(of|about|before|prior\s+to|in\s+advance)",
            r"(30|60|90)\s+day\w*\s+(advance\s+)?noti(ce|fication)\s+(before|prior\s+to|of)\s+(any\s+)?(material\s+)?(change|modif)",
            r"(advance|prior|reasonable)\s+noti(ce|fication)\s+of\s+(any\s+)?(material\s+)?(change|modif)",
            r"(email|notify)\s+(you|user)\s+(before|prior).{0,20}(change|modif|updat)",
        ],
        "context": [
            r"(change|modify|update|amend|revis).{0,80}(terms|agreement|policy|conditions|notice|notification)",
        ],
    },
    "liability_limitation": {
        "bad": [
            r"(limit|cap|exclud|disclaim)\w*\s+(of\s+)?(our|its|the\s+company.s|.{0,20})?\s*(liability|damages|responsibility)",
            r"(in\s+no\s+event|under\s+no\s+circumstance).{0,20}(shall|will).{0,30}(liable|liability|responsible)",
            r"(aggregate|total|maximum|cumulative)\s+liability\s+(shall|will|of).{0,20}(not\s+exceed|be\s+limited|limited\s+to)",
            r"(as.is|as\s+available|without\s+warrant)",
            r"(disclaim|exclude)\s+(all|any)\s+(warrant|liabilit|responsibilit|damage)",
            r"(shall|will)\s+not\s+be\s+(liable|responsible)\s+for\s+(any\s+)?(indirect|consequential|incidental|special|punitive|exemplary)",
        ],
        "good": [
            r"(full|unlimited|complete)\s+liability",
            r"(responsible|liable)\s+for\s+(all|any)\s+(damages|losses|harm)",
            r"(no\s+)?limitation\s+(on|of)\s+(our\s+)?liability",
        ],
        "context": [
            r"(liabilit|warrant|disclaim|damage|responsib|as.is).{0,100}(limit|cap|exclud|disclaim|indemn|maximum|aggregate)",
        ],
    },
    "content_license": {
        "bad": [
            r"(grant|give)\s+(us|.{0,30})\s+(a\s+)?(worldwide|perpetual|irrevocable|non.exclusive|royalty.free|sublicens|transferable).{0,50}(license|right)",
            r"(license|right)\s+to\s+(use|reproduce|modify|distribute|display|perform|create\s+derivative).{0,30}(your\s+)?(content|material|submission|post|upload)",
            r"(perpetual|irrevocable|unlimited|worldwide).{0,30}(license|right)\s+to\s+(your\s+)?(content|material|upload)",
            r"(we\s+may|reserves?\s+the\s+right\s+to)\s+(use|reproduce|modify|remove|disable\s+access\s+to)\s+(any\s+)?(user\s+)?(content|material)",
        ],
        "good": [
            r"(you\s+)?(own|retain)\s+(all\s+)?(right|ownership|intellectual\s+property)\s+(to|of|in)\s+(your\s+)?(content|material|upload)",
            r"(no|not|don.t|do\s+not)\s+(claim|take|assert)\s+(any\s+)?(ownership|proprietary)\s+(right|interest|claim)\s+(to|of|in|over)\s+(your\s+)?(content|material)",
            r"your\s+content\s+(remains|is|stays)\s+(your\s+)?(property|own)",
        ],
        "context": [
            r"(user\s+)?(content|material|submission|upload).{0,80}(license|right|own|retain|grant|use|reproduce|modify)",
            r"(license|right|grant|own).{0,80}(content|material|submission|upload)",
        ],
    },
}


def _extract_evidence(text: str, patterns: list[str], context_chars: int = 200) -> str | None:
    """
    Find the first matching pattern and return a clean surrounding quote.
    Extracts ~200 chars of context and tries to snap to sentence boundaries.
    """
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            start = max(0, match.start() - context_chars // 2)
            end = min(len(text), match.end() + context_chars // 2)

            snippet = text[start:end]

            # Snap to sentence start
            sentence_start = snippet.find(". ")
            if sentence_start != -1 and sentence_start < context_chars // 3:
                snippet = snippet[sentence_start + 2:]

            # Snap to sentence end
            last_period = snippet.rfind(".")
            if last_period != -1 and last_period > len(snippet) * 0.6:
                snippet = snippet[:last_period + 1]

            # Clean whitespace
            snippet = re.sub(r"\s+", " ", snippet).strip()

            if len(snippet) > 20:
                return f'"{snippet}"'
            return snippet if snippet else None
    return None


def _get_context_evidence(text: str, attr_id: str) -> str:
    """
    For neutral attributes — search for ANY related mentions in the text
    and build a reasoned explanation of why it's unclear.
    """
    patterns = ATTRIBUTE_PATTERNS.get(attr_id, {})
    context_patterns = patterns.get("context", [])

    evidence = _extract_evidence(text, context_patterns, context_chars=250)
    if evidence:
        return f"The policy mentions related topics but does not clearly address this: {evidence}"

    # Fallback: describe what we looked for
    descriptions = {
        "data_selling": "The policy does not contain explicit language about selling or not selling user data to third parties. This could indicate the company avoids directly addressing this practice.",
        "data_sharing": "The policy does not clearly state its data sharing practices with third-party partners or affiliates.",
        "account_deletion": "The policy does not explicitly describe a process for users to delete their accounts or request data erasure. Users may need to contact support directly.",
        "encryption": "The policy does not mention encryption, SSL/TLS, or specific data security measures. This does not necessarily mean data is unprotected, but transparency is lacking.",
        "data_retention": "The policy does not specify how long user data is retained or what happens to data after account closure.",
        "third_party_tracking": "The policy does not explicitly address the use of third-party tracking technologies, cookies, or analytics tools.",
        "government_requests": "The policy does not describe its process for handling government or law enforcement data requests, or whether users are notified.",
        "arbitration_clause": "The policy does not contain a mandatory arbitration clause. Disputes may be handled through standard legal channels.",
        "class_action_waiver": "The policy does not explicitly waive or preserve users' rights to participate in class-action lawsuits.",
        "unilateral_changes": "The policy does not clearly state how changes to terms are communicated to users or how much notice is given.",
        "liability_limitation": "The policy does not contain explicit liability limitations or warranty disclaimers.",
        "content_license": "The policy does not clearly address what rights the company claims over user-generated content.",
    }
    return descriptions.get(attr_id, "This attribute was not explicitly addressed in the analyzed policy text.")


def extract_attributes_heuristic(text: str) -> list[dict]:
    """
    Extract policy attributes using keyword heuristics.
    Returns a list of attribute dicts with: id, value, severity, evidence.

    Every attribute will ALWAYS have meaningful evidence — either a direct
    quote from the policy or a reasoned explanation.
    """
    results = []

    for attr_id in ATTRIBUTE_IDS:
        patterns = ATTRIBUTE_PATTERNS.get(attr_id, {})
        good_patterns = patterns.get("good", [])
        bad_patterns = patterns.get("bad", [])

        good_evidence = _extract_evidence(text, good_patterns)
        bad_evidence = _extract_evidence(text, bad_patterns)

        # Determine severity with priority logic:
        # 1. If BOTH good and bad are found → check which is more specific
        # 2. Good-only → good
        # 3. Bad-only → bad
        # 4. Neither → neutral with context-based evidence

        if good_evidence and bad_evidence:
            # Both found — for most attributes, bad overrides good
            # EXCEPT: negation patterns (like "do not sell") should win
            if attr_id in ("data_selling", "data_sharing", "third_party_tracking"):
                # These often have "do not share/sell" which should override
                severity = "good"
                value = _get_good_value(attr_id)
                evidence = f"Policy states: {good_evidence} — However, it also mentions: {bad_evidence}"
            else:
                severity = "bad"
                value = _get_bad_value(attr_id)
                evidence = f"Policy states: {bad_evidence}"
        elif good_evidence:
            severity = "good"
            value = _get_good_value(attr_id)
            evidence = f"Policy states: {good_evidence}"
        elif bad_evidence:
            severity = "bad"
            value = _get_bad_value(attr_id)
            evidence = f"Policy states: {bad_evidence}"
        else:
            severity = "neutral"
            value = "Not clearly addressed"
            evidence = _get_context_evidence(text, attr_id)

        results.append({
            "id": attr_id,
            "value": value,
            "severity": severity,
            "evidence": evidence,
        })

    return results


def _get_good_value(attr_id: str) -> str:
    """Human-readable 'good' value for an attribute."""
    values = {
        "data_selling": "No — does not sell personal data",
        "data_sharing": "Limited or no third-party data sharing",
        "account_deletion": "Yes — users can delete their account and data",
        "encryption": "Yes — data is encrypted",
        "data_retention": "Limited retention period specified",
        "third_party_tracking": "No third-party tracking",
        "government_requests": "Users are notified of government data requests",
        "arbitration_clause": "No mandatory arbitration",
        "class_action_waiver": "Class-action rights preserved",
        "unilateral_changes": "Advance notice provided before changes",
        "liability_limitation": "Full liability accepted",
        "content_license": "Users retain full content ownership",
    }
    return values.get(attr_id, "User-friendly")


def _get_bad_value(attr_id: str) -> str:
    """Human-readable 'bad' value for an attribute."""
    values = {
        "data_selling": "Yes — may sell or share data with advertisers",
        "data_sharing": "Shares data with third parties and affiliates",
        "account_deletion": "No clear account deletion option",
        "encryption": "No encryption practices mentioned",
        "data_retention": "Data retained indefinitely or long-term",
        "third_party_tracking": "Uses third-party trackers and cookies",
        "government_requests": "Complies with requests without notifying users",
        "arbitration_clause": "Mandatory binding arbitration required",
        "class_action_waiver": "Class-action lawsuit rights waived",
        "unilateral_changes": "Can change terms without prior notice",
        "liability_limitation": "Liability is capped or broadly excluded",
        "content_license": "Claims broad license to your content",
    }
    return values.get(attr_id, "User-hostile")
