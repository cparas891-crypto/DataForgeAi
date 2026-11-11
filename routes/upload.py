import html
import datetime

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.io as pio

from fastapi import (
    APIRouter,
    Request,
    UploadFile,
    File
)

from fastapi.responses import (
    HTMLResponse
)

from fastapi.templating import (
    Jinja2Templates
)

from config import (
    TEMPLATE_DIRECTORY
)

from database import (
    insert_dataset
)

from services.loaders import (
    clean_filename,
    load_dataset,
    extract_zip_dataset
)

from services.profiler import (
    calculate_dataset_metrics
)

from services.storage import (
    save_bytes,
    file_exists,
    get_file_size,
    get_file_path
)


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    tags=[
        "Upload"
    ]
)


# =========================================================
# TEMPLATES
# =========================================================

templates = Jinja2Templates(
    directory=str(
        TEMPLATE_DIRECTORY
    )
)


# =========================================================
# LATEST UPLOAD METRICS
#
# Used by the report service until report state is moved
# into its own dedicated persistence layer.
# =========================================================

latest_upload_metrics = {
    "filename": "",
    "rows": 0,
    "columns": 0,
    "missing_values": 0,
    "duplicates": 0,
    "quality_score": 0,
    "memory_usage": 0
}


# =========================================================
# STATISTICS HTML
# =========================================================

def generate_statistics_html(
    dataframe
):

    try:

        statistics_dataframe = (
            dataframe.describe(
                include="all"
            )
        )

        statistics_dataframe = (
            statistics_dataframe
            .astype(object)
            .where(
                pd.notna(
                    statistics_dataframe
                ),
                ""
            )
        )

        return (
            statistics_dataframe
            .to_html(
                classes="table",
                border=0,
                escape=True
            )
        )

    except Exception:

        return (
            "<p>Descriptive statistics are not "
            "available for this dataset.</p>"
        )


# =========================================================
# PLOTLY CHART
# =========================================================

def generate_chart_html(
    dataframe
):

    numeric_columns = (
        dataframe
        .select_dtypes(
            include="number"
        )
        .columns
        .tolist()
    )

    if not numeric_columns:

        return ""

    chart_column = (
        numeric_columns[0]
    )

    try:

        figure = px.histogram(
            dataframe,
            x=chart_column,
            title=(
                f"Distribution of "
                f"{chart_column}"
            ),
            template="plotly_dark"
        )

        figure.update_layout(
            paper_bgcolor="#0d1829",
            plot_bgcolor="#0d1829",
            font_color="#e2e8f0",
            margin=dict(
                l=40,
                r=40,
                t=60,
                b=40
            )
        )

        return pio.to_html(
            figure,
            full_html=False,
            include_plotlyjs="cdn"
        )

    except Exception:

        return ""


# =========================================================
# UPLOAD ERROR RESPONSE
# =========================================================

def build_upload_error_response(
    error
):

    error_message = html.escape(
        str(
            error
        )
    )

    return HTMLResponse(
        content=f"""
        <!DOCTYPE html>

        <html lang="en">

        <head>

            <meta charset="UTF-8">

            <meta
                name="viewport"
                content="width=device-width, initial-scale=1.0"
            >

            <title>
                DataForge Upload Error
            </title>

        </head>

        <body
            style="
                margin:0;
                background:#08111f;
                color:#ffffff;
                font-family:Arial,Helvetica,sans-serif;
            "
        >

            <div
                style="
                    max-width:700px;
                    margin:80px auto;
                    padding:30px;
                "
            >

                <div
                    style="
                        padding:35px;
                        background:#0d1829;
                        border:1px solid #334155;
                        border-radius:14px;
                    "
                >

                    <div
                        style="
                            margin-bottom:10px;
                            color:#f87171;
                            font-size:13px;
                            font-weight:bold;
                        "
                    >
                        DATASET PROCESSING ERROR
                    </div>

                    <h1>
                        DataForge Upload Error
                    </h1>

                    <p
                        style="
                            color:#cbd5e1;
                            line-height:1.7;
                        "
                    >
                        {error_message}
                    </p>

                    <div
                        style="
                            margin-top:30px;
                        "
                    >

                        <a
                            href="/upload"
                            style="
                                display:inline-block;
                                margin-right:10px;
                                padding:12px 18px;
                                background:#0284c7;
                                color:#ffffff;
                                border-radius:7px;
                                text-decoration:none;
                            "
                        >
                            Try Again
                        </a>

                        <a
                            href="/"
                            style="
                                display:inline-block;
                                padding:12px 18px;
                                background:#334155;
                                color:#ffffff;
                                border-radius:7px;
                                text-decoration:none;
                            "
                        >
                            Dashboard
                        </a>

                    </div>

                </div>

            </div>

        </body>

        </html>
        """,
        status_code=400
    )


# =========================================================
# UPLOAD PAGE
# =========================================================

@router.get(
    "/upload",
    response_class=HTMLResponse
)
@router.get(
    "/upload/",
    response_class=HTMLResponse,
    include_in_schema=False
)
async def upload_page(
    request: Request
):

    return templates.TemplateResponse(
        request=request,
        name="upload.html",
        context={
            "request":
                request
        }
    )


# =========================================================
# UPLOAD DATASET
# =========================================================

@router.post(
    "/upload",
    response_class=HTMLResponse
)
@router.post(
    "/upload/",
    response_class=HTMLResponse,
    include_in_schema=False
)
async def upload_file(
    request: Request,
    file: UploadFile = File(...)
):

    global latest_upload_metrics


    try:

        # =================================================
        # FILENAME
        # =================================================

        filename = clean_filename(
            file.filename
        )


        # =================================================
        # EXTENSION
        # =================================================

        extension = (
            Path(
                filename
            )
            .suffix
            .lower()
            .lstrip(".")
        )


        allowed_extensions = {
            "csv",
            "json",
            "xlsx",
            "zip"
        }


        if extension not in allowed_extensions:

            raise ValueError(
                f"Unsupported file type: {extension}. "
                "Supported types are CSV, JSON, XLSX, and ZIP."
            )


        # =================================================
        # READ UPLOADED FILE
        # =================================================

        file_data = await file.read()

        await file.close()


        # =================================================
        # VALIDATE CONTENT
        # =================================================

        if not file_data:

            raise ValueError(
                "The uploaded file is empty."
            )


        # =================================================
        # SAVE THROUGH STORAGE SERVICE
        # =================================================

        filepath = save_bytes(
            "uploads",
            filename,
            file_data
        )


        # =================================================
        # VERIFY STORAGE
        # =================================================

        if not file_exists(
            "uploads",
            filename
        ):

            raise ValueError(
                "The uploaded file could not be saved."
            )


        if get_file_size(
            "uploads",
            filename
        ) == 0:

            raise ValueError(
                "The uploaded file is empty."
            )


        # =================================================
        # GET STORED FILE PATH
        # =================================================

        filepath = get_file_path(
            "uploads",
            filename
        )


        # =================================================
        # LOAD DATASET
        # =================================================

        if extension == "zip":

            dataframe = (
                extract_zip_dataset(
                    filepath
                )
            )

        else:

            dataframe = (
                load_dataset(
                    filepath,
                    extension
                )
            )


        # =================================================
        # VALIDATE DATAFRAME
        # =================================================

        if not isinstance(
            dataframe,
            pd.DataFrame
        ):

            raise ValueError(
                "The uploaded file did not produce "
                "a valid dataset."
            )


        # =================================================
        # PROFILE DATASET
        # =================================================

        metrics = (
            calculate_dataset_metrics(
                dataframe
            )
        )


        # =================================================
        # UPLOAD TIMESTAMP
        # =================================================

        timestamp = (
            datetime.datetime.now()
            .strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )


        # =================================================
        # SAVE METADATA
        #
        # Local mode:
        # SQLite
        #
        # Docker/cloud mode:
        # PostgreSQL
        # =================================================

        insert_dataset(
            filename=filename,
            upload_date=timestamp,
            rows=metrics["rows"],
            columns_count=metrics["columns"],
            missing_values=metrics[
                "missing_values"
            ],
            duplicates=metrics[
                "duplicates"
            ],
            quality_score=metrics[
                "quality_score"
            ],
            memory_usage=metrics[
                "memory_usage"
            ]
        )


        # =================================================
        # DATA TYPES
        # =================================================

        dtypes = (
            dataframe
            .dtypes
            .astype(str)
            .to_dict()
        )


        # =================================================
        # MISSING COUNTS
        # =================================================

        null_counts = (
            dataframe
            .isnull()
            .sum()
            .sort_values(
                ascending=False
            )
            .to_dict()
        )


        # =================================================
        # DATASET PREVIEW
        # =================================================

        preview = (
            dataframe
            .head(10)
            .to_html(
                classes="table",
                index=False,
                border=0,
                escape=True
            )
        )


        # =================================================
        # DESCRIPTIVE STATISTICS
        # =================================================

        stats = (
            generate_statistics_html(
                dataframe
            )
        )


        # =================================================
        # SUMMARY
        # =================================================

        summary = (
            f"Dataset contains "
            f"{metrics['rows']:,} rows and "
            f"{metrics['columns']:,} columns. "
            f"It contains "
            f"{metrics['missing_values']:,} "
            f"missing values and "
            f"{metrics['duplicates']:,} "
            f"duplicate rows. "
            f"The calculated quality score is "
            f"{metrics['quality_score']}/100."
        )


        # =================================================
        # LATEST REPORT METRICS
        # =================================================

        latest_upload_metrics = {
            "filename":
                filename,

            **metrics
        }


        # =================================================
        # VISUALIZATION
        # =================================================

        chart_html = (
            generate_chart_html(
                dataframe
            )
        )


        # =================================================
        # PROFILE PAGE
        # =================================================

        return templates.TemplateResponse(
            request=request,
            name="profile.html",
            context={
                "request":
                    request,

                "filename":
                    filename,

                "rows":
                    metrics["rows"],

                "columns":
                    metrics["columns"],

                "missing_values":
                    metrics[
                        "missing_values"
                    ],

                "duplicates":
                    metrics[
                        "duplicates"
                    ],

                "quality_score":
                    metrics[
                        "quality_score"
                    ],

                "memory_usage":
                    metrics[
                        "memory_usage"
                    ],

                "dtypes":
                    dtypes,

                "null_counts":
                    null_counts,

                "preview":
                    preview,

                "stats":
                    stats,

                "summary":
                    summary,

                "chart_html":
                    chart_html
            }
        )


    except Exception as error:

        # UploadFile may already have been closed.
        # Attempting to close it again is harmless here,
        # but we protect against an exception.

        try:

            await file.close()

        except Exception:

            pass


        return build_upload_error_response(
            error
        )