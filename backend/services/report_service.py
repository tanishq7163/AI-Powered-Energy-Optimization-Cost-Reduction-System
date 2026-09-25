from __future__ import annotations

from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from db.database import REPORTS_DIR
from db.models import GeneratedReport
from schemas.contracts import ReportResponse
from services.analytics_service import get_analytics_summary
from services.anomaly_service import detect_anomalies
from services.cost_service import get_cost_summary
from services.forecast_service import generate_forecast
from services.recommendation_service import generate_recommendations


def generate_pdf_report(db: Session) -> ReportResponse:
    analytics = get_analytics_summary(db)
    forecast = generate_forecast(db, "30d")
    anomalies = detect_anomalies(db)
    costs = get_cost_summary(db)
    recommendations = generate_recommendations(db)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    report_name = f"energy_optimization_report_{timestamp}.pdf"
    report_path = REPORTS_DIR / report_name

    doc = SimpleDocTemplate(str(report_path), pagesize=A4, title="Energy Optimization Report")
    styles = getSampleStyleSheet()
    story = [Paragraph("AI-Powered Energy Consumption Optimization Report", styles["Title"]), Spacer(1, 16)]

    overview_rows = [
        ["Metric", "Value"],
        ["Total Energy (kWh)", f"{analytics.total_energy:.2f}"],
        ["Average Consumption (kWh)", f"{analytics.average_consumption:.2f}"],
        ["Peak Consumption (kWh)", f"{analytics.peak_consumption:.2f}"],
        ["Estimated Monthly Cost", f"{analytics.estimated_monthly_cost:.2f}"],
        ["Savings Opportunity", f"{analytics.savings_opportunity:.2f}"],
    ]
    story.extend(_table_section("Consumption Summary", overview_rows))

    forecast_rows = [["Timestamp", "Prediction", "Lower", "Upper"]]
    forecast_rows.extend(
        [
            point.timestamp.strftime("%Y-%m-%d %H:%M"),
            f"{point.predicted_consumption_kwh:.2f}",
            f"{point.lower_bound:.2f}",
            f"{point.upper_bound:.2f}",
        ]
        for point in forecast.forecast[:20]
    )
    story.extend(_table_section("Forecast Results", forecast_rows))

    anomaly_rows = [["Timestamp", "Device", "Severity", "Score", "Description"]]
    anomaly_rows.extend(
        [
            item.timestamp.strftime("%Y-%m-%d %H:%M"),
            item.device_name,
            item.severity_level,
            f"{item.anomaly_score:.3f}",
            item.description,
        ]
        for item in anomalies.anomalies[:15]
    )
    story.extend(_table_section("Detected Anomalies", anomaly_rows))

    cost_rows = [
        ["Current Cost", f"{costs.current_cost:.2f}"],
        ["Daily Cost", f"{costs.daily_cost:.2f}"],
        ["Weekly Cost", f"{costs.weekly_cost:.2f}"],
        ["Monthly Cost", f"{costs.monthly_cost:.2f}"],
        ["Forecast Cost", f"{costs.forecast_cost:.2f}"],
        ["Potential Savings", f"{costs.potential_savings:.2f}"],
    ]
    story.extend(_table_section("Cost Analysis", [["Metric", "Value"], *cost_rows]))

    recommendation_rows = [["Category", "Priority", "Recommendation", "Estimated Savings"]]
    recommendation_rows.extend(
        [item.category, item.priority, item.description, f"{item.estimated_savings:.2f}"]
        for item in recommendations.recommendations
    )
    story.extend(_table_section("Optimization Recommendations", recommendation_rows))

    doc.build(story)

    record = GeneratedReport(report_name=report_name, file_path=str(report_path), filters={"generated_at": timestamp})
    db.add(record)
    db.commit()
    db.refresh(record)
    return ReportResponse.model_validate(record)


def _table_section(title: str, rows: list[list[str]]) -> list:
    styles = getSampleStyleSheet()
    table = Table(rows, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16324f")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ]
        )
    )
    return [Paragraph(title, styles["Heading2"]), Spacer(1, 8), table, Spacer(1, 16)]


def list_reports(db: Session) -> list[GeneratedReport]:
    return db.query(GeneratedReport).order_by(GeneratedReport.created_at.desc()).all()
