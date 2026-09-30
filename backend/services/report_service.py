from __future__ import annotations

from datetime import datetime
from typing import Sequence

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing, Line
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    CondPageBreak,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy.orm import Session

from db.database import REPORTS_DIR
from db.models import GeneratedReport
from schemas.contracts import ReportResponse
from services.analytics_service import get_analytics_summary
from services.anomaly_service import detect_anomalies
from services.cost_service import get_cost_summary
from services.forecast_service import generate_forecast
from services.recommendation_service import generate_recommendations


NAVY = colors.HexColor("#16324f")
STEEL = colors.HexColor("#2f6f9f")
TEAL = colors.HexColor("#0f9b8e")
AMBER = colors.HexColor("#d98324")
CRIMSON = colors.HexColor("#b3261e")
SLATE = colors.HexColor("#475569")
LINE_GREY = colors.HexColor("#cbd5e1")
BAND_GREY = colors.HexColor("#f4f7fa")

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 18 * mm
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN

SEVERITY_COLORS = {
    "Critical": CRIMSON,
    "High": AMBER,
    "Medium": colors.HexColor("#b08900"),
    "Low": TEAL,
}


def _build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "ReportTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=23,
            leading=27,
            textColor=NAVY,
            alignment=TA_CENTER,
            spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=14,
            textColor=SLATE,
            alignment=TA_CENTER,
        ),
        "section": ParagraphStyle(
            "SectionHeading",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=NAVY,
            spaceBefore=2,
            spaceAfter=2,
        ),
        "section_note": ParagraphStyle(
            "SectionNote",
            parent=base["Normal"],
            fontSize=8.5,
            leading=11.5,
            textColor=SLATE,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "ReportBody",
            parent=base["Normal"],
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor("#1f2937"),
            alignment=TA_JUSTIFY,
            spaceAfter=6,
        ),
        "kpi_label": ParagraphStyle(
            "KpiLabel",
            parent=base["Normal"],
            fontSize=7,
            leading=9,
            textColor=SLATE,
            alignment=TA_CENTER,
        ),
        "kpi_value": ParagraphStyle(
            "KpiValue",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=NAVY,
            alignment=TA_CENTER,
        ),
        "th": ParagraphStyle(
            "TableHeader",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.white,
        ),
        "th_right": ParagraphStyle(
            "TableHeaderRight",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.white,
            alignment=TA_RIGHT,
        ),
        "td": ParagraphStyle(
            "TableCell",
            parent=base["Normal"],
            fontSize=8,
            leading=10.5,
            textColor=colors.HexColor("#1f2937"),
        ),
        "td_right": ParagraphStyle(
            "TableCellRight",
            parent=base["Normal"],
            fontSize=8,
            leading=10.5,
            textColor=colors.HexColor("#1f2937"),
            alignment=TA_RIGHT,
        ),
        "td_label": ParagraphStyle(
            "TableCellLabel",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10.5,
            textColor=NAVY,
        ),
        "caption": ParagraphStyle(
            "FigureCaption",
            parent=base["Normal"],
            fontSize=7.5,
            leading=10,
            textColor=SLATE,
            alignment=TA_CENTER,
            spaceBefore=2,
            spaceAfter=12,
        ),
    }
    for severity, color in SEVERITY_COLORS.items():
        styles[f"sev_{severity}"] = ParagraphStyle(
            f"Severity{severity}",
            parent=styles["td"],
            fontName="Helvetica-Bold",
            textColor=color,
        )
    return styles


_STYLES = _build_styles()


def _number(value: float, decimals: int = 2) -> str:
    return f"{value:,.{decimals}f}"


def _header_footer(reference: str, generated_on: str):
    def draw(canvas, doc) -> None:
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.rect(0, PAGE_HEIGHT - 12 * mm, PAGE_WIDTH, 12 * mm, stroke=0, fill=1)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 7.5)
        canvas.drawString(MARGIN, PAGE_HEIGHT - 8 * mm, "ENERGY CONSUMPTION OPTIMIZATION PROGRAMME")
        canvas.setFont("Helvetica", 7.5)
        canvas.drawRightString(PAGE_WIDTH - MARGIN, PAGE_HEIGHT - 8 * mm, reference)

        canvas.setStrokeColor(LINE_GREY)
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, 13 * mm, PAGE_WIDTH - MARGIN, 13 * mm)
        canvas.setFillColor(SLATE)
        canvas.setFont("Helvetica", 7)
        canvas.drawString(MARGIN, 9.5 * mm, f"Internal use only  |  Issued {generated_on}")
        canvas.drawRightString(PAGE_WIDTH - MARGIN, 9.5 * mm, f"Page {doc.page}")
        canvas.restoreState()

    return draw


def _section(title: str, note: str | None = None) -> list:
    rule = Drawing(CONTENT_WIDTH, 3)
    rule.add(Line(0, 1.5, CONTENT_WIDTH, 1.5, strokeColor=STEEL, strokeWidth=1.2))
    flowables = [Paragraph(title, _STYLES["section"]), rule, Spacer(1, 5)]
    if note:
        flowables.append(Paragraph(note, _STYLES["section_note"]))
    return flowables


def _data_table(
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    col_widths: Sequence[float],
    right_aligned: Sequence[int] = (),
    severity_column: int | None = None,
) -> Table:
    right = set(right_aligned)
    table_rows = [
        [
            Paragraph(text, _STYLES["th_right"] if index in right else _STYLES["th"])
            for index, text in enumerate(headers)
        ]
    ]
    for row in rows:
        cells = []
        for index, value in enumerate(row):
            if severity_column is not None and index == severity_column:
                style = _STYLES.get(f"sev_{value}", _STYLES["td"])
            elif index in right:
                style = _STYLES["td_right"]
            else:
                style = _STYLES["td"]
            cells.append(Paragraph(str(value), style))
        table_rows.append(cells)

    table = Table(table_rows, colWidths=list(col_widths), repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BAND_GREY]),
                ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE_GREY),
                ("LINEBEFORE", (0, 0), (-1, -1), 0.4, LINE_GREY),
                ("LINEAFTER", (0, 0), (-1, -1), 0.4, LINE_GREY),
                ("BOX", (0, 0), (-1, -1), 0.6, NAVY),
            ]
        )
    )
    return table


def _kpi_band(entries: Sequence[tuple[str, str]]) -> Table:
    values = [Paragraph(value, _STYLES["kpi_value"]) for _, value in entries]
    labels = [Paragraph(label, _STYLES["kpi_label"]) for label, _ in entries]
    width = CONTENT_WIDTH / len(entries)
    table = Table([values, labels], colWidths=[width] * len(entries), hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), BAND_GREY),
                ("BOX", (0, 0), (-1, -1), 0.6, LINE_GREY),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.white),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return table


def _axis_bounds(values: Sequence[float]) -> tuple[float, float, float]:
    low = min(values)
    high = max(values)
    if high - low < 1e-6:
        high = low + max(abs(low) * 0.1, 1.0)
    padding = (high - low) * 0.18
    minimum = max(0.0, low - padding)
    maximum = high + padding
    return minimum, maximum, (maximum - minimum) / 4


def _thin_labels(labels: Sequence[str], maximum: int = 12) -> list[str]:
    if len(labels) <= maximum:
        return list(labels)
    step = max(1, round(len(labels) / maximum))
    return [label if index % step == 0 else "" for index, label in enumerate(labels)]


def _line_chart(
    categories: Sequence[str],
    series: Sequence[Sequence[float]],
    names: Sequence[str],
    palette: Sequence[colors.Color],
    height: float = 160,
) -> Drawing:
    drawing = Drawing(CONTENT_WIDTH, height + 22)
    chart = HorizontalLineChart()
    chart.x = 44
    chart.y = 34
    chart.width = CONTENT_WIDTH - 60
    chart.height = height - 46
    chart.data = [list(values) for values in series]
    chart.categoryAxis.categoryNames = _thin_labels(categories)
    chart.categoryAxis.labels.boxAnchor = "ne"
    chart.categoryAxis.labels.angle = 30
    chart.categoryAxis.labels.dy = -3
    chart.categoryAxis.labels.fontName = "Helvetica"
    chart.categoryAxis.labels.fontSize = 6.5
    chart.categoryAxis.strokeColor = LINE_GREY
    chart.valueAxis.labels.fontName = "Helvetica"
    chart.valueAxis.labels.fontSize = 6.5
    chart.valueAxis.strokeColor = LINE_GREY
    chart.valueAxis.gridStrokeColor = colors.HexColor("#e6eaf0")
    chart.valueAxis.visibleGrid = True
    flat = [value for values in series for value in values]
    chart.valueAxis.valueMin, chart.valueAxis.valueMax, chart.valueAxis.valueStep = _axis_bounds(flat)
    for index, color in enumerate(palette):
        chart.lines[index].strokeColor = color
        chart.lines[index].strokeWidth = 1.5
    drawing.add(chart)

    legend = Legend()
    legend.x = 44
    legend.y = height + 12
    legend.alignment = "right"
    legend.columnMaximum = 1
    legend.deltax = 88
    legend.dxTextSpace = 4
    legend.fontName = "Helvetica"
    legend.fontSize = 7
    legend.dx = 6
    legend.dy = 6
    legend.colorNamePairs = list(zip(palette, names))
    drawing.add(legend)
    return drawing


def _bar_chart(categories: Sequence[str], values: Sequence[float], height: float = 165) -> Drawing:
    drawing = Drawing(CONTENT_WIDTH, height)
    chart = VerticalBarChart()
    chart.x = 44
    chart.y = 44
    chart.width = CONTENT_WIDTH - 60
    chart.height = height - 56
    chart.data = [list(values)]
    chart.categoryAxis.categoryNames = list(categories)
    chart.categoryAxis.labels.boxAnchor = "ne"
    chart.categoryAxis.labels.angle = 28
    chart.categoryAxis.labels.dy = -3
    chart.categoryAxis.labels.fontName = "Helvetica"
    chart.categoryAxis.labels.fontSize = 6.5
    chart.categoryAxis.strokeColor = LINE_GREY
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = max(values) * 1.15
    chart.valueAxis.valueStep = chart.valueAxis.valueMax / 4
    chart.valueAxis.labels.fontName = "Helvetica"
    chart.valueAxis.labels.fontSize = 6.5
    chart.valueAxis.strokeColor = LINE_GREY
    chart.valueAxis.gridStrokeColor = colors.HexColor("#e6eaf0")
    chart.valueAxis.visibleGrid = True
    chart.barWidth = 5
    chart.groupSpacing = 10
    chart.bars[0].fillColor = STEEL
    chart.bars[0].strokeColor = None
    drawing.add(chart)
    return drawing


def _pie_chart(labels: Sequence[str], values: Sequence[float], palette: Sequence[colors.Color]) -> Drawing:
    drawing = Drawing(CONTENT_WIDTH, 145)
    pie = Pie()
    pie.x = 110
    pie.y = 18
    pie.width = 110
    pie.height = 110
    pie.data = list(values)
    pie.labels = None
    pie.slices.strokeColor = colors.white
    pie.slices.strokeWidth = 1
    for index, color in enumerate(palette):
        pie.slices[index].fillColor = color
    drawing.add(pie)

    legend = Legend()
    legend.x = 250
    legend.y = 100
    legend.alignment = "right"
    legend.columnMaximum = 6
    legend.fontName = "Helvetica"
    legend.fontSize = 7.5
    legend.dx = 6
    legend.dy = 6
    legend.dxTextSpace = 5
    legend.deltay = 12
    legend.colorNamePairs = [
        (palette[index], f"{label} \u2014 {int(values[index])} intervals") for index, label in enumerate(labels)
    ]
    drawing.add(legend)
    return drawing


def _figure(drawing: Drawing, caption: str) -> list:
    return [drawing, Paragraph(caption, _STYLES["caption"])]


def _cover_block(reference: str, generated_on: str, period: str, scope: str, model_name: str) -> Table:
    meta_rows = [
        ("Report reference", reference, "Reporting period", period),
        ("Date of issue", generated_on, "Forecast engine", model_name),
        ("Prepared by", "Energy Analytics Platform", "Data scope", scope),
    ]
    cells = [
        [
            Paragraph(row[0], _STYLES["td_label"]),
            Paragraph(row[1], _STYLES["td"]),
            Paragraph(row[2], _STYLES["td_label"]),
            Paragraph(row[3], _STYLES["td"]),
        ]
        for row in meta_rows
    ]
    table = Table(
        cells,
        colWidths=[CONTENT_WIDTH * 0.19, CONTENT_WIDTH * 0.31, CONTENT_WIDTH * 0.19, CONTENT_WIDTH * 0.31],
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), BAND_GREY),
                ("BOX", (0, 0), (-1, -1), 0.6, LINE_GREY),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.white),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return table


def generate_pdf_report(db: Session) -> ReportResponse:
    analytics = get_analytics_summary(db)
    # Only the leading points are tabulated, so the short horizon avoids ~700 wasted predictions.
    forecast = generate_forecast(db, "24h")
    anomalies = detect_anomalies(db)
    costs = get_cost_summary(db)
    recommendations = generate_recommendations(db)

    issued_at = datetime.now()
    timestamp = issued_at.strftime("%Y%m%d_%H%M%S")
    report_name = f"energy_optimization_report_{timestamp}.pdf"
    report_path = REPORTS_DIR / report_name
    reference = f"EOR-{issued_at.strftime('%Y%m%d-%H%M')}"
    generated_on = issued_at.strftime("%d %B %Y, %H:%M")

    daily_trend = analytics.daily_trend
    period = f"{daily_trend[0].period} to {daily_trend[-1].period}" if daily_trend else issued_at.strftime("%Y-%m-%d")
    scope = f"{len(daily_trend)} operating days across {len(analytics.device_breakdown)} monitored assets"

    doc = SimpleDocTemplate(
        str(report_path),
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN + 6 * mm,
        bottomMargin=MARGIN,
        title="Energy Consumption Optimization Report",
        author="Energy Analytics Platform",
        subject=f"Energy optimization findings for {period}",
    )

    story: list = [
        Paragraph("Energy Consumption Optimization Report", _STYLES["title"]),
        Paragraph(
            "Consumption performance, demand forecast, anomaly surveillance and cost reduction plan",
            _STYLES["subtitle"],
        ),
        Spacer(1, 14),
        _cover_block(reference, generated_on, period, scope, forecast.best_model),
        Spacer(1, 16),
    ]

    story.extend(_section("1. Executive Summary"))
    critical_count = sum(1 for item in anomalies.anomalies if item.severity_level in {"Critical", "High"})
    total_savings = sum(item.estimated_savings for item in recommendations.recommendations)
    story.append(
        Paragraph(
            f"Metered consumption across the review period totalled <b>{_number(analytics.total_energy)} kWh</b>, "
            f"averaging {_number(analytics.average_consumption)} kWh per interval against a recorded peak of "
            f"{_number(analytics.peak_consumption)} kWh. The underlying demand trend is "
            f"<b>{analytics.trend_direction}</b> and load concentrates around {analytics.peak_hour:02d}:00, where "
            f"the mean draw reaches {_number(analytics.peak_hour_average)} kWh. Cost exposure for the most recent "
            f"billing month is {_number(analytics.estimated_monthly_cost)}, against which this assessment "
            f"identifies an addressable reduction of {_number(analytics.savings_opportunity)} through "
            f"tariff-aware scheduling and off-hours load control.",
            _STYLES["body"],
        )
    )
    story.append(
        Paragraph(
            f"Automated surveillance flagged <b>{anomalies.count} anomalous intervals</b>, of which "
            f"{critical_count} are rated critical or high and warrant engineering inspection. Demand for the "
            f"next 24 hours is projected by the <b>{forecast.best_model}</b> model, selected on lowest "
            f"out-of-sample RMSE from the candidate set evaluated in Section 3. The actions listed in Section 6 "
            f"carry a combined estimated saving of {_number(total_savings)}.",
            _STYLES["body"],
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        _kpi_band(
            [
                ("TOTAL ENERGY (kWh)", _number(analytics.total_energy, 0)),
                ("PEAK LOAD (kWh)", _number(analytics.peak_consumption)),
                ("MONTHLY COST", _number(analytics.estimated_monthly_cost)),
                ("SAVINGS POTENTIAL", _number(analytics.savings_opportunity)),
                ("ANOMALIES", str(anomalies.count)),
            ]
        )
    )
    story.append(Spacer(1, 18))

    story.extend(_section("2. Consumption Performance"))
    story.append(
        _data_table(
            ["Indicator", "Measured value"],
            [
                ["Total energy consumed", f"{_number(analytics.total_energy)} kWh"],
                ["Average consumption per interval", f"{_number(analytics.average_consumption)} kWh"],
                ["Peak recorded consumption", f"{_number(analytics.peak_consumption)} kWh"],
                ["Minimum recorded consumption", f"{_number(analytics.minimum_consumption)} kWh"],
                [
                    "Peak demand hour",
                    f"{analytics.peak_hour:02d}:00 ({_number(analytics.peak_hour_average)} kWh avg.)",
                ],
                ["Observed trend direction", analytics.trend_direction.capitalize()],
                ["Estimated monthly cost", _number(analytics.estimated_monthly_cost)],
                ["Identified savings opportunity", _number(analytics.savings_opportunity)],
            ],
            [CONTENT_WIDTH * 0.62, CONTENT_WIDTH * 0.38],
            right_aligned=[1],
        )
    )
    story.append(Spacer(1, 16))

    if daily_trend:
        trend_points = daily_trend[-45:]
        story.extend(
            _figure(
                _line_chart(
                    [point.period for point in trend_points],
                    [[point.energy_consumption_kwh for point in trend_points]],
                    ["Daily energy (kWh)"],
                    [STEEL],
                ),
                "Figure 1 \u2014 Daily metered consumption across the review period.",
            )
        )

    if analytics.device_breakdown:
        devices = analytics.device_breakdown[:10]
        story.append(CondPageBreak(210))
        story.extend(
            _figure(
                _bar_chart(
                    [str(item["device_name"])[:18] for item in devices],
                    [float(item["energy_consumption_kwh"]) for item in devices],
                ),
                "Figure 2 \u2014 Energy consumption by monitored asset (highest contributors).",
            )
        )

    story.append(PageBreak())

    story.extend(
        _section(
            "3. Demand Forecast",
            "Predicted interval demand with a 95% confidence band derived from out-of-sample residual dispersion.",
        )
    )
    if forecast.forecast:
        points = forecast.forecast
        story.extend(
            _figure(
                _line_chart(
                    [point.timestamp.strftime("%d %b %H:%M") for point in points],
                    [
                        [point.upper_bound for point in points],
                        [point.predicted_consumption_kwh for point in points],
                        [point.lower_bound for point in points],
                    ],
                    ["Upper bound", "Forecast", "Lower bound"],
                    [LINE_GREY, STEEL, LINE_GREY],
                ),
                f"Figure 3 \u2014 {forecast.selected_horizon} demand forecast from the {forecast.best_model} model.",
            )
        )
        story.append(
            _data_table(
                ["Interval", "Forecast (kWh)", "Lower 95%", "Upper 95%"],
                [
                    [
                        point.timestamp.strftime("%d %b %Y  %H:%M"),
                        _number(point.predicted_consumption_kwh),
                        _number(point.lower_bound),
                        _number(point.upper_bound),
                    ]
                    for point in points[:14]
                ],
                [CONTENT_WIDTH * 0.34, CONTENT_WIDTH * 0.22, CONTENT_WIDTH * 0.22, CONTENT_WIDTH * 0.22],
                right_aligned=[1, 2, 3],
            )
        )
        story.append(Spacer(1, 16))

    if forecast.metrics:
        story.append(
            KeepTogether(
                [
                    Paragraph("3.1 Model selection evidence", _STYLES["section"]),
                    Spacer(1, 5),
                    _data_table(
                        ["Candidate model", "MAE", "RMSE", "MAPE", "R\u00b2", "Status"],
                        [
                            [
                                metric.model_name,
                                _number(metric.mae, 3),
                                _number(metric.rmse, 3),
                                _number(metric.mape, 3),
                                _number(metric.r2, 3),
                                metric.status.capitalize(),
                            ]
                            for metric in forecast.metrics
                        ],
                        [
                            CONTENT_WIDTH * 0.26,
                            CONTENT_WIDTH * 0.13,
                            CONTENT_WIDTH * 0.13,
                            CONTENT_WIDTH * 0.13,
                            CONTENT_WIDTH * 0.13,
                            CONTENT_WIDTH * 0.22,
                        ],
                        right_aligned=[1, 2, 3, 4],
                    ),
                ]
            )
        )
    story.append(PageBreak())

    story.extend(
        _section(
            "4. Anomaly Surveillance",
            "Intervals isolated by an Isolation Forest and Local Outlier Factor ensemble, combined with a "
            "rate-of-change spike detector.",
        )
    )
    if anomalies.severity_breakdown:
        order = list(SEVERITY_COLORS)
        breakdown = sorted(
            anomalies.severity_breakdown,
            key=lambda item: order.index(item["severity"]) if item["severity"] in order else 99,
        )
        story.extend(
            _figure(
                _pie_chart(
                    [str(item["severity"]) for item in breakdown],
                    [float(item["count"]) for item in breakdown],
                    [SEVERITY_COLORS.get(str(item["severity"]), SLATE) for item in breakdown],
                ),
                "Figure 4 \u2014 Distribution of flagged intervals by severity class.",
            )
        )

    if anomalies.anomalies:
        story.append(
            _data_table(
                ["Interval", "Asset", "Severity", "Score", "Observation"],
                [
                    [
                        item.timestamp.strftime("%d %b %Y %H:%M"),
                        item.device_name,
                        item.severity_level,
                        _number(item.anomaly_score, 3),
                        f"{_number(item.energy_consumption_kwh)} kWh recorded, deviating from the learned "
                        f"operating profile for this asset and time of day.",
                    ]
                    for item in anomalies.anomalies[:15]
                ],
                [
                    CONTENT_WIDTH * 0.18,
                    CONTENT_WIDTH * 0.16,
                    CONTENT_WIDTH * 0.11,
                    CONTENT_WIDTH * 0.09,
                    CONTENT_WIDTH * 0.46,
                ],
                right_aligned=[3],
                severity_column=2,
            )
        )
        if anomalies.count > 15:
            story.append(Spacer(1, 5))
            story.append(
                Paragraph(
                    f"Showing the 15 highest-scoring intervals of {anomalies.count} detected; the complete set is "
                    "available from the anomalies endpoint of the platform.",
                    _STYLES["section_note"],
                )
            )
    else:
        story.append(Paragraph("No anomalous intervals were detected in this review period.", _STYLES["body"]))
    story.append(PageBreak())

    story.extend(_section("5. Cost Analysis"))
    story.append(
        _data_table(
            ["Cost measure", "Amount"],
            [
                ["Most recent interval", _number(costs.current_cost)],
                ["Trailing 24 hours", _number(costs.daily_cost)],
                ["Trailing 7 days", _number(costs.weekly_cost)],
                ["Trailing 30 days", _number(costs.monthly_cost)],
                ["Forecast horizon", _number(costs.forecast_cost)],
                ["Peak-window contribution", _number(costs.peak_cost_contribution)],
                ["Addressable savings", _number(costs.potential_savings)],
            ],
            [CONTENT_WIDTH * 0.62, CONTENT_WIDTH * 0.38],
            right_aligned=[1],
        )
    )
    story.append(Spacer(1, 16))

    if costs.breakdown:
        story.append(
            KeepTogether(
                [
                    Paragraph("5.1 Cost attribution by asset", _STYLES["section"]),
                    Spacer(1, 5),
                    _data_table(
                        ["Asset", "Energy (kWh)", "Cost"],
                        [
                            [
                                str(item.get("device_name", "Unknown")),
                                _number(float(item.get("energy_consumption_kwh", 0.0))),
                                _number(float(item.get("cost", 0.0))),
                            ]
                            for item in costs.breakdown[:12]
                        ],
                        [CONTENT_WIDTH * 0.48, CONTENT_WIDTH * 0.26, CONTENT_WIDTH * 0.26],
                        right_aligned=[1, 2],
                    ),
                ]
            )
        )
        story.append(Spacer(1, 18))

    story.extend(
        _section(
            "6. Optimization Recommendations",
            "Actions derived from the observed load profile, anomaly findings and tariff structure, ranked by "
            "expected impact.",
        )
    )
    if recommendations.recommendations:
        story.append(
            _data_table(
                ["Priority", "Category", "Recommended action", "Est. saving"],
                [
                    [
                        item.priority,
                        item.category,
                        f"<b>{item.title}</b><br/>{item.description}",
                        _number(item.estimated_savings),
                    ]
                    for item in recommendations.recommendations
                ],
                [CONTENT_WIDTH * 0.11, CONTENT_WIDTH * 0.16, CONTENT_WIDTH * 0.58, CONTENT_WIDTH * 0.15],
                right_aligned=[3],
            )
        )
    else:
        story.append(Paragraph("No optimization actions were generated for this period.", _STYLES["body"]))

    story.append(Spacer(1, 18))
    story.append(
        Paragraph(
            "<b>Basis of preparation.</b> Figures are derived from the cleaned meter dataset held by the platform; "
            "duplicate and out-of-range intervals are removed before analysis. Monetary values are expressed in the "
            "tariff currency of the source dataset and exclude fixed charges, taxes and demand penalties. Forecast "
            "bands represent statistical uncertainty only and do not account for planned operational changes.",
            _STYLES["section_note"],
        )
    )

    decorate = _header_footer(reference, generated_on)
    doc.build(story, onFirstPage=decorate, onLaterPages=decorate)

    record = GeneratedReport(report_name=report_name, file_path=str(report_path), filters={"generated_at": timestamp})
    db.add(record)
    db.commit()
    db.refresh(record)
    return ReportResponse.model_validate(record)


def list_reports(db: Session) -> list[GeneratedReport]:
    return db.query(GeneratedReport).order_by(GeneratedReport.created_at.desc()).all()
