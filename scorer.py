from urllib.parse import urlparse

DOMAIN_SCORES = {
    # Wire services (93-95)
    "reuters.com": 95, "apnews.com": 95, "afp.com": 93, "bloomberg.com": 88,
    # Major English outlets (78-92)
    "bbc.com": 92, "bbc.co.uk": 92, "nytimes.com": 88, "theguardian.com": 87,
    "economist.com": 89, "ft.com": 87, "wsj.com": 85, "washingtonpost.com": 84,
    "time.com": 80, "newsweek.com": 78, "cnn.com": 75, "nbcnews.com": 75,
    # Scientific / Academic (82-99)
    "nature.com": 99, "science.org": 98, "ncbi.nlm.nih.gov": 98,
    "pubmed.ncbi.nlm.nih.gov": 98, "arxiv.org": 82, "jstor.org": 85,
    # Official / Government (90-97)
    "who.int": 97, "cdc.gov": 96, "nih.gov": 95, "un.org": 93,
    "europa.eu": 92, "gov.uk": 90,
    # Fact-checking (87-91)
    "factcheck.org": 91, "snopes.com": 88, "fullfact.org": 89, "politifact.com": 87,
    # Spanish / Catalan outlets (75-88)
    "elpais.com": 85, "rtve.es": 82, "lavanguardia.com": 80, "efe.com": 88,
    "elconfidencial.com": 78, "elperiodico.com": 75, "ccma.cat": 80, "324.cat": 78,
    # Reference (65-78)
    "wikipedia.org": 65, "britannica.com": 78,
    # Low credibility (15-40)
    "medium.com": 40, "substack.com": 35, "wordpress.com": 30,
    "reddit.com": 20, "twitter.com": 25, "x.com": 25, "facebook.com": 15,
}

def score_source(url: str) -> dict:
    if not url:
        return {"score": 30, "tier": "Unknown", "domain": "—"}
    try:
        domain = urlparse(url).netloc.replace("www.", "").lower()
    except Exception:
        return {"score": 30, "tier": "Unknown", "domain": "—"}

    for known, score in DOMAIN_SCORES.items():
        if known in domain:
            return {"score": score, "tier": tier(score), "domain": domain}

    if any(domain.endswith(t) for t in [".gov", ".gob.es", ".gouv.fr"]):
        return {"score": 85, "tier": "Government", "domain": domain}
    if domain.endswith(".edu"):
        return {"score": 78, "tier": "Academic", "domain": domain}
    if domain.endswith(".org"):
        return {"score": 55, "tier": "Organization", "domain": domain}

    return {"score": 40, "tier": "Unknown", "domain": domain}

def tier(score: int) -> str:
    if score >= 90: return "Highly Trusted"
    if score >= 75: return "Trusted"
    if score >= 60: return "Moderate"
    if score >= 40: return "Low"
    return "Unreliable"

def verdict_color(verdict: str) -> str:
    v = verdict.upper()
    if v == "TRUE":             return "#6ab187"
    if v == "FALSE":            return "#c0726a"
    if v == "PARTIALLY TRUE":   return "#c8a040"
    return "#7a7a7a"

def overall_score(results: list) -> int:
    if not results:
        return 0
    weights = {"TRUE": 100, "PARTIALLY TRUE": 50, "FALSE": 0, "UNVERIFIABLE": 50}
    scores = [weights.get(r.get("verdict", "UNVERIFIABLE").upper(), 50) *
              (r.get("confidence", 50) / 100) for r in results]
    return round(sum(scores) / len(scores))
