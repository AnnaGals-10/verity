from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from scorer import score_source
import json

llm    = ChatOpenAI(model="gpt-4o-mini", temperature=0)
search = TavilySearchResults(max_results=5)

def _clean_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return text.strip()

def verify_claim(claim: str, context: str = "", language: str = "English") -> dict:
    # 1. Search for evidence
    try:
        raw = search.invoke(f"fact check: {claim}")
    except Exception:
        raw = []

    sources, evidence_text = [], ""
    for r in raw:
        url     = r.get("url", "")
        content = r.get("content", "")
        src     = score_source(url)
        sources.append({
            "url":               url,
            "domain":            src["domain"],
            "credibility_score": src["score"],
            "tier":              src["tier"],
            "snippet":           content[:250],
        })
        evidence_text += f"Source [{src['domain']} — credibility {src['score']}/100]:\n{content}\n\n"

    # 2. LLM analysis
    prompt = (
        f"You are a senior fact-checker. Reply exclusively in {language}.\n\n"
        f'Claim to verify: "{claim}"\n'
        f'Context: "{context}"\n\n'
        f"Evidence:\n{evidence_text or 'No external sources found.'}\n\n"
        "Based on the evidence (weight sources by credibility score), provide:\n"
        '- verdict: "TRUE", "FALSE", "PARTIALLY TRUE", or "UNVERIFIABLE"\n'
        "- confidence: 0-100\n"
        "- explanation: 2-3 sentences citing specific sources\n"
        "- sources_used: list of URLs that supported your verdict\n\n"
        'Return ONLY a JSON object: '
        '{"verdict": "...", "confidence": <n>, "explanation": "...", "sources_used": ["..."]}'
    )
    raw_result = llm.invoke(prompt).content
    try:
        analysis = json.loads(_clean_json(raw_result))
    except Exception:
        analysis = {"verdict": "UNVERIFIABLE", "confidence": 0,
                    "explanation": "Could not analyze this claim.", "sources_used": []}

    return {
        "claim":        claim,
        "context":      context,
        "verdict":      analysis.get("verdict", "UNVERIFIABLE"),
        "confidence":   analysis.get("confidence", 0),
        "explanation":  analysis.get("explanation", ""),
        "sources":      sources,
        "sources_used": analysis.get("sources_used", []),
    }

def verify_all_claims(claims: list, language: str = "English") -> list:
    return [verify_claim(c["claim"], c.get("context", ""), language) for c in claims]
