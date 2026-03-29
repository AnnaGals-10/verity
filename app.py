import streamlit as st
import os, sys, json
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from extractor import extract_claims, extract_text_from_pdf, extract_text_from_url, detect_language
from verifier import verify_all_claims
from comparator import compare_documents
from report_generator import generate_report
from scorer import overall_score, verdict_color, tier

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "history.json")
UPLOADS_DIR  = os.path.join(os.path.dirname(__file__), "uploads")

st.set_page_config(page_title="Lexis Verify", page_icon="◎",
                   layout="wide", initial_sidebar_state="collapsed")

# ── Session state ─────────────────────────────────────────────────────────────
for key, val in [("results", None), ("language", "English"), ("input_title", ""),
                 ("compare_a", None), ("compare_b", None), ("comparison", None)]:
    if key not in st.session_state:
        st.session_state[key] = val

# ── History ───────────────────────────────────────────────────────────────────
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, encoding="utf-8") as f: return json.load(f)
    return []

def save_history(title, results, language):
    h = load_history()
    n = len(results)
    h.insert(0, {
        "title": title, "date": datetime.now().strftime("%d %b %Y %H:%M"),
        "language": language, "n_claims": n,
        "score": overall_score(results),
        "true": sum(1 for r in results if r["verdict"].upper() == "TRUE"),
        "false": sum(1 for r in results if r["verdict"].upper() == "FALSE"),
        "partial": sum(1 for r in results if r["verdict"].upper() == "PARTIALLY TRUE"),
        "results": results,
    })
    with open(HISTORY_FILE, "w", encoding="utf-8") as f: json.dump(h[:30], f, ensure_ascii=False, indent=2)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;1,9..40,300&family=DM+Serif+Display:ital@0;1&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; background: #080808; color: #f0ece4; }
.block-container { padding: 3rem 3.5rem 4rem; max-width: 1280px; }
#MainMenu, footer, header { visibility: hidden; }
[data-testid="collapsedControl"], [data-testid="collapsedControl"] * { visibility: visible !important; }

/* Nav */
.nav { display:flex; justify-content:space-between; align-items:center;
       padding-bottom:2.5rem; border-bottom:1px solid #181818; margin-bottom:3.5rem; }
.nav-logo { font-family:'DM Serif Display',serif; font-size:1.35rem; color:#f0ece4; letter-spacing:-0.5px; }
.nav-logo span { color:#c8a882; font-style:italic; }
.nav-tag { font-size:0.7rem; font-weight:500; letter-spacing:2.5px; text-transform:uppercase; color:#3a3a3a; }

/* Hero */
.hero-eyebrow { font-size:0.7rem; letter-spacing:3px; text-transform:uppercase; color:#3a3a3a; margin-bottom:1.25rem; }
.hero-title { font-family:'DM Serif Display',serif; font-size:clamp(2.4rem,4.5vw,3.8rem);
              line-height:1.1; color:#f0ece4; letter-spacing:-1px; margin-bottom:1.5rem; }
.hero-title em { color:#c8a882; font-style:italic; }
.hero-sub { font-size:0.95rem; font-weight:300; color:#4a4a4a; line-height:1.75; max-width:380px; }

/* Divider */
.div { border:none; border-top:1px solid #181818; margin:3rem 0; }

/* Labels */
.lbl { font-size:0.78rem; font-weight:500; letter-spacing:2.5px;
       text-transform:uppercase; color:#5a5a5a; margin-bottom:1.75rem; }

/* Score block */
.score-block { padding:1.75rem 0; border-top:1px solid #181818; border-bottom:1px solid #181818; }
.score-num { font-family:'DM Serif Display',serif; font-size:5rem; line-height:1;
             font-weight:400; letter-spacing:-3px; }
.score-den { font-size:1.3rem; color:#3a3a3a; }
.score-cap { font-size:0.7rem; letter-spacing:2px; text-transform:uppercase; color:#3a3a3a; margin-top:0.5rem; }

/* Stats row */
.stat { padding:1.5rem 0; border-bottom:1px solid #181818; }
.stat-lbl { font-size:0.7rem; letter-spacing:2px; text-transform:uppercase; color:#5a5a5a; margin-bottom:0.4rem; }
.stat-val { font-size:0.95rem; font-weight:400; color:#f0ece4; }

/* Claim card */
.claim { padding:1.5rem 0; border-bottom:1px solid #181818; }
.claim-header { display:flex; justify-content:space-between; align-items:flex-start; gap:1rem; margin-bottom:0.6rem; }
.claim-text { font-size:0.95rem; font-weight:500; color:#f0ece4; line-height:1.45; }
.claim-verdict { font-size:0.7rem; font-weight:600; letter-spacing:2px; text-transform:uppercase; white-space:nowrap; }
.claim-conf { font-size:0.72rem; color:#3a3a3a; margin-top:2px; text-align:right; }
.claim-ctx { font-size:0.82rem; font-style:italic; color:#3a3a3a; margin-bottom:0.6rem; }
.claim-exp { font-size:0.85rem; font-weight:300; color:#5a5a5a; line-height:1.65; margin-bottom:0.75rem; }
.claim-sources { display:flex; flex-wrap:wrap; gap:6px; margin-top:0.5rem; }
.source-pill { font-size:0.72rem; background:#0f0f0f; border:1px solid #1e1e1e;
               border-radius:2px; padding:3px 10px; color:#5a5a5a; white-space:nowrap; }
.source-pill.high { color:#6ab187; border-color:#1a2e1f; }
.source-pill.mid  { color:#c8a040; border-color:#2a2010; }

/* Contradiction */
.contra { padding:1.25rem; background:#0d0808; border:1px solid #2a1010;
          border-radius:2px; margin-bottom:10px; }
.contra-lbl { font-size:0.68rem; letter-spacing:2px; text-transform:uppercase; color:#c0726a; margin-bottom:8px; }
.agree { padding:1.25rem; background:#080d09; border:1px solid #0f2a14;
         border-radius:2px; margin-bottom:10px; }
.agree-lbl { font-size:0.68rem; letter-spacing:2px; text-transform:uppercase; color:#6ab187; margin-bottom:8px; }
.cmp-text { font-size:0.85rem; font-weight:300; color:#7a7a7a; line-height:1.6; }
.cmp-exp { font-size:0.82rem; font-style:italic; color:#3a3a3a; margin-top:6px; }

/* History row */
.hist { padding:1rem 0; border-bottom:1px solid #161616; }
.hist-title { font-size:0.88rem; font-weight:500; color:#f0ece4; margin-bottom:4px; }
.hist-meta { font-size:0.72rem; color:#3a3a3a; }

/* Buttons */
.stButton > button { background:#0c0c0c; border:1px solid #242424; color:#c8a882;
    font-size:0.72rem; letter-spacing:1.5px; text-transform:uppercase;
    padding:0.5rem 1.25rem; border-radius:2px; font-family:'DM Sans',sans-serif; }
.stButton > button:hover { border-color:#c8a882; }

/* Tabs */
[data-testid="stTabs"] button { font-size:0.75rem; letter-spacing:1.5px; text-transform:uppercase; color:#3a3a3a; }
[data-testid="stTabs"] button[aria-selected="true"] { color:#f0ece4; border-bottom-color:#c8a882; }
[data-testid="stTabs"] { border-bottom:1px solid #181818; }

/* Upload */
[data-testid="stFileUploaderDropzone"] { background:#080808 !important; border:1px dashed #222 !important; border-radius:2px !important; }
[data-testid="stFileUploaderDropzone"]:hover { border-color:#c8a882 !important; }

/* Progress */
.stProgress > div > div > div > div { background:#c8a882 !important; }
.stProgress > div > div > div { background:#181818 !important; }

/* Text area */
.stTextArea textarea { background:#0c0c0c !important; border:1px solid #222 !important;
    color:#f0ece4 !important; font-size:0.88rem !important; border-radius:2px !important; }
</style>
""", unsafe_allow_html=True)

# ── Nav ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="nav">
  <div class="nav-logo">Lexis <span>Verify</span></div>
  <div class="nav-tag">AI Fact-Checking</div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_verify, tab_compare, tab_history = st.tabs(["Verify", "Compare", "History"])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — VERIFY
# ═══════════════════════════════════════════════════════════════════════════════
with tab_verify:
    col_hero, col_input = st.columns([1, 1], gap="large")

    with col_hero:
        st.markdown("""
        <div class="hero-eyebrow">AI Fact-Checking</div>
        <div class="hero-title">Verify what's true,<br>with <em>certainty.</em></div>
        <div class="hero-sub">
            Extract every verifiable claim from any document,
            cross-reference against trusted sources, and get
            a credibility score backed by evidence.
        </div>
        """, unsafe_allow_html=True)

    with col_input:
        input_mode = st.radio("Input", ["PDF", "Text", "URL", "Multiple PDFs"],
                              horizontal=True, label_visibility="collapsed")
        st.markdown('<div style="margin-top:1rem;"></div>', unsafe_allow_html=True)

        input_text, input_files = "", []

        if input_mode == "PDF":
            f = st.file_uploader("Upload PDF", type=["pdf"], label_visibility="collapsed")
            if f: input_files = [f]

        elif input_mode == "URL":
            input_text = st.text_input("Article URL", placeholder="https://...",
                                       label_visibility="collapsed")

        elif input_mode == "Multiple PDFs":
            fs = st.file_uploader("Upload PDFs", type=["pdf"],
                                   accept_multiple_files=True, label_visibility="collapsed")
            if fs: input_files = fs

        else:
            input_text = st.text_area("Paste text to verify", height=200,
                                       placeholder="Paste any text here...",
                                       label_visibility="collapsed")

        run = st.button("Analyze")

    # ── Run analysis ──────────────────────────────────────────────────────────
    if run and (input_files or input_text.strip()):
        all_results, all_text, title = [], "", ""

        if input_files:
            texts = []
            for f in input_files:
                path = os.path.join(UPLOADS_DIR, f.name)
                with open(path, "wb") as fout: fout.write(f.read())
                texts.append(extract_text_from_pdf(path))
                os.remove(path)
            all_text = " ".join(texts)
            title = ", ".join(f.name for f in input_files)
        elif input_mode == "URL" and input_text.strip():
            try:
                all_text, title = extract_text_from_url(input_text.strip())
            except ValueError as e:
                st.error(str(e))
                st.stop()
        else:
            all_text = input_text
            title = "Pasted text"

        with st.spinner(""):
            prog = st.progress(0, text="Detecting language...")
            lang = detect_language(all_text)
            st.session_state.language = lang

            prog.progress(15, text="Extracting claims...")
            claims = extract_claims(all_text)

            if not claims:
                st.warning("No verifiable claims found in this document.")
                prog.empty()
            else:
                results = []
                for i, c in enumerate(claims):
                    pct = 15 + int(80 * (i + 1) / len(claims))
                    prog.progress(pct, text=f"Verifying claim {i+1} of {len(claims)}...")
                    from verifier import verify_claim
                    results.append(verify_claim(c["claim"], c.get("context", ""), lang))

                prog.progress(100, text="Done.")
                prog.empty()
                st.session_state.results = results
                st.session_state.input_title = title
                save_history(title, results, lang)

    # ── Results ───────────────────────────────────────────────────────────────
    if st.session_state.results:
        results = st.session_state.results
        lang    = st.session_state.language
        title   = st.session_state.input_title
        score   = overall_score(results)
        n       = len(results)
        true_n  = sum(1 for r in results if r["verdict"].upper() == "TRUE")
        false_n = sum(1 for r in results if r["verdict"].upper() == "FALSE")
        part_n  = sum(1 for r in results if r["verdict"].upper() == "PARTIALLY TRUE")
        unv_n   = n - true_n - false_n - part_n

        st.markdown('<hr class="div">', unsafe_allow_html=True)

        # Action bar
        _, exp_col = st.columns([4, 1])
        with exp_col:
            if st.button("Export PDF"):
                buf = generate_report(title, results, lang)
                st.download_button("Download report", data=buf,
                    file_name=f"lexis_verify_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf")

        st.markdown('<hr class="div">', unsafe_allow_html=True)

        # Overview row
        score_col_val = "#6ab187" if score >= 70 else "#c8a040" if score >= 40 else "#c0726a"
        c1, c2, c3 = st.columns([1, 2, 2], gap="large")

        with c1:
            st.markdown(f"""
            <div class="lbl">Credibility</div>
            <div class="score-block">
              <div class="score-num" style="color:{score_col_val};">{score}<span class="score-den">/100</span></div>
              <div class="score-cap">Overall score</div>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div class="lbl">Breakdown</div>
            <div class="stat"><div class="stat-lbl">True</div>
              <div class="stat-val" style="color:#6ab187;">{true_n} claim{"s" if true_n!=1 else ""}</div></div>
            <div class="stat"><div class="stat-lbl">False</div>
              <div class="stat-val" style="color:#c0726a;">{false_n} claim{"s" if false_n!=1 else ""}</div></div>
            <div class="stat"><div class="stat-lbl">Partially true</div>
              <div class="stat-val" style="color:#c8a040;">{part_n} claim{"s" if part_n!=1 else ""}</div></div>
            <div class="stat"><div class="stat-lbl">Unverifiable</div>
              <div class="stat-val" style="color:#5a5a5a;">{unv_n} claim{"s" if unv_n!=1 else ""}</div></div>
            """, unsafe_allow_html=True)

        with c3:
            st.markdown(f"""
            <div class="lbl">Document</div>
            <div class="stat"><div class="stat-lbl">Title</div>
              <div class="stat-val">{title}</div></div>
            <div class="stat"><div class="stat-lbl">Language</div>
              <div class="stat-val">{lang}</div></div>
            <div class="stat"><div class="stat-lbl">Claims analyzed</div>
              <div class="stat-val">{n}</div></div>
            """, unsafe_allow_html=True)

        st.markdown('<hr class="div">', unsafe_allow_html=True)
        st.markdown(f'<div class="lbl">Verified claims ({n})</div>', unsafe_allow_html=True)

        for r in results:
            verdict = r.get("verdict", "UNVERIFIABLE").upper()
            conf    = r.get("confidence", 0)
            vc      = verdict_color(verdict)

            sources_html = ""
            for s in r.get("sources", [])[:4]:
                if s.get("domain") and s["domain"] != "—":
                    sc = s.get("credibility_score", 0)
                    cls = "high" if sc >= 75 else "mid" if sc >= 50 else ""
                    sources_html += f'<span class="source-pill {cls}">{s["domain"]} · {sc}</span>'

            ctx_html = f'<div class="claim-ctx">Context: {r["context"]}</div>' if r.get("context") else ""
            src_html = f'<div class="claim-sources">{sources_html}</div>' if sources_html else ""

            st.markdown(f"""
            <div class="claim">
              <div class="claim-header">
                <div class="claim-text">{r["claim"]}</div>
                <div>
                  <div class="claim-verdict" style="color:{vc};">{verdict}</div>
                  <div class="claim-conf">{conf}% confidence</div>
                </div>
              </div>
              {ctx_html}
              <div class="claim-exp">{r.get("explanation","")}</div>
              {src_html}
            </div>
            """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — COMPARE
# ═══════════════════════════════════════════════════════════════════════════════
with tab_compare:
    st.markdown("""
    <div style="margin-bottom:2.5rem;">
      <div class="hero-eyebrow">Comparison Mode</div>
      <div class="hero-title" style="font-size:2rem;">Two documents,<br>one <em>truth.</em></div>
    </div>
    """, unsafe_allow_html=True)

    ca_col, cb_col = st.columns(2, gap="large")

    with ca_col:
        st.markdown('<div class="lbl">Document A</div>', unsafe_allow_html=True)
        mode_a = st.radio("Input A", ["PDF", "Text"], horizontal=True,
                          label_visibility="collapsed", key="mode_a")
        if mode_a == "PDF":
            fa = st.file_uploader("Doc A", type=["pdf"], label_visibility="collapsed", key="fa")
        else:
            fa = st.text_area("Text A", height=150, label_visibility="collapsed",
                              placeholder="Paste text A...", key="ta")

    with cb_col:
        st.markdown('<div class="lbl">Document B</div>', unsafe_allow_html=True)
        mode_b = st.radio("Input B", ["PDF", "Text"], horizontal=True,
                          label_visibility="collapsed", key="mode_b")
        if mode_b == "PDF":
            fb = st.file_uploader("Doc B", type=["pdf"], label_visibility="collapsed", key="fb")
        else:
            fb = st.text_area("Text B", height=150, label_visibility="collapsed",
                              placeholder="Paste text B...", key="tb")

    cmp_btn = st.button("Compare documents")

    if cmp_btn:
        def get_text(mode, f):
            if mode == "PDF" and f:
                path = os.path.join(UPLOADS_DIR, f.name)
                with open(path, "wb") as fout: fout.write(f.read())
                t = extract_text_from_pdf(path)
                os.remove(path)
                return t
            elif mode == "Text" and f and f.strip():
                return f
            return ""

        text_a = get_text(mode_a, fa)
        text_b = get_text(mode_b, fb)

        if text_a and text_b:
            with st.spinner("Analyzing and comparing..."):
                lang = detect_language(text_a)
                claims_a = extract_claims(text_a)
                claims_b = extract_claims(text_b)
                results_a = verify_all_claims(claims_a, lang)
                results_b = verify_all_claims(claims_b, lang)
                comparison = compare_documents(results_a, results_b, lang)
                st.session_state.compare_a   = results_a
                st.session_state.compare_b   = results_b
                st.session_state.comparison  = comparison
        else:
            st.warning("Please provide both documents.")

    if st.session_state.comparison:
        cmp = st.session_state.comparison
        st.markdown('<hr class="div">', unsafe_allow_html=True)

        contras = cmp.get("contradictions", [])
        agrees  = cmp.get("agreements", [])
        uniq_a  = cmp.get("unique_a", [])
        uniq_b  = cmp.get("unique_b", [])

        st.markdown(f'<div class="lbl">Contradictions ({len(contras)})</div>', unsafe_allow_html=True)
        if not contras:
            st.markdown('<div style="color:#3a3a3a;font-size:0.85rem;padding:1rem 0;">No direct contradictions found.</div>', unsafe_allow_html=True)
        for c in contras:
            st.markdown(f"""
            <div class="contra">
              <div class="contra-lbl">Contradiction</div>
              <div class="cmp-text"><b>A:</b> {c.get("claim_a","")}</div>
              <div class="cmp-text" style="margin-top:6px;"><b>B:</b> {c.get("claim_b","")}</div>
              <div class="cmp-exp">{c.get("explanation","")}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f'<div class="lbl" style="margin-top:2rem;">Agreements ({len(agrees)})</div>', unsafe_allow_html=True)
        for a in agrees:
            st.markdown(f"""
            <div class="agree">
              <div class="agree-lbl">Agreement</div>
              <div class="cmp-text"><b>A:</b> {a.get("claim_a","")}</div>
              <div class="cmp-text" style="margin-top:6px;"><b>B:</b> {a.get("claim_b","")}</div>
              <div class="cmp-exp">{a.get("explanation","")}</div>
            </div>
            """, unsafe_allow_html=True)

        if uniq_a or uniq_b:
            u1, u2 = st.columns(2, gap="large")
            with u1:
                st.markdown(f'<div class="lbl">Only in A ({len(uniq_a)})</div>', unsafe_allow_html=True)
                for u in uniq_a:
                    st.markdown(f'<div class="claim"><div class="claim-text" style="font-weight:300;color:#5a5a5a;">{u}</div></div>', unsafe_allow_html=True)
            with u2:
                st.markdown(f'<div class="lbl">Only in B ({len(uniq_b)})</div>', unsafe_allow_html=True)
                for u in uniq_b:
                    st.markdown(f'<div class="claim"><div class="claim-text" style="font-weight:300;color:#5a5a5a;">{u}</div></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — HISTORY
# ═══════════════════════════════════════════════════════════════════════════════
with tab_history:
    st.markdown("""
    <div style="margin-bottom:2.5rem;">
      <div class="hero-eyebrow">Analysis history</div>
      <div class="hero-title" style="font-size:2rem;">Past <em>verifications.</em></div>
    </div>
    """, unsafe_allow_html=True)

    history = load_history()
    if not history:
        st.markdown('<div style="color:#3a3a3a;font-size:0.88rem;padding:2rem 0;">No analyses yet.</div>', unsafe_allow_html=True)
    else:
        # Summary stats
        avg_score = round(sum(h["score"] for h in history) / len(history))
        total_claims = sum(h["n_claims"] for h in history)
        st.markdown(f"""
        <div style="display:flex;gap:4rem;padding:1.5rem 0;border-bottom:1px solid #181818;margin-bottom:2rem;">
          <div><div class="stat-lbl">Analyses</div><div style="font-size:1.5rem;font-family:'DM Serif Display',serif;color:#f0ece4;">{len(history)}</div></div>
          <div><div class="stat-lbl">Claims verified</div><div style="font-size:1.5rem;font-family:'DM Serif Display',serif;color:#f0ece4;">{total_claims}</div></div>
          <div><div class="stat-lbl">Avg credibility</div><div style="font-size:1.5rem;font-family:'DM Serif Display',serif;color:#c8a882;">{avg_score}/100</div></div>
        </div>
        """, unsafe_allow_html=True)

        for h in history:
            score = h.get("score", 0)
            sc = "#6ab187" if score >= 70 else "#c8a040" if score >= 40 else "#c0726a"
            st.markdown(f"""
            <div class="hist">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <div class="hist-title">{h.get("title","—")}</div>
                <div style="font-size:1.1rem;font-family:'DM Serif Display',serif;color:{sc};">{score}/100</div>
              </div>
              <div style="display:flex;gap:1.5rem;margin-top:4px;">
                <span class="hist-meta">{h.get("date","")}</span>
                <span class="hist-meta">{h.get("language","")}</span>
                <span class="hist-meta">{h.get("n_claims",0)} claims</span>
                <span style="font-size:0.72rem;color:#6ab187;">{h.get("true",0)} true</span>
                <span style="font-size:0.72rem;color:#c0726a;">{h.get("false",0)} false</span>
                <span style="font-size:0.72rem;color:#c8a040;">{h.get("partial",0)} partial</span>
              </div>
            </div>
            """, unsafe_allow_html=True)
