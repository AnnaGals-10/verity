"""Module for extracting claims and facts from documents."""
from langchain_openai import ChatOpenAI
import json
import trafilatura

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def _clean_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return text.strip()

def detect_language(text: str) -> str:
    result = llm.invoke(
        f"What language is this text written in? Reply with only the language name in English "
        f"(e.g. 'Spanish', 'Catalan', 'English'). Text: {text[:300]}"
    ).content.strip()
    return result

def extract_claims(text: str) -> list:
    prompt = (
        "You are a fact-checking analyst. Extract ALL verifiable factual claims from the text below.\n"
        "Ignore opinions, predictions, and subjective statements.\n"
        "Only extract objective claims that can be verified with external sources.\n\n"
        f"Text:\n{text}\n\n"
        'Return ONLY a JSON array: [{"claim": "the factual claim", "context": "brief context"}]'
    )
    result = llm.invoke(prompt).content
    try:
        return json.loads(_clean_json(result))
    except Exception:
        return []

def extract_text_from_pdf(pdf_path: str) -> str:
    from langchain_community.document_loaders import PyPDFLoader
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    return " ".join([d.page_content for d in docs])

def extract_text_from_url(url: str) -> tuple[str, str]:
    """Returns (text, title) from a URL."""
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        raise ValueError(f"Could not fetch content from: {url}")
    text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
    metadata = trafilatura.extract_metadata(downloaded)
    title = metadata.title if metadata and metadata.title else url
    if not text:
        raise ValueError(f"Could not extract text from: {url}")
    return text, title
