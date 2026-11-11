import re
import uuid

from pathlib import Path

from fastapi import (
    APIRouter,
    Request
)

from fastapi.responses import (
    HTMLResponse,
    FileResponse
)

from fastapi.templating import (
    Jinja2Templates
)

from config import (
    TEMPLATE_DIRECTORY,
)

from database import (
    get_cleaning_dataset_history
)

from services.loaders import (
    clean_filename,
    load_uploaded_dataset
)

from services.profiler import (
    calculate_dataset_metrics
)

from services.cleaner import (
    apply_cleaning_operations
)

from services.storage import (
    safe_filename,
    save_dataframe,
    file_exists,
    get_file_path
)


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    tags=[
        "Cleaning Studio"
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
# AVAILABLE DATASETS
# =========================================================

def get_available_datasets():

    dataset_rows = (
        get_cleaning_dataset_history()
    )

    available_datasets = []

    seen_filenames = set()


    for dataset in dataset_rows:

        filename = dataset[1]


        if (
            filename not in seen_filenames
            and file_exists(
                "uploads",
                filename
            )
        ):

            available_datasets.append(
                dataset
            )

            seen_filenames.add(
                filename
            )


    return available_datasets


# =========================================================
# CLEANING STUDIO PAGE
# =========================================================

@router.get(
    "/clean",
    response_class=HTMLResponse
)
async def cleaning_studio(
    request: Request
):

    available_datasets = (
        get_available_datasets()
    )

    return templates.TemplateResponse(
        request=request,
        name="clean.html",
        context={
            "request":
                request,

            "datasets":
                available_datasets,

            "selected_filename":
                "",

            "original_metrics":
                None,

            "cleaned_metrics":
                None,

            "original_preview":
                "",

            "cleaned_preview":
                "",

            "operations":
                [],

            "download_filename":
                "",

            "error_message":
                ""
        }
    )


# =========================================================
# RUN CLEANING PIPELINE
# =========================================================

@router.post(
    "/clean",
    response_class=HTMLResponse
)
async def run_cleaning_studio(
    request: Request
):

    form = await request.form()


    # =====================================================
    # SELECTED DATASET
    # =====================================================

    selected_filename = str(
        form.get(
            "filename",
            ""
        )
    ).strip()


    # =====================================================
    # CHECKBOX OPTIONS
    # =====================================================

    remove_duplicates = (
        form.get(
            "remove_duplicates"
        )
        == "on"
    )

    trim_spaces = (
        form.get(
            "trim_spaces"
        )
        == "on"
    )

    standardize_columns = (
        form.get(
            "standardize_columns"
        )
        == "on"
    )

    reset_index = (
        form.get(
            "reset_index"
        )
        == "on"
    )


    # =====================================================
    # MISSING-VALUE STRATEGIES
    # =====================================================

    missing_strategy = str(
        form.get(
            "missing_strategy",
            "keep"
        )
    )

    numeric_fill_strategy = str(
        form.get(
            "numeric_fill_strategy",
            "none"
        )
    )

    text_fill_strategy = str(
        form.get(
            "text_fill_strategy",
            "none"
        )
    )

    custom_text_value = str(
        form.get(
            "custom_text_value",
            ""
        )
    ).strip()


    # =====================================================
    # EXPORT FORMAT
    # =====================================================

    export_format = str(
        form.get(
            "export_format",
            "csv"
        )
    ).lower()


    # Only allow the formats currently supported by
    # the Cleaning Studio.

    if export_format not in {
        "csv",
        "xlsx"
    }:

        export_format = "csv"


    available_datasets = (
        get_available_datasets()
    )


    try:

        # =================================================
        # VALIDATE DATASET
        # =================================================

        if not selected_filename:

            raise ValueError(
                "Select a dataset before running "
                "the cleaning pipeline."
            )


        # =================================================
        # LOAD ORIGINAL DATASET
        # =================================================

        dataframe = (
            load_uploaded_dataset(
                selected_filename
            )
        )


        # =================================================
        # ORIGINAL QUALITY METRICS
        # =================================================

        original_metrics = (
            calculate_dataset_metrics(
                dataframe
            )
        )


        # =================================================
        # RUN CLEANING ENGINE
        # =================================================

        cleaned_dataframe, operations = (
            apply_cleaning_operations(
                dataframe=dataframe,

                remove_duplicates=
                    remove_duplicates,

                missing_strategy=
                    missing_strategy,

                numeric_fill_strategy=
                    numeric_fill_strategy,

                text_fill_strategy=
                    text_fill_strategy,

                custom_text_value=
                    custom_text_value,

                trim_spaces=
                    trim_spaces,

                standardize_columns=
                    standardize_columns,

                reset_index=
                    reset_index
            )
        )


        # =================================================
        # CLEANED QUALITY METRICS
        # =================================================

        cleaned_metrics = (
            calculate_dataset_metrics(
                cleaned_dataframe
            )
        )


        # =================================================
        # ORIGINAL PREVIEW
        # =================================================

        original_preview = (
            dataframe
            .head(10)
            .to_html(
                classes="data-table",
                index=False,
                border=0,
                escape=True
            )
        )


        # =================================================
        # CLEANED PREVIEW
        # =================================================

        cleaned_preview = (
            cleaned_dataframe
            .head(10)
            .to_html(
                classes="data-table",
                index=False,
                border=0,
                escape=True
            )
        )


        # =================================================
        # OUTPUT FILENAME
        # =================================================

        original_stem = (
            Path(
                selected_filename
            )
            .stem
        )


        safe_stem = re.sub(
            r"[^a-zA-Z0-9_-]+",
            "_",
            original_stem
        )


        if not safe_stem:

            safe_stem = (
                "dataset"
            )


        unique_identifier = (
            uuid.uuid4()
            .hex[:8]
        )


        # =================================================
        # XLSX EXPORT
        # =================================================

        if export_format == "xlsx":

            download_filename = (
                f"{safe_stem}"
                f"_cleaned_"
                f"{unique_identifier}"
                f".xlsx"
            )


        # =================================================
        # CSV EXPORT
        # =================================================

        else:

            download_filename = (
                f"{safe_stem}"
                f"_cleaned_"
                f"{unique_identifier}"
                f".csv"
            )


        # =================================================
        # SAVE THROUGH STORAGE SERVICE
        # =================================================

        save_dataframe(
            "cleaned",
            download_filename,
            cleaned_dataframe
        )


        # =================================================
        # VERIFY EXPORT
        # =================================================

        if not file_exists(
            "cleaned",
            download_filename
        ):

            raise ValueError(
                "DataForge created the cleaned dataset "
                "but could not verify the exported file."
            )


        # =================================================
        # RESULTS PAGE
        # =================================================

        return templates.TemplateResponse(
            request=request,
            name="clean.html",
            context={
                "request":
                    request,

                "datasets":
                    available_datasets,

                "selected_filename":
                    selected_filename,

                "original_metrics":
                    original_metrics,

                "cleaned_metrics":
                    cleaned_metrics,

                "original_preview":
                    original_preview,

                "cleaned_preview":
                    cleaned_preview,

                "operations":
                    operations,

                "download_filename":
                    download_filename,

                "error_message":
                    ""
            }
        )


    except Exception as error:

        return templates.TemplateResponse(
            request=request,
            name="clean.html",
            context={
                "request":
                    request,

                "datasets":
                    available_datasets,

                "selected_filename":
                    selected_filename,

                "original_metrics":
                    None,

                "cleaned_metrics":
                    None,

                "original_preview":
                    "",

                "cleaned_preview":
                    "",

                "operations":
                    [],

                "download_filename":
                    "",

                "error_message":
                    str(
                        error
                    )
            },
            status_code=400
        )


# =========================================================
# DOWNLOAD CLEANED DATASET
# =========================================================

@router.get(
    "/download-cleaned/{filename}"
)
async def download_cleaned_dataset(
    filename: str
):

    # =====================================================
    # SAFE FILENAME
    # =====================================================

    download_filename = (
        safe_filename(
            filename
        )
    )


    # =====================================================
    # VERIFY FILE EXISTS THROUGH STORAGE SERVICE
    # =====================================================

    if not file_exists(
        "cleaned",
        download_filename
    ):

        return HTMLResponse(
            content="""
            <!DOCTYPE html>

            <html lang="en">

            <head>

                <meta charset="UTF-8">

                <meta
                    name="viewport"
                    content="width=device-width, initial-scale=1.0"
                >

                <title>
                    Cleaned File Not Found
                </title>

            </head>

            <body
                style="
                    margin:0;
                    padding:45px;
                    background:#08111f;
                    color:#ffffff;
                    font-family:Arial,Helvetica,sans-serif;
                "
            >

                <h1>
                    Cleaned dataset not found
                </h1>

                <p>
                    The requested cleaned dataset
                    is no longer available.
                </p>

                <a
                    href="/clean"
                    style="
                        display:inline-block;
                        margin-top:20px;
                        padding:12px 18px;
                        color:#ffffff;
                        background:#0284c7;
                        border-radius:7px;
                        text-decoration:none;
                    "
                >
                    Return to Cleaning Studio
                </a>

            </body>

            </html>
            """,
            status_code=404
        )


    # =====================================================
    # GET FILE THROUGH STORAGE SERVICE
    # =====================================================

    filepath = (
        get_file_path(
            "cleaned",
            download_filename
        )
    )


    # =====================================================
    # MEDIA TYPE
    # =====================================================

    extension = (
        filepath
        .suffix
        .lower()
    )


    if extension == ".xlsx":

        media_type = (
            "application/"
            "vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )

    elif extension == ".csv":

        media_type = (
            "text/csv"
        )

    else:

        return HTMLResponse(
            content=(
                "Unsupported cleaned "
                "dataset format."
            ),
            status_code=400
        )


    # =====================================================
    # DOWNLOAD RESPONSE
    # =====================================================

    return FileResponse(
        path=str(
            filepath
        ),
        media_type=media_type,
        filename=download_filename
    )