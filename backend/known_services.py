"""Known service database — maps popular service names to their official policy URLs.
This avoids needing an LLM just to find well-known URLs.
"""

KNOWN_SERVICES: dict[str, dict] = {
    "netflix": {
        "service_name": "Netflix",
        "domain": "netflix.com",
        "terms_url": "https://help.netflix.com/legal/termsofuse",
        "privacy_url": "https://help.netflix.com/legal/privacy",
    },
    "spotify": {
        "service_name": "Spotify",
        "domain": "spotify.com",
        "terms_url": "https://www.spotify.com/us/legal/end-user-agreement/",
        "privacy_url": "https://www.spotify.com/us/legal/privacy-policy/",
    },
    "amazon": {
        "service_name": "Amazon",
        "domain": "amazon.com",
        "terms_url": "https://www.amazon.com/gp/help/customer/display.html?nodeId=508088",
        "privacy_url": "https://www.amazon.com/gp/help/customer/display.html?nodeId=468496",
    },
    "google": {
        "service_name": "Google",
        "domain": "google.com",
        "terms_url": "https://policies.google.com/terms",
        "privacy_url": "https://policies.google.com/privacy",
    },
    "instagram": {
        "service_name": "Instagram",
        "domain": "instagram.com",
        "terms_url": "https://help.instagram.com/581066165581870",
        "privacy_url": "https://privacycenter.instagram.com/policy",
    },
    "tiktok": {
        "service_name": "TikTok",
        "domain": "tiktok.com",
        "terms_url": "https://www.tiktok.com/legal/page/us/terms-of-service",
        "privacy_url": "https://www.tiktok.com/legal/page/us/privacy-policy",
    },
    "uber": {
        "service_name": "Uber",
        "domain": "uber.com",
        "terms_url": "https://www.uber.com/legal/en/document/?name=general-terms-of-use",
        "privacy_url": "https://www.uber.com/legal/en/document/?name=privacy-notice",
    },
    "discord": {
        "service_name": "Discord",
        "domain": "discord.com",
        "terms_url": "https://discord.com/terms",
        "privacy_url": "https://discord.com/privacy",
    },
    "twitter": {
        "service_name": "X (Twitter)",
        "domain": "x.com",
        "terms_url": "https://x.com/en/tos",
        "privacy_url": "https://x.com/en/privacy",
    },
    "facebook": {
        "service_name": "Facebook",
        "domain": "facebook.com",
        "terms_url": "https://www.facebook.com/terms.php",
        "privacy_url": "https://www.facebook.com/privacy/policy/",
    },
    "apple": {
        "service_name": "Apple",
        "domain": "apple.com",
        "terms_url": "https://www.apple.com/legal/internet-services/itunes/",
        "privacy_url": "https://www.apple.com/legal/privacy/",
    },
    "microsoft": {
        "service_name": "Microsoft",
        "domain": "microsoft.com",
        "terms_url": "https://www.microsoft.com/en-us/servicesagreement",
        "privacy_url": "https://privacy.microsoft.com/en-us/privacystatement",
    },
    "reddit": {
        "service_name": "Reddit",
        "domain": "reddit.com",
        "terms_url": "https://www.redditinc.com/policies/user-agreement",
        "privacy_url": "https://www.reddit.com/policies/privacy-policy",
    },
    "youtube": {
        "service_name": "YouTube",
        "domain": "youtube.com",
        "terms_url": "https://www.youtube.com/t/terms",
        "privacy_url": "https://policies.google.com/privacy",
    },
    "linkedin": {
        "service_name": "LinkedIn",
        "domain": "linkedin.com",
        "terms_url": "https://www.linkedin.com/legal/user-agreement",
        "privacy_url": "https://www.linkedin.com/legal/privacy-policy",
    },
    "snapchat": {
        "service_name": "Snapchat",
        "domain": "snapchat.com",
        "terms_url": "https://snap.com/en-US/terms",
        "privacy_url": "https://snap.com/en-US/privacy/privacy-policy",
    },
    "whatsapp": {
        "service_name": "WhatsApp",
        "domain": "whatsapp.com",
        "terms_url": "https://www.whatsapp.com/legal/terms-of-service",
        "privacy_url": "https://www.whatsapp.com/legal/privacy-policy",
    },
    "zoom": {
        "service_name": "Zoom",
        "domain": "zoom.us",
        "terms_url": "https://explore.zoom.us/en/terms/",
        "privacy_url": "https://explore.zoom.us/en/privacy/",
    },
    "openai": {
        "service_name": "OpenAI",
        "domain": "openai.com",
        "terms_url": "https://openai.com/policies/terms-of-use",
        "privacy_url": "https://openai.com/policies/privacy-policy",
    },
    "chatgpt": {
        "service_name": "OpenAI (ChatGPT)",
        "domain": "openai.com",
        "terms_url": "https://openai.com/policies/terms-of-use",
        "privacy_url": "https://openai.com/policies/privacy-policy",
    },
    "hulu": {
        "service_name": "Hulu",
        "domain": "hulu.com",
        "terms_url": "https://www.hulu.com/terms",
        "privacy_url": "https://www.hulu.com/privacy",
    },
}


def lookup_service(query: str) -> dict | None:
    """Look up a service by name. Returns service info dict or None."""
    key = query.strip().lower()
    # Direct match
    if key in KNOWN_SERVICES:
        return KNOWN_SERVICES[key].copy()
    # Partial match
    for k, v in KNOWN_SERVICES.items():
        if key in k or k in key:
            return v.copy()
    return None
