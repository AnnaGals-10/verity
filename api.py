"""
Verity AI API — FastAPI endpoints
Run: uvicorn api:app --reload
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, sys, tempfile

sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from extractor import extract_claims, extract_text_from_pdf, detect_language
from verifier import verify_all_claims
from scorer import overall_score

app = FastAPI(title="Verity AI API", version="1.0.0",
              description="AI-powered fact-checking API")

app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

class TextRequest(BaseModel):
    text: str
    language: str = "auto"

@app.get("/")
def root():
    return {"name": "Verity AI API", "version": "1.0.0", "status": "ok"}

@app.post("/verify/text")
def verify_text(req: TextRequest):
    lang = detect_language(req.text) if req.language == "auto" else req.language
    claims = extract_claims(req.text)
    if not claims:
        raise HTTPException(422, "No verifiable claims found in the provided text.")
    results = verify_all_claims(claims, lang)
    return {
        "language": lang,
        "n_claims": len(results),
        "overall_score": overall_score(results),
        "results": results,
    }

@app.post("/verify/pdf")
def verify_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported.")
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name
    try:
        text = extract_text_from_pdf(tmp_path)
        lang = detect_language(text)
        claims = extract_claims(text)
        if not claims:
            raise HTTPException(422, "No verifiable claims found in the PDF.")
        results = verify_all_claims(claims, lang)
        return {
            "filename": file.filename,
            "language": lang,
            "n_claims": len(results),
            "overall_score": overall_score(results),
            "results": results,
        }
    finally:
        os.remove(tmp_path)
