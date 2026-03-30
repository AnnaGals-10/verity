"""Module for comparing and analyzing semantic similarity between documents."""
from langchain_openai import ChatOpenAI
import json

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def _clean_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return text.strip()

def compare_documents(results_a: list, results_b: list, language: str = "English") -> dict:
    claims_a = [{"claim": r["claim"], "verdict": r["verdict"]} for r in results_a]
    claims_b = [{"claim": r["claim"], "verdict": r["verdict"]} for r in results_b]

    prompt = (
        f"You are a senior fact-checker. Reply exclusively in {language}.\n"
        "Compare these two sets of claims from different documents and identify:\n"
        "1. Direct contradictions — claims that say opposite things\n"
        "2. Agreements — claims that reinforce each other\n"
        "3. Unique claims in document A not covered by B\n"
        "4. Unique claims in document B not covered by A\n\n"
        f"Document A:\n{json.dumps(claims_a, ensure_ascii=False)}\n\n"
        f"Document B:\n{json.dumps(claims_b, ensure_ascii=False)}\n\n"
        'Return ONLY a JSON object:\n'
        '{"contradictions": [{"claim_a": "...", "claim_b": "...", "explanation": "..."}], '
        '"agreements": [{"claim_a": "...", "claim_b": "...", "explanation": "..."}], '
        '"unique_a": ["..."], "unique_b": ["..."]}'
    )
    result = llm.invoke(prompt).content
    try:
        return json.loads(_clean_json(result))
    except Exception:
        return {"contradictions": [], "agreements": [], "unique_a": [], "unique_b": []}
