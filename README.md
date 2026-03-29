# Lexis Verify

AI-powered fact-checking platform. Extract every verifiable claim from any document, cross-reference against trusted sources, and get a credibility score backed by evidence.

## Features

- **Claim extraction** — automatically identifies all verifiable factual claims from any input
- **Source credibility scoring** — rates sources from wire services (Reuters 95/100) to social media (Reddit 20/100)
- **Multi-format input** — PDF, plain text, article URL, or multiple PDFs at once
- **Language detection** — works in any language, responds in the document's language
- **Comparison mode** — upload two documents and find contradictions and agreements between their claims
- **PDF report export** — download a professional report with all claims, verdicts and sources
- **History dashboard** — track all past analyses with credibility trends
- **REST API** — integrate fact-checking into any external system

## Verdicts

| Verdict | Meaning |
|---|---|
| **TRUE** | Supported by credible sources |
| **FALSE** | Contradicted by credible sources |
| **PARTIALLY TRUE** | Some aspects confirmed, others not |
| **UNVERIFIABLE** | Insufficient evidence found |

## Setup

**1. Clone the repo**
```bash
git clone https://github.com/AnnaGals-10/lexis-verify.git
cd lexis-verify
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Configure API keys**
```bash
cp .env.example .env
```
Edit `.env` and add your keys:
- `OPENAI_API_KEY` — from [platform.openai.com](https://platform.openai.com)
- `TAVILY_API_KEY` — from [tavily.com](https://tavily.com) (free tier available)

**4. Run the app**
```bash
python -m streamlit run app.py
```

## API

Run the REST API with:
```bash
uvicorn api:app --reload
```

### Endpoints

```
GET  /                    Health check
POST /verify/text         Verify claims from plain text
POST /verify/pdf          Verify claims from a PDF file
```

**Example — verify text:**
```bash
curl -X POST http://localhost:8000/verify/text \
  -H "Content-Type: application/json" \
  -d '{"text": "The Eiffel Tower was built in 1889 and is located in Berlin."}'
```

**Response:**
```json
{
  "language": "English",
  "n_claims": 2,
  "overall_score": 45,
  "results": [
    {
      "claim": "The Eiffel Tower was built in 1889",
      "verdict": "TRUE",
      "confidence": 99,
      "explanation": "..."
    },
    {
      "claim": "The Eiffel Tower is located in Berlin",
      "verdict": "FALSE",
      "confidence": 98,
      "explanation": "..."
    }
  ]
}
```

## Project structure

```
fact-checker/
├── app.py              — Streamlit UI
├── extractor.py        — Claim extraction from text, PDF and URLs
├── verifier.py         — Claim verification via Tavily + LLM
├── comparator.py       — Document comparison logic
├── scorer.py           — Source credibility scoring
├── report_generator.py — PDF report export
├── api.py              — FastAPI REST endpoints
├── requirements.txt
├── .env.example
└── uploads/            — Temporary upload directory (gitignored)
```

## Source credibility tiers

| Tier | Score | Examples |
|---|---|---|
| Highly Trusted | 90–99 | Reuters, AP, Nature, WHO, CDC |
| Trusted | 75–89 | BBC, NYT, Guardian, Economist |
| Moderate | 60–74 | Wikipedia, regional outlets |
| Low | 40–59 | Unknown .org domains |
| Unreliable | 0–39 | Reddit, Facebook, anonymous blogs |
