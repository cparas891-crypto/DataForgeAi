import html
import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from services.storage import (
    get_file_path
)


# =========================================================
# GENERATE EXECUTIVE PDF REPORT
# =========================================================

def create_executive_report(
    metrics
):

    report_path = get_file_path(
    "reports",
    "DataForge_Report.pdf"
)

    document = SimpleDocTemplate(
        str(
            report_path
        ),
        pagesize=letter,
        title="DataForge AI Executive Report"
    )

    styles = getSampleStyleSheet()

    content = []


    # -----------------------------------------------------
    # Title
    # -----------------------------------------------------

    content.append(
        Paragraph(
            "DataForge AI Executive Report",
            styles["Title"]
        )
    )

    content.append(
        Spacer(
            1,
            20
        )
    )


    # -----------------------------------------------------
    # Timestamp
    # -----------------------------------------------------

    generated_time = (
        datetime.datetime.now()
        .strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    content.append(
        Paragraph(
            f"Generated: {generated_time}",
            styles["BodyText"]
        )
    )

    content.append(
        Spacer(
            1,
            20
        )
    )


    # -----------------------------------------------------
    # Friendly metric names
    # -----------------------------------------------------

    pretty_names = {
        "filename":
            "Dataset",

        "rows":
            "Rows",

        "columns":
            "Columns",

        "missing_values":
            "Missing Values",

        "duplicates":
            "Duplicate Rows",

        "quality_score":
            "Quality Score",

        "memory_usage":
            "Memory Usage (KB)"
    }


    # -----------------------------------------------------
    # Add metrics
    # -----------------------------------------------------

    for key, value in metrics.items():

        label = pretty_names.get(
            key,
            key
        )

        safe_label = html.escape(
            str(label)
        )

        safe_value = html.escape(
            str(value)
        )

        if key == "quality_score":

            safe_value += "/100"

        content.append(
            Paragraph(
                f"<b>{safe_label}:</b> "
                f"{safe_value}",
                styles["BodyText"]
            )
        )

        content.append(
            Spacer(
                1,
                8
            )
        )


    # -----------------------------------------------------
    # Build report
    # -----------------------------------------------------

    document.build(
        content
    )

    return report_path