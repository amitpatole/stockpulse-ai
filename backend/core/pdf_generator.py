```python
"""
PDF Generator - Generate PDF reports from research briefs.

Uses reportlab to create professional PDF documents with:
- Title and header
- Executive summary
- Key metrics visualization
- Research content
- Footer with generation date
"""

import json
import logging
import io
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
        PageBreak, Image
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

logger = logging.getLogger(__name__)


class PDFGenerator:
    """Generate PDF reports from research brief data."""

    def __init__(self, page_size: str = "letter"):
        """Initialize PDF generator."""
        if not REPORTLAB_AVAILABLE:
            logger.warning("reportlab not installed - PDF generation will fail")
        self.page_size = A4 if page_size == "a4" else letter
        self.styles = getSampleStyleSheet()
        self._define_custom_styles()

    def _define_custom_styles(self) -> None:
        """Define custom paragraph styles for report."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e3a8a'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Section heading
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=8,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))

        # Summary style
        self.styles.add(ParagraphStyle(
            name='Summary',
            parent=self.styles['BodyText'],
            fontSize=11,
            leading=14,
            spaceAfter=10,
            borderPadding=10,
            backColor=colors.HexColor('#f0f9ff')
        ))

        # Metric label
        self.styles.add(ParagraphStyle(
            name='MetricLabel',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#64748b'),
            fontName='Helvetica'
        ))

    def generate_pdf_bytes(
        self,
        brief_data: Dict[str, Any]
    ) -> Tuple[bytes, int]:
        """
        Generate PDF and return bytes and size.

        Args:
            brief_data: Dict with keys: ticker, title, content, executive_summary, metrics

        Returns:
            Tuple of (pdf_bytes, size_in_kb)
        """
        if not REPORTLAB_AVAILABLE:
            logger.error("reportlab not available - cannot generate PDF")
            return b"", 0

        try:
            pdf_buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                pdf_buffer,
                pagesize=self.page_size,
                rightMargin=0.75 * inch,
                leftMargin=0.75 * inch,
                topMargin=0.75 * inch,
                bottomMargin=0.75 * inch,
            )

            # Build story (content elements)
            story = []

            # Add title
            title = brief_data.get('title', 'Research Brief')
            ticker = brief_data.get('ticker', 'UNKNOWN')
            story.append(Paragraph(f"{ticker}: {title}", self.styles['CustomTitle']))
            story.append(Spacer(1, 0.2 * inch))

            # Add metadata line
            generated_at = datetime.now().strftime("%B %d, %Y at %I:%M %p")
            metadata_text = f"Generated: {generated_at}"
            story.append(Paragraph(metadata_text, self.styles['Normal']))
            story.append(Spacer(1, 0.3 * inch))

            # Add executive summary if available
            summary = brief_data.get('executive_summary')
            if summary:
                story.append(Paragraph("Executive Summary", self.styles['SectionHeading']))
                story.append(Paragraph(summary, self.styles['Summary']))
                story.append(Spacer(1, 0.2 * inch))

            # Add key metrics if available
            metrics = brief_data.get('metrics', {})
            if metrics:
                story.extend(self._build_metrics_section(metrics))
                story.append(Spacer(1, 0.2 * inch))

            # Add main content
            content = brief_data.get('content', '')
            if content:
                story.append(Paragraph("Research Content", self.styles['SectionHeading']))
                story.append(Spacer(1, 0.1 * inch))

                # Split content into paragraphs
                for paragraph_text in content.split('\n\n'):
                    if paragraph_text.strip():
                        # Handle markdown-style headers
                        if paragraph_text.startswith('##'):
                            heading_text = paragraph_text.replace('##', '').strip()
                            story.append(Paragraph(heading_text, self.styles['Heading2']))
                            story.append(Spacer(1, 0.1 * inch))
                        elif paragraph_text.startswith('#'):
                            heading_text = paragraph_text.replace('#', '').strip()
                            story.append(Paragraph(heading_text, self.styles['Heading1']))
                            story.append(Spacer(1, 0.1 * inch))
                        else:
                            story.append(Paragraph(paragraph_text.strip(), self.styles['BodyText']))
                            story.append(Spacer(1, 0.1 * inch))

            # Add footer
            story.append(Spacer(1, 0.5 * inch))
            footer_text = f"TickerPulse AI Research Brief | {ticker} | {generated_at}"
            story.append(Paragraph(footer_text, self.styles['Normal']))

            # Build PDF
            doc.build(story)

            # Get bytes
            pdf_bytes = pdf_buffer.getvalue()
            size_kb = len(pdf_bytes) // 1024

            logger.info(f"Generated PDF for {ticker}: {size_kb}KB")
            return pdf_bytes, size_kb

        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            return b"", 0

    def _build_metrics_section(self, metrics: Dict[str, Any]) -> list:
        """Build metrics visualization section."""
        elements = []
        elements.append(Paragraph("Key Metrics", self.styles['SectionHeading']))

        # Create metrics table
        rows = [["Metric", "Value"]]

        if "current_price" in metrics and metrics["current_price"]:
            rows.append(["Current Price", f"${metrics['current_price']:.2f}"])

        if "price_change_24h_pct" in metrics and metrics["price_change_24h_pct"] is not None:
            change = metrics["price_change_24h_pct"]
            rows.append(["24H Change", f"{change:+.2f}%"])

        if "rsi" in metrics and metrics["rsi"]:
            rows.append(["RSI (14)", f"{metrics['rsi']:.1f}"])

        if "sentiment_label" in metrics and metrics["sentiment_label"]:
            rows.append(["Sentiment", metrics["sentiment_label"].capitalize()])

        if "sentiment_score" in metrics and metrics["sentiment_score"] is not None:
            score = metrics["sentiment_score"]
            rows.append(["Sentiment Score", f"{score:.2f}"])

        if "news_count_7d" in metrics:
            rows.append(["News (7D)", str(metrics["news_count_7d"])])

        # Create and style table
        table = Table(rows, colWidths=[2 * inch, 2 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 0.2 * inch))
        return elements


def generate_pdf_for_brief(
    brief_data: Dict[str, Any],
    page_size: str = "letter"
) -> Tuple[bytes, int]:
    """
    Convenience function to generate PDF for a brief.

    Returns (pdf_bytes, size_in_kb)
    """
    generator = PDFGenerator(page_size=page_size)
    return generator.generate_pdf_bytes(brief_data)
```