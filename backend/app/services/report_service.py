"""PDF Report generation service."""
from __future__ import annotations
import io
import base64
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER


DARK_BG = HexColor("#0f172a")
ACCENT = HexColor("#3b82f6")
TEXT = HexColor("#1e293b")
LIGHT_TEXT = HexColor("#64748b")
WHITE = HexColor("#ffffff")
GREEN = HexColor("#22c55e")
YELLOW = HexColor("#eab308")
RED = HexColor("#ef4444")


def _priority_color(p: str):
    return {"LOW": GREEN, "MEDIUM": YELLOW, "HIGH": RED}.get(p.upper(), LIGHT_TEXT)


async def generate_report(
    query: str,
    analysis: dict,
    image_name: str = "",
    heatmap_b64: str = "",
) -> bytes:
    """Generate a PDF report. Returns raw PDF bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm, leftMargin=20*mm, rightMargin=20*mm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title2", parent=styles["Title"], fontSize=22, textColor=ACCENT, spaceAfter=6*mm)
    subtitle_style = ParagraphStyle("Sub", parent=styles["Normal"], fontSize=11, textColor=LIGHT_TEXT, spaceAfter=4*mm)
    heading_style = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=14, textColor=TEXT, spaceBefore=6*mm, spaceAfter=3*mm)
    body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, textColor=TEXT, spaceAfter=2*mm, leading=14)
    disclaimer_style = ParagraphStyle("Disc", parent=styles["Normal"], fontSize=8, textColor=LIGHT_TEXT, spaceAfter=2*mm, italic=True)

    elements = []

    # Header
    elements.append(Paragraph("SATQUERY AI", title_style))
    elements.append(Paragraph("Remote Sensing Intelligence Report", subtitle_style))
    mode = analysis.get("mode", "demo")
    mode_text = "LIVE AI" if mode == "live" else "DEMO MODE"
    elements.append(Paragraph(f"Analysis Mode: <b>{mode_text}</b>", body_style))
    elements.append(Paragraph(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", body_style))
    if image_name:
        elements.append(Paragraph(f"Scene: {image_name}", body_style))
    elements.append(Spacer(1, 4*mm))

    # Query
    elements.append(Paragraph("QUERY", heading_style))
    elements.append(Paragraph(query, body_style))

    # Answer
    elements.append(Paragraph("ANSWER", heading_style))
    elements.append(Paragraph(analysis.get("answer", "N/A"), body_style))

    confidence = analysis.get("confidence", 0)
    elements.append(Paragraph(f"Confidence: {confidence:.0%}", body_style))

    # Objects
    objects = analysis.get("objects", [])
    if objects:
        elements.append(Paragraph("DETECTED FEATURES", heading_style))
        table_data = [["Feature", "Count", "Confidence"]]
        for obj in objects:
            if isinstance(obj, dict):
                table_data.append([obj.get("label", ""), str(obj.get("count", 0)), f"{obj.get('confidence', 0):.0%}"])
            else:
                table_data.append([obj.label, str(obj.count), f"{obj.confidence:.0%}"])
        t = Table(table_data, colWidths=[80*mm, 30*mm, 40*mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, LIGHT_TEXT),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(t)

    # Land Cover
    lc = analysis.get("land_cover")
    if lc:
        elements.append(Paragraph("AI-ESTIMATED VISUAL LAND COVER", heading_style))
        lc_data = lc if isinstance(lc, dict) else lc.dict() if hasattr(lc, 'dict') else {}
        for k, v in lc_data.items():
            label = k.replace("_", " ").title()
            elements.append(Paragraph(f"{label}: {v}%", body_style))

    # Findings
    findings = analysis.get("findings", [])
    if findings:
        elements.append(Paragraph("EVIDENCE-BASED FINDINGS", heading_style))
        for f in findings:
            fd = f if isinstance(f, dict) else f.dict() if hasattr(f, 'dict') else {}
            elements.append(Paragraph(f"<b>{fd.get('finding', '')}</b>", body_style))
            elements.append(Paragraph(f"Confidence: {fd.get('confidence', 0):.0%} | Quality: {fd.get('evidence_quality', 'N/A')}", body_style))
            elements.append(Paragraph(f"Evidence: {fd.get('evidence_description', '')}", body_style))
            lims = fd.get("limitations", [])
            if lims:
                elements.append(Paragraph(f"Limitations: {'; '.join(lims)}", disclaimer_style))
            elements.append(Spacer(1, 2*mm))

    # Changes (for comparison reports)
    changes = analysis.get("changes", [])
    if changes:
        elements.append(Paragraph("DETECTED CHANGES", heading_style))
        for c in changes:
            cd = c if isinstance(c, dict) else c.dict() if hasattr(c, 'dict') else {}
            sev = cd.get("severity", "medium").upper()
            elements.append(Paragraph(f"<b>{cd.get('type', '').replace('_', ' ').title()}</b> — Severity: {sev}", body_style))
            elements.append(Paragraph(cd.get("description", ""), body_style))
            elements.append(Paragraph(f"Confidence: {cd.get('confidence', 0):.0%}", body_style))
            elements.append(Spacer(1, 2*mm))

    # Government Insight
    gov = analysis.get("government_use")
    if gov:
        gd = gov if isinstance(gov, dict) else gov.dict() if hasattr(gov, 'dict') else {}
        elements.append(Paragraph("GOVERNMENT INSIGHT", heading_style))
        elements.append(Paragraph(f"Department: <b>{gd.get('department', 'N/A')}</b>", body_style))
        elements.append(Paragraph(f"Issue: {gd.get('issue', 'N/A')}", body_style))
        priority = gd.get("priority", "MEDIUM")
        elements.append(Paragraph(f"Priority: <b>{priority}</b>", body_style))
        elements.append(Paragraph(f"Recommended Action: {gd.get('recommended_action', 'N/A')}", body_style))
        elements.append(Paragraph(f"Reasoning: {gd.get('reasoning', 'N/A')}", body_style))

    # Heatmap image
    if heatmap_b64:
        try:
            elements.append(Paragraph("VISUAL CHANGE MAP", heading_style))
            elements.append(Paragraph("Pixel-difference visualization — not scientifically validated change detection.", disclaimer_style))
            img_data = base64.b64decode(heatmap_b64)
            img_buf = io.BytesIO(img_data)
            img = RLImage(img_buf, width=150*mm, height=100*mm)
            elements.append(img)
        except Exception:
            pass

    # Limitations
    limitations = analysis.get("limitations", [])
    if limitations:
        elements.append(Paragraph("LIMITATIONS", heading_style))
        for lim in limitations:
            elements.append(Paragraph(f"• {lim}", disclaimer_style))

    # Disclaimer
    elements.append(Spacer(1, 8*mm))
    elements.append(Paragraph(
        "DISCLAIMER: AI-assisted interpretation for screening and decision-support. "
        "Not a substitute for official survey, legal determination, or field verification. "
        "Uploaded imagery is processed by the configured AI provider when Live AI mode is enabled.",
        disclaimer_style,
    ))

    doc.build(elements)
    return buf.getvalue()
