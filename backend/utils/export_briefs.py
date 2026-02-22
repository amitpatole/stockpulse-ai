"""
TickerPulse AI v3.0 - Research Brief Export Utilities
Generates ZIP, CSV, and PDF exports from a list of brief dicts.
"""

import csv
import io
import zipfile
from datetime import date
from typing import Literal

ExportFormat = Literal['zip', 'csv', 'pdf']


def export_as_zip(briefs: list[dict]) -> bytes:
    """Return a ZIP archive with one .md file per brief."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        for brief in briefs:
            ticker = brief.get('ticker', 'UNKNOWN')
            brief_id = brief.get('id', 0)
            filename = f"{ticker}-{brief_id}.md"

            md_lines = [
                f"# {brief.get('title', '')}",
                f"",
                f"**Ticker:** {ticker}",
                f"**Agent:** {brief.get('agent_name', '')}",
                f"**Model:** {brief.get('model_used', '')}",
                f"**Date:** {brief.get('created_at', '')}",
                f"",
                f"---",
                f"",
                brief.get('content', ''),
            ]
            zf.writestr(filename, "\n".join(md_lines))
    return buf.getvalue()


def export_as_csv(briefs: list[dict]) -> bytes:
    """Return CSV bytes with columns: id, ticker, title, agent_name, model_used, created_at, content."""
    buf = io.StringIO()
    columns = ['id', 'ticker', 'title', 'agent_name', 'model_used', 'created_at', 'content']
    writer = csv.DictWriter(buf, fieldnames=columns, extrasaction='ignore')
    writer.writeheader()
    for brief in briefs:
        writer.writerow({col: brief.get(col, '') for col in columns})
    return buf.getvalue().encode('utf-8')


def export_as_pdf(briefs: list[dict]) -> bytes:
    """Return PDF bytes with one section per brief using reportlab."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, PageBreak, HRFlowable,
    )
    from reportlab.lib import colors

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=inch,
        rightMargin=inch,
        topMargin=inch,
        bottomMargin=inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'BriefTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=6,
        textColor=colors.HexColor('#1e3a5f'),
    )
    meta_style = ParagraphStyle(
        'BriefMeta',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#666666'),
        spaceAfter=12,
    )
    body_style = ParagraphStyle(
        'BriefBody',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        spaceAfter=6,
    )

    story = []

    for i, brief in enumerate(briefs):
        if i > 0:
            story.append(PageBreak())

        story.append(Paragraph(_escape_pdf(brief.get('title', 'Untitled')), title_style))

        meta = (
            f"<b>Ticker:</b> {brief.get('ticker', '')} &nbsp;|&nbsp; "
            f"<b>Agent:</b> {brief.get('agent_name', '')} &nbsp;|&nbsp; "
            f"<b>Model:</b> {brief.get('model_used', '')} &nbsp;|&nbsp; "
            f"<b>Date:</b> {brief.get('created_at', '')}"
        )
        story.append(Paragraph(meta, meta_style))
        story.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#cccccc')))
        story.append(Spacer(1, 0.1 * inch))

        content = brief.get('content', '')
        for line in content.split('\n'):
            stripped = line.strip()
            if not stripped:
                story.append(Spacer(1, 0.05 * inch))
                continue
            story.append(Paragraph(_escape_pdf(stripped), body_style))

    doc.build(story)
    return buf.getvalue()


def _escape_pdf(text: str) -> str:
    """Escape characters that would break reportlab XML parsing."""
    return (
        text
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
    )


def build_export_filename(fmt: str) -> str:
    """Return a dated filename for the export."""
    today = date.today().isoformat()
    ext = {'zip': 'zip', 'csv': 'csv', 'pdf': 'pdf'}.get(fmt, fmt)
    return f"research-brief-export-{today}.{ext}"


MIME_TYPES = {
    'zip': 'application/zip',
    'csv': 'text/csv',
    'pdf': 'application/pdf',
}
