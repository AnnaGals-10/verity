from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from scorer import verdict_color, overall_score
import io
from datetime import datetime

def _s(name, **kw):
    s = ParagraphStyle(name, fontName="Helvetica", fontSize=10,
                       textColor=colors.HexColor("#1a1a1a"), leading=16)
    for k, v in kw.items(): setattr(s, k, v)
    return s

S = {
    "logo":    _s("logo", fontSize=11, fontName="Helvetica-Bold"),
    "eye":     _s("eye",  fontSize=8,  textColor=colors.HexColor("#aaaaaa"), spaceAfter=4),
    "title":   _s("ttl",  fontSize=20, fontName="Helvetica-Bold", spaceAfter=4, leading=26),
    "meta":    _s("meta", fontSize=9,  textColor=colors.HexColor("#888888"), spaceAfter=16),
    "sec":     _s("sec",  fontSize=8,  fontName="Helvetica-Bold",
                  textColor=colors.HexColor("#888888"), spaceAfter=10, leading=12),
    "body":    _s("body", fontSize=10, spaceAfter=6, leading=16),
    "small":   _s("sml",  fontSize=9,  textColor=colors.HexColor("#555555"), leading=14, spaceAfter=4),
    "italic":  _s("itl",  fontSize=9,  fontName="Helvetica-Oblique",
                  textColor=colors.HexColor("#888888"), leading=14, leftIndent=10),
    "footer":  _s("ftr",  fontSize=8,  textColor=colors.HexColor("#bbbbbb"), alignment=TA_CENTER),
}

HR  = lambda: HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e0e0e0"), spaceAfter=10)
HRt = lambda: HRFlowable(width="100%", thickness=0.3, color=colors.HexColor("#f0f0f0"), spaceAfter=6)
SP  = lambda h=0.4: Spacer(1, h * cm)

def generate_report(title: str, results: list, language: str = "English") -> io.BytesIO:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=2.5*cm, rightMargin=2.5*cm,
                            topMargin=2.5*cm, bottomMargin=2.5*cm)
    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph("LEXIS VERIFY", S["logo"]))
    story.append(Paragraph("Fact-Checking Report", S["eye"]))
    story.append(HR())
    story.append(SP(0.2))
    story.append(Paragraph(title, S["title"]))
    story.append(Paragraph(
        f"Generated {datetime.now().strftime('%B %d, %Y at %H:%M')}  ·  Language: {language}",
        S["meta"]
    ))

    # ── Overview ──────────────────────────────────────────────────────────────
    score  = overall_score(results)
    n      = len(results)
    true_n = sum(1 for r in results if r["verdict"].upper() == "TRUE")
    false_n= sum(1 for r in results if r["verdict"].upper() == "FALSE")
    part_n = sum(1 for r in results if r["verdict"].upper() == "PARTIALLY TRUE")
    unv_n  = n - true_n - false_n - part_n

    score_hex = "4a7c59" if score >= 70 else "c8a040" if score >= 40 else "c0726a"

    ov = [[
        Paragraph("CREDIBILITY SCORE", S["sec"]),
        Paragraph("CLAIMS", S["sec"]),
        Paragraph("BREAKDOWN", S["sec"]),
    ], [
        Paragraph(f"<font size='28' color='#{score_hex}'><b>{score}</b></font><font size='14' color='#aaaaaa'>/100</font>", S["body"]),
        Paragraph(f"<b>{n}</b> total", S["body"]),
        Paragraph(
            f"<font color='#4a7c59'>✓ {true_n} true</font>  "
            f"<font color='#c0726a'>✗ {false_n} false</font>  "
            f"<font color='#c8a040'>~ {part_n} partial</font>  "
            f"<font color='#7a7a7a'>? {unv_n} unverifiable</font>",
            S["body"]
        ),
    ]]
    tbl = Table(ov, colWidths=[4*cm, 3.5*cm, 9*cm])
    tbl.setStyle(TableStyle([
        ("VALIGN",       (0,0), (-1,-1), "TOP"),
        ("LINEBELOW",    (0,0), (-1,0),  0.5, colors.HexColor("#e0e0e0")),
        ("LINEBELOW",    (0,1), (-1,1),  0.5, colors.HexColor("#e0e0e0")),
        ("TOPPADDING",   (0,0), (-1,-1), 8),
        ("BOTTOMPADDING",(0,0), (-1,-1), 8),
    ]))
    story.append(tbl)
    story.append(SP(0.6))

    # ── Claims ────────────────────────────────────────────────────────────────
    story.append(Paragraph("VERIFIED CLAIMS", S["sec"]))
    story.append(HR())

    for i, r in enumerate(results):
        verdict = r.get("verdict", "UNVERIFIABLE").upper()
        conf    = r.get("confidence", 0)
        vc      = verdict_color(verdict).lstrip("#")

        row = [[
            Paragraph(f"{i+1}. {r['claim']}", _s(f"cl{i}", fontSize=10, fontName="Helvetica-Bold")),
            Paragraph(
                f"<font color='#{vc}'><b>{verdict}</b></font>  <font color='#aaaaaa'>{conf}%</font>",
                ParagraphStyle(f"vd{i}", fontSize=9, fontName="Helvetica-Bold", alignment=TA_RIGHT)
            )
        ]]
        t = Table(row, colWidths=[12.5*cm, 4*cm])
        t.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP")]))
        story.append(t)

        if r.get("context"):
            story.append(Paragraph(f'Context: {r["context"]}', S["italic"]))
        story.append(Paragraph(r.get("explanation", ""), S["small"]))

        # Sources
        used = set(r.get("sources_used", []))
        src_line = "  ·  ".join(
            f"{s['domain']} ({s['credibility_score']})"
            for s in r.get("sources", [])
            if s.get("domain") and s["domain"] != "—"
        )
        if src_line:
            story.append(Paragraph(f"Sources: {src_line}", S["italic"]))

        story.append(HRt())
        story.append(SP(0.15))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(SP(0.8))
    story.append(HR())
    story.append(Paragraph(
        "Generated by Lexis Verify · For informational purposes only · Not a substitute for professional fact-checking.",
        S["footer"]
    ))

    doc.build(story)
    buf.seek(0)
    return buf
