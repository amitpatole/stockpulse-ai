"""
TickerPulse AI - Research Brief Export Utilities
Generates ZIP, CSV, and PDF exports from research brief records.
"""

import csv
import io
import logging
import re
import zipfile
from typing import Literal

logger = logging.getLogger(__name__)

ExportFormat = Literal['zip', 'csv', 'pdf']

_MARKDOWN_HEADER = """\
# {title}

**Ticker:** {ticker}
**Agent:** {agent_name}
**Model:** {model_used}
**Created:** {created_at}

---

"""


def _brief_to_markdown(brief: dict) -> str:
    """Render a brief dict as a Markdown string with a metadata header."""
    header = _MARKDOWN_HEADER.format(
        title=brief.get('title', ''),
        ticker=brief.get('ticker', ''),
        agent_name=brief.get('agent_name', ''),
        model_used=brief.get('model_used', ''),
        created_at=brief.get('created_at', ''),
    )
    return header + (brief.get('content') or '')


def _safe_filename(ticker: str, brief_id: int) -> str:
    """Return a filesystem-safe filename for a brief."""
    safe_ticker = re.sub(r'[^\w.-]', '_', ticker.upper())
    return f"{safe_ticker}-{brief_id}.md"


def build_zip(briefs: list[dict]) -> bytes:
    """Return a ZIP archive containing one Markdown file per brief."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        for brief in briefs:
            filename = _safe_filename(brief.get('ticker', 'UNKNOWN'), brief['id'])
            content = _brief_to_markdown(brief)
            zf.writestr(filename, content.encode('utf-8'))
    return buf.getvalue()


def build_csv(briefs: list[dict]) -> bytes:
    """Return a UTF-8 CSV with one row per brief (BOM for Excel compatibility)."""
    buf = io.StringIO()
    fieldnames = ['id', 'ticker', 'title', 'agent_name', 'model_used', 'created_at', 'content']
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    for brief in briefs:
        writer.writerow({k: brief.get(k, '') for k in fieldnames})
    return buf.getvalue().encode('utf-8')


def _latin1(text: str) -> str:
    """Drop characters that are outside Latin-1; replace common Unicode punctuation."""
    replacements = {
        '\u2014': '-', '\u2013': '-', '\u2018': "'", '\u2019': "'",
        '\u201c': '"', '\u201d': '"', '\u2026': '...', '\u00a0': ' ',
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text.encode('latin-1', errors='ignore').decode('latin-1')


def build_pdf(briefs: list[dict]) -> bytes:
    """Return a PDF with one section per brief."""
    from fpdf import FPDF

    class BriefPDF(FPDF):
        def header(self):
            self.set_font('Helvetica', 'B', 9)
            self.set_text_color(120, 120, 120)
            self.cell(0, 8, 'TickerPulse AI - Research Brief Export', align='C')
            self.ln(2)

        def footer(self):
            self.set_y(-12)
            self.set_font('Helvetica', '', 8)
            self.set_text_color(150, 150, 150)
            self.cell(0, 6, f'Page {self.page_no()}', align='C')

    pdf = BriefPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(left=20, top=18, right=20)

    errors: list[str] = []

    for i, brief in enumerate(briefs):
        try:
            pdf.add_page()

            # --- Ticker badge & title ---
            pdf.set_font('Helvetica', 'B', 18)
            pdf.set_text_color(59, 130, 246)  # blue-500
            pdf.cell(0, 10, _latin1(brief.get('ticker', '')), ln=True)

            pdf.set_font('Helvetica', 'B', 13)
            pdf.set_text_color(240, 240, 240)
            pdf.multi_cell(0, 7, _latin1(brief.get('title', '')))
            pdf.ln(2)

            # --- Metadata row ---
            pdf.set_font('Helvetica', '', 9)
            pdf.set_text_color(160, 160, 160)
            meta = (
                f"Agent: {brief.get('agent_name', '')}  |  "
                f"Model: {brief.get('model_used', '')}  |  "
                f"Created: {brief.get('created_at', '')}"
            )
            pdf.multi_cell(0, 5, _latin1(meta))
            pdf.ln(4)

            # Separator line
            pdf.set_draw_color(71, 85, 105)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(5)

            # --- Content (strip markdown syntax for clean plain text) ---
            content = brief.get('content', '')
            content = re.sub(r'^#{1,3} ', '', content, flags=re.MULTILINE)
            content = re.sub(r'\*\*(.+?)\*\*', r'\1', content)
            content = re.sub(r'\*(.+?)\*', r'\1', content)
            content = re.sub(r'`(.+?)`', r'\1', content)

            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(220, 220, 220)
            pdf.multi_cell(0, 5.5, _latin1(content))

        except Exception as exc:
            logger.warning("PDF: failed to render brief id=%s: %s", brief.get('id'), exc)
            errors.append(f"Brief ID {brief.get('id')} ({brief.get('ticker')}): {exc}")

    if errors:
        pdf.add_page()
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(239, 68, 68)  # red
        pdf.cell(0, 10, 'Export Errors', ln=True)
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(220, 220, 220)
        for msg in errors:
            pdf.multi_cell(0, 6, _latin1(msg))

    return bytes(pdf.output())
