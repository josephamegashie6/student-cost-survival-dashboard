"""
pdf_export.py — Admit Comparison PDF Memo Generator
CostCompass — Plan. Manage. Thrive.
"""
import io
from datetime import date
from typing import List, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# ── colour palette (matches dashboard)
DARK_BG   = colors.HexColor("#0f172a")
TEAL      = colors.HexColor("#14b8a6")
GOLD      = colors.HexColor("#f59e0b")
GREEN     = colors.HexColor("#10b981")
RED       = colors.HexColor("#ef4444")
SLATE_700 = colors.HexColor("#334155")
SLATE_400 = colors.HexColor("#94a3b8")
SLATE_200 = colors.HexColor("#e2e8f0")
WHITE     = colors.white
BLACK     = colors.black


def _score_color(score: float):
    if score >= 75:
        return GREEN
    if score >= 55:
        return TEAL
    if score >= 35:
        return GOLD
    return RED


def _score_label(score: float) -> str:
    if score >= 80:
        return "Excellent"
    if score >= 60:
        return "Good"
    if score >= 40:
        return "Risky"
    return "Critical"


def _usd(v: float) -> str:
    sign = "-" if v < 0 else ""
    return f"{sign}${abs(v):,.0f}"


def generate_admit_comparison_pdf(saved: List[Tuple]) -> bytes:
    """
    saved: list of (PlanningScenario, DecisionResult) tuples
    Returns: PDF bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontSize=20,
        fontName="Helvetica-Bold",
        textColor=BLACK,
        spaceAfter=4,
        alignment=TA_LEFT,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=10,
        fontName="Helvetica",
        textColor=SLATE_700,
        spaceAfter=2,
        alignment=TA_LEFT,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Normal"],
        fontSize=11,
        fontName="Helvetica-Bold",
        textColor=BLACK,
        spaceBefore=14,
        spaceAfter=6,
        borderPad=4,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=9,
        fontName="Helvetica",
        textColor=SLATE_700,
        spaceAfter=4,
        leading=14,
    )
    advisor_style = ParagraphStyle(
        "Advisor",
        parent=styles["Normal"],
        fontSize=9,
        fontName="Helvetica-Oblique",
        textColor=SLATE_700,
        spaceAfter=4,
        leading=14,
        leftIndent=10,
        borderPad=6,
    )
    small_style = ParagraphStyle(
        "Small",
        parent=styles["Normal"],
        fontSize=8,
        fontName="Helvetica",
        textColor=SLATE_400,
        spaceAfter=2,
    )

    story = []

    # ── Header
    story.append(Paragraph("Admit Comparison Memo", title_style))
    story.append(Paragraph("CostCompass · Decision Intelligence Edition", subtitle_style))
    story.append(Paragraph(f"Generated: {date.today().strftime('%B %d, %Y')}", small_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=TEAL, spaceAfter=10))

    results = [r for _, r in saved]
    scenarios = [s for s, _ in saved]
    labels = [r.scenario_label for r in results]
    ranked = sorted(results, key=lambda r: r.affordability_score, reverse=True)

    # ── Executive Summary
    story.append(Paragraph("Executive Summary", section_style))
    best = ranked[0]
    worst = ranked[-1]
    if len(ranked) > 1:
        gap = best.monthly_surplus - worst.monthly_surplus
        summary_text = (
            f"This memo compares {len(results)} financial scenarios. "
            f"<b>{best.scenario_label}</b> is the strongest option with an affordability score of "
            f"{best.affordability_score}/100 ({_score_label(best.affordability_score)}) and a monthly surplus of "
            f"{_usd(best.monthly_surplus)}. "
            f"It outperforms <b>{worst.scenario_label}</b> by {_usd(gap)} per month in baseline surplus. "
        )
        if all(r.stress_moderate >= 0 for r in results):
            summary_text += "All options hold under moderate stress."
        elif all(r.stress_moderate < 0 for r in results):
            summary_text += "No option is resilient under moderate stress — additional funding is required across all scenarios."
        else:
            summary_text += "Some options break under moderate stress. Review risk flags carefully before committing."
    else:
        summary_text = f"Single scenario analysis for <b>{best.scenario_label}</b>. Score: {best.affordability_score}/100."
    story.append(Paragraph(summary_text, body_style))

    # ── Ranking Table
    story.append(Paragraph("Ranking by Affordability Score", section_style))
    rank_data = [["Rank", "Option", "Score", "Rating", "Monthly Surplus", "Plan Viable"]]
    for i, r in enumerate(ranked):
        medal = ["1st", "2nd", "3rd"][i] if i < 3 else f"#{i+1}"
        rank_data.append([
            medal,
            r.scenario_label,
            f"{r.affordability_score}/100",
            _score_label(r.affordability_score),
            _usd(r.monthly_surplus),
            "Yes" if r.plan_viable else "No",
        ])
    rank_table = Table(rank_data, colWidths=[0.5*inch, 2.2*inch, 0.7*inch, 0.8*inch, 1.1*inch, 0.8*inch])
    rank_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TEAL),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), WHITE]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("ALIGN", (2, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(rank_table)

    # ── Full Comparison Table
    story.append(Paragraph("Full Financial Comparison", section_style))
    metrics = [
        ("Monthly Income", [_usd(r.monthly_income) for r in results]),
        ("Monthly Expenses", [_usd(r.monthly_expenses) for r in results]),
        ("Monthly Surplus", [_usd(r.monthly_surplus) for r in results]),
        ("Affordability Score", [f"{r.affordability_score}/100" for r in results]),
        ("Safe Rent Ceiling", [_usd(r.safe_rent_ceiling) for r in results]),
        ("Move-In Cash Needed", [_usd(r.move_in_cash_required) for r in results]),
        ("Cash After Move-In", [_usd(r.starting_cash_after_movein) for r in results]),
        ("Emergency Runway", [f"{r.emergency_runway_months:.1f} mo" for r in results]),
        ("Moderate Stress Surplus", [_usd(r.stress_moderate) for r in results]),
        ("Severe Stress Surplus", [_usd(r.stress_severe) for r in results]),
        ("Plan Viable", ["Yes" if r.plan_viable else "No" for r in results]),
    ]
    # Column widths: metric col + one col per scenario
    n = len(results)
    metric_col_w = 1.8 * inch
    data_col_w = (7.0 * inch - metric_col_w) / max(n, 1)
    comp_data = [["Metric"] + labels]
    for metric_name, values in metrics:
        comp_data.append([metric_name] + values)
    comp_table = Table(comp_data, colWidths=[metric_col_w] + [data_col_w] * n)
    comp_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SLATE_700),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), WHITE]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(comp_table)

    # ── Individual Recommendations
    story.append(Paragraph("Advisor Recommendations", section_style))
    for i, (scenario, result) in enumerate(saved):
        story.append(Paragraph(f"<b>{result.scenario_label}</b> — Score: {result.affordability_score}/100 ({_score_label(result.affordability_score)})", body_style))
        story.append(Paragraph(result.recommendation, advisor_style))
        # Risk flags
        danger_flags = [f for f in result.risk_flags if f.severity == "danger"]
        warning_flags = [f for f in result.risk_flags if f.severity == "warning"]
        if danger_flags:
            story.append(Paragraph("<b>Critical Risks:</b>", body_style))
            for flag in danger_flags:
                story.append(Paragraph(f"• {flag.message}", body_style))
        if warning_flags:
            story.append(Paragraph("<b>Warnings:</b>", body_style))
            for flag in warning_flags:
                story.append(Paragraph(f"• {flag.message}", body_style))
        if i < len(saved) - 1:
            story.append(Spacer(1, 8))

    # ── Footer
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=0.5, color=SLATE_400))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "This memo was generated by CostCompass. "
        "All figures are based on user-entered data and benchmark estimates. "
        "Verify all costs with your institution and local housing market.",
        small_style
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
