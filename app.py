import sys
import os
import re
import json
import uuid
import html
import shutil
import sqlite3
import zipfile
import tempfile
import datetime

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.io as pio

from fastapi import (
    FastAPI,
    Request,
    UploadFile,
    File
)

from fastapi.responses import (
    HTMLResponse,
    FileResponse
)

from fastapi.templating import Jinja2Templates

from reportlab.lib.pagesizes import letter

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import getSampleStyleSheet


# =========================================================
# APPLICATION
# =========================================================

app = FastAPI(
    title="DataForge AI",
    description=(
        "Dataset profiling, cleaning, "
        "analytics, and reporting platform"
    ),
    version="1.0.0"
)


# =========================================================
# PYINSTALLER-AWARE PATHS
# =========================================================

def get_resource_directory():
    """
    Returns the folder containing bundled resources.

    In development:
        The folder containing app.py

    In a PyInstaller build:
        The temporary PyInstaller resource folder
    """

    if getattr(
        sys,
        "frozen",
        False
    ):

        return Path(
            sys._MEIPASS
        )

    return Path(
        __file__
    ).resolve().parent


def get_data_directory():
    """
    Returns the persistent application-data folder.

    In development:
        The folder containing app.py

    In a PyInstaller build:
        The folder containing DataForgeAI.exe
    """

    if getattr(
        sys,
        "frozen",
        False
    ):

        return Path(
            sys.executable
        ).resolve().parent

    return Path(
        __file__
    ).resolve().parent


RESOURCE_DIR = get_resource_directory()

DATA_DIR = get_data_directory()


# =========================================================
# TEMPLATES
# =========================================================

TEMPLATE_DIRECTORY = (
    RESOURCE_DIR
    / "templates"
)

templates = Jinja2Templates(
    directory=str(
        TEMPLATE_DIRECTORY
    )
)


# =========================================================
# PERSISTENT DIRECTORIES
# =========================================================

UPLOAD_FOLDER = (
    DATA_DIR
    / "uploads"
)

REPORT_FOLDER = (
    DATA_DIR
    / "reports"
)

CLEANED_FOLDER = (
    DATA_DIR
    / "cleaned"
)

DATABASE_PATH = (
    DATA_DIR
    / "dataforge.db"
)


UPLOAD_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)

REPORT_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)

CLEANED_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)


# =========================================================
# DATABASE
# =========================================================

def get_db_connection():

    connection = sqlite3.connect(
        str(
            DATABASE_PATH
        ),
        check_same_thread=False
    )

    return connection


def initialize_database():

    connection = get_db_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                upload_date TEXT NOT NULL,
                rows INTEGER DEFAULT 0,
                columns_count INTEGER DEFAULT 0,
                missing_values INTEGER DEFAULT 0,
                duplicates INTEGER DEFAULT 0,
                quality_score INTEGER DEFAULT 0,
                memory_usage REAL DEFAULT 0
            )
            """
        )

        connection.commit()

    finally:

        connection.close()


initialize_database()


# =========================================================
# LATEST REPORT METRICS
# =========================================================

latest_metrics = {
    "filename": "",
    "rows": 0,
    "columns": 0,
    "missing_values": 0,
    "duplicates": 0,
    "quality_score": 0,
    "memory_usage": 0
}


# =========================================================
# GENERAL HELPERS
# =========================================================

def clean_filename(
    filename
):

    if not filename:

        return "uploaded_file"

    filename = os.path.basename(
        filename
    )

    filename = re.sub(
        r"[^a-zA-Z0-9._-]+",
        "_",
        filename
    )

    return filename


def safe_download_filename(
    filename
):

    filename = os.path.basename(
        filename
    )

    filename = re.sub(
        r"[^a-zA-Z0-9._-]+",
        "_",
        filename
    )

    return filename


def make_values_hashable(
    dataframe
):

    converted_dataframe = (
        dataframe.copy()
    )

    for column in converted_dataframe.columns:

        converted_dataframe[column] = (
            converted_dataframe[column]
            .apply(
                lambda value:
                    json.dumps(
                        value,
                        sort_keys=True,
                        default=str
                    )
                    if isinstance(
                        value,
                        (
                            dict,
                            list,
                            set,
                            tuple
                        )
                    )
                    else value
            )
        )

    return converted_dataframe


# =========================================================
# JSON LOADER
# =========================================================

def load_json_dataset(
    filepath
):

    parser_errors = []


    # -----------------------------------------------------
    # Attempt 1: Standard pandas JSON
    # -----------------------------------------------------

    try:

        dataframe = pd.read_json(
            filepath
        )

        if isinstance(
            dataframe,
            pd.DataFrame
        ):

            return dataframe

    except Exception as error:

        parser_errors.append(
            str(error)
        )


    # -----------------------------------------------------
    # Attempt 2: JSON Lines / NDJSON
    # -----------------------------------------------------

    try:

        dataframe = pd.read_json(
            filepath,
            lines=True
        )

        if isinstance(
            dataframe,
            pd.DataFrame
        ):

            return dataframe

    except Exception as error:

        parser_errors.append(
            str(error)
        )


    # -----------------------------------------------------
    # Attempt 3: Built-in JSON parser
    # -----------------------------------------------------

    data = None

    encodings = [
        "utf-8",
        "utf-8-sig",
        "latin-1"
    ]

    for encoding in encodings:

        try:

            with open(
                filepath,
                "r",
                encoding=encoding
            ) as json_file:

                data = json.load(
                    json_file
                )

            break

        except Exception as error:

            parser_errors.append(
                str(error)
            )


    if data is None:

        error_summary = " | ".join(
            parser_errors[-3:]
        )

        raise ValueError(
            "DataForge could not parse this JSON file. "
            f"{error_summary}"
        )


    # -----------------------------------------------------
    # JSON array
    # -----------------------------------------------------

    if isinstance(
        data,
        list
    ):

        if not data:

            return pd.DataFrame()

        try:

            return pd.json_normalize(
                data
            )

        except Exception:

            return pd.DataFrame(
                data
            )


    # -----------------------------------------------------
    # JSON object
    # -----------------------------------------------------

    if isinstance(
        data,
        dict
    ):

        common_record_keys = [
            "data",
            "records",
            "results",
            "items",
            "rows",
            "values",
            "events"
        ]

        for key in common_record_keys:

            value = data.get(
                key
            )

            if isinstance(
                value,
                list
            ):

                try:

                    return pd.json_normalize(
                        value
                    )

                except Exception:

                    return pd.DataFrame(
                        value
                    )


        try:

            return pd.DataFrame(
                data
            )

        except Exception:

            try:

                return pd.json_normalize(
                    data
                )

            except Exception as error:

                raise ValueError(
                    "The JSON file is valid, but DataForge "
                    "could not convert it into a dataset. "
                    f"Error: {str(error)}"
                )


    raise ValueError(
        "The JSON file is valid, but its top-level "
        "value cannot be converted into a tabular dataset."
    )


# =========================================================
# DATASET LOADER
# =========================================================

def load_dataset(
    filepath,
    extension
):

    extension = (
        str(extension)
        .lower()
        .lstrip(".")
    )


    # -----------------------------------------------------
    # CSV
    # -----------------------------------------------------

    if extension == "csv":

        parser_errors = []

        encodings = [
            "utf-8",
            "utf-8-sig",
            "latin-1"
        ]

        for encoding in encodings:

            try:

                return pd.read_csv(
                    filepath,
                    encoding=encoding
                )

            except Exception as error:

                parser_errors.append(
                    str(error)
                )

        error_summary = " | ".join(
            parser_errors[-2:]
        )

        raise ValueError(
            "DataForge could not parse the CSV file. "
            f"{error_summary}"
        )


    # -----------------------------------------------------
    # JSON
    # -----------------------------------------------------

    if extension == "json":

        return load_json_dataset(
            filepath
        )


    # -----------------------------------------------------
    # Excel
    # -----------------------------------------------------

    if extension == "xlsx":

        return pd.read_excel(
            filepath,
            engine="openpyxl"
        )


    raise ValueError(
        f"Unsupported dataset type: {extension}"
    )


# =========================================================
# ZIP DATASET LOADER
# =========================================================

def extract_zip_dataset(
    zip_path
):

    zip_path = Path(
        zip_path
    )


    if not zip_path.is_file():

        raise ValueError(
            "The uploaded ZIP file could not be found."
        )


    if not zipfile.is_zipfile(
        zip_path
    ):

        raise ValueError(
            "The uploaded file is not a valid ZIP archive."
        )


    temporary_folder = tempfile.mkdtemp(
        prefix="dataforge_zip_"
    )


    try:

        with zipfile.ZipFile(
            zip_path,
            "r"
        ) as zip_reference:

            # Validate archive

            bad_file = (
                zip_reference.testzip()
            )

            if bad_file is not None:

                raise ValueError(
                    "The ZIP archive appears corrupted. "
                    f"Problem file: {bad_file}"
                )


            # Find supported files

            supported_files = []

            for member in zip_reference.infolist():

                if member.is_dir():

                    continue

                extension = (
                    Path(
                        member.filename
                    )
                    .suffix
                    .lower()
                )

                if extension in {
                    ".csv",
                    ".json",
                    ".xlsx"
                }:

                    supported_files.append(
                        member
                    )


            if not supported_files:

                files_found = [
                    member.filename
                    for member
                    in zip_reference.infolist()
                    if not member.is_dir()
                ]

                displayed_files = ", ".join(
                    files_found[:10]
                )

                raise ValueError(
                    "The ZIP archive does not contain "
                    "a CSV, JSON, or XLSX dataset. "
                    f"Files found: {displayed_files}"
                )


            # Prefer tabular files over metadata JSON.

            extension_priority = {
                ".csv": 1,
                ".xlsx": 2,
                ".json": 3
            }

            supported_files.sort(
                key=lambda member:
                    extension_priority.get(
                        Path(
                            member.filename
                        ).suffix.lower(),
                        99
                    )
            )

            selected_member = (
                supported_files[0]
            )


            temporary_root = os.path.abspath(
                temporary_folder
            )

            destination = os.path.abspath(
                os.path.join(
                    temporary_folder,
                    selected_member.filename
                )
            )


            try:

                common_path = os.path.commonpath(
                    [
                        temporary_root,
                        destination
                    ]
                )

            except ValueError:

                raise ValueError(
                    "Unsafe path detected inside ZIP archive."
                )


            if common_path != temporary_root:

                raise ValueError(
                    "Unsafe path detected inside ZIP archive."
                )


            zip_reference.extract(
                selected_member,
                temporary_folder
            )


        if not os.path.isfile(
            destination
        ):

            raise ValueError(
                "The selected dataset could not be "
                "extracted from the ZIP archive."
            )


        extension = (
            Path(
                destination
            )
            .suffix
            .lower()
            .lstrip(".")
        )


        try:

            dataframe = load_dataset(
                destination,
                extension
            )

        except Exception as error:

            raise ValueError(
                "ZIP extraction succeeded, but DataForge "
                f"could not read '{selected_member.filename}'. "
                f"Error: {str(error)}"
            )


        return dataframe.copy()


    except zipfile.BadZipFile:

        raise ValueError(
            "The uploaded ZIP archive is invalid "
            "or corrupted."
        )


    finally:

        shutil.rmtree(
            temporary_folder,
            ignore_errors=True
        )


# =========================================================
# DATASET METRICS
# =========================================================

def calculate_dataset_metrics(
    dataframe
):

    rows = len(
        dataframe
    )

    columns = len(
        dataframe.columns
    )

    missing_values = int(
        dataframe.isnull()
        .sum()
        .sum()
    )


    try:

        duplicates = int(
            dataframe.duplicated()
            .sum()
        )

    except TypeError:

        comparable_dataframe = (
            make_values_hashable(
                dataframe
            )
        )

        duplicates = int(
            comparable_dataframe
            .duplicated()
            .sum()
        )


    total_cells = (
        rows
        *
        columns
    )


    if total_cells > 0:

        missing_ratio = (
            missing_values
            /
            total_cells
        )

    else:

        missing_ratio = 0


    if rows > 0:

        duplicate_ratio = (
            duplicates
            /
            rows
        )

    else:

        duplicate_ratio = 0


    quality_penalty = (
        missing_ratio * 70
        +
        duplicate_ratio * 30
    )


    quality_score = round(
        max(
            0,
            min(
                100,
                100 - quality_penalty
            )
        )
    )


    memory_usage = round(
        dataframe.memory_usage(
            deep=True
        ).sum()
        /
        1024,
        2
    )


    return {
        "rows": rows,
        "columns": columns,
        "missing_values": missing_values,
        "duplicates": duplicates,
        "quality_score": quality_score,
        "memory_usage": memory_usage
    }


# =========================================================
# CLEANING HELPERS
# =========================================================

def standardize_column_name(
    column_name
):

    column_name = (
        str(
            column_name
        )
        .strip()
        .lower()
    )


    column_name = re.sub(
        r"[^a-z0-9]+",
        "_",
        column_name
    )


    column_name = re.sub(
        r"_+",
        "_",
        column_name
    )


    column_name = (
        column_name
        .strip(
            "_"
        )
    )


    if not column_name:

        column_name = "unnamed_column"


    return column_name


def make_unique_column_names(
    column_names
):

    used_names = {}

    final_names = []


    for original_name in column_names:

        base_name = (
            standardize_column_name(
                original_name
            )
        )


        if base_name not in used_names:

            used_names[
                base_name
            ] = 1

            final_names.append(
                base_name
            )


        else:

            used_names[
                base_name
            ] += 1

            sequence_number = (
                used_names[
                    base_name
                ]
            )

            final_names.append(
                f"{base_name}_{sequence_number}"
            )


    return final_names


def trim_text_columns(
    dataframe
):

    cleaned_dataframe = (
        dataframe.copy()
    )


    text_columns = (
        cleaned_dataframe
        .select_dtypes(
            include=[
                "object",
                "string"
            ]
        )
        .columns
    )


    for column in text_columns:

        cleaned_dataframe[column] = (
            cleaned_dataframe[column]
            .apply(
                lambda value:
                    value.strip()
                    if isinstance(
                        value,
                        str
                    )
                    else value
            )
        )


    return cleaned_dataframe


def fill_numeric_missing_values(
    dataframe,
    strategy
):

    cleaned_dataframe = (
        dataframe.copy()
    )


    numeric_columns = (
        cleaned_dataframe
        .select_dtypes(
            include="number"
        )
        .columns
    )


    for column in numeric_columns:

        if strategy == "zero":

            cleaned_dataframe[column] = (
                cleaned_dataframe[column]
                .fillna(
                    0
                )
            )


        elif strategy == "mean":

            replacement = (
                cleaned_dataframe[column]
                .mean()
            )

            if pd.notna(
                replacement
            ):

                cleaned_dataframe[column] = (
                    cleaned_dataframe[column]
                    .fillna(
                        replacement
                    )
                )


        elif strategy == "median":

            replacement = (
                cleaned_dataframe[column]
                .median()
            )

            if pd.notna(
                replacement
            ):

                cleaned_dataframe[column] = (
                    cleaned_dataframe[column]
                    .fillna(
                        replacement
                    )
                )


    return cleaned_dataframe


def fill_text_missing_values(
    dataframe,
    strategy,
    custom_value=""
):

    cleaned_dataframe = (
        dataframe.copy()
    )


    text_columns = (
        cleaned_dataframe
        .select_dtypes(
            include=[
                "object",
                "string"
            ]
        )
        .columns
    )


    for column in text_columns:

        if strategy == "custom":

            replacement = (
                custom_value
                if custom_value
                else "Unknown"
            )

            cleaned_dataframe[column] = (
                cleaned_dataframe[column]
                .fillna(
                    replacement
                )
            )


        elif strategy == "mode":

            modes = (
                cleaned_dataframe[column]
                .mode(
                    dropna=True
                )
            )

            if not modes.empty:

                cleaned_dataframe[column] = (
                    cleaned_dataframe[column]
                    .fillna(
                        modes.iloc[0]
                    )
                )


    return cleaned_dataframe


def apply_cleaning_operations(
    dataframe,
    remove_duplicates=False,
    missing_strategy="keep",
    numeric_fill_strategy="none",
    text_fill_strategy="none",
    custom_text_value="",
    trim_spaces=False,
    standardize_columns=False,
    reset_index=False
):

    cleaned_dataframe = (
        dataframe.copy()
    )

    operations = []


    # -----------------------------------------------------
    # Duplicate removal
    # -----------------------------------------------------

    if remove_duplicates:

        rows_before = len(
            cleaned_dataframe
        )


        try:

            cleaned_dataframe = (
                cleaned_dataframe
                .drop_duplicates(
                    ignore_index=True
                )
            )


        except TypeError:

            comparable_dataframe = (
                make_values_hashable(
                    cleaned_dataframe
                )
            )

            keep_mask = (
                ~comparable_dataframe
                .duplicated(
                    keep="first"
                )
            )

            cleaned_dataframe = (
                cleaned_dataframe[
                    keep_mask
                ]
                .copy()
                .reset_index(
                    drop=True
                )
            )


        rows_removed = (
            rows_before
            -
            len(
                cleaned_dataframe
            )
        )


        operations.append(
            f"Removed {rows_removed:,} duplicate rows"
        )


    # -----------------------------------------------------
    # Missing-value row/column handling
    # -----------------------------------------------------

    if missing_strategy == "drop_rows":

        rows_before = len(
            cleaned_dataframe
        )

        cleaned_dataframe = (
            cleaned_dataframe
            .dropna()
            .copy()
        )

        rows_removed = (
            rows_before
            -
            len(
                cleaned_dataframe
            )
        )

        operations.append(
            f"Dropped {rows_removed:,} rows "
            "containing missing values"
        )


    elif missing_strategy == "drop_columns":

        columns_before = len(
            cleaned_dataframe.columns
        )

        cleaned_dataframe = (
            cleaned_dataframe
            .dropna(
                axis=1
            )
            .copy()
        )

        columns_removed = (
            columns_before
            -
            len(
                cleaned_dataframe.columns
            )
        )

        operations.append(
            f"Dropped {columns_removed:,} columns "
            "containing missing values"
        )


    # -----------------------------------------------------
    # Numeric missing values
    # -----------------------------------------------------

    if numeric_fill_strategy in {
        "zero",
        "mean",
        "median"
    }:

        cleaned_dataframe = (
            fill_numeric_missing_values(
                cleaned_dataframe,
                numeric_fill_strategy
            )
        )

        operations.append(
            "Filled missing numeric values "
            f"using {numeric_fill_strategy}"
        )


    # -----------------------------------------------------
    # Text missing values
    # -----------------------------------------------------

    if text_fill_strategy in {
        "mode",
        "custom"
    }:

        cleaned_dataframe = (
            fill_text_missing_values(
                cleaned_dataframe,
                text_fill_strategy,
                custom_text_value
            )
        )


        if text_fill_strategy == "custom":

            replacement = (
                custom_text_value
                if custom_text_value
                else "Unknown"
            )

            operations.append(
                "Filled missing text values "
                f"with '{replacement}'"
            )


        else:

            operations.append(
                "Filled missing text values using "
                "the most common value"
            )


    # -----------------------------------------------------
    # Text cleanup
    # -----------------------------------------------------

    if trim_spaces:

        cleaned_dataframe = (
            trim_text_columns(
                cleaned_dataframe
            )
        )

        operations.append(
            "Trimmed leading and trailing spaces "
            "from text values"
        )


    # -----------------------------------------------------
    # Column cleanup
    # -----------------------------------------------------

    if standardize_columns:

        cleaned_dataframe.columns = (
            make_unique_column_names(
                cleaned_dataframe.columns
            )
        )

        operations.append(
            "Standardized column names"
        )


    # -----------------------------------------------------
    # Reset index
    # -----------------------------------------------------

    if reset_index:

        cleaned_dataframe = (
            cleaned_dataframe
            .reset_index(
                drop=True
            )
        )

        operations.append(
            "Reset the row index"
        )


    if not operations:

        operations.append(
            "No cleaning operations were selected"
        )


    return (
        cleaned_dataframe,
        operations
    )


# =========================================================
# STORED DATASET HELPERS
# =========================================================

def find_uploaded_dataset(
    filename
):

    safe_filename = clean_filename(
        filename
    )

    filepath = (
        UPLOAD_FOLDER
        /
        safe_filename
    )


    if not filepath.is_file():

        raise ValueError(
            "The original uploaded dataset "
            "could not be found."
        )


    return filepath


def load_uploaded_dataset(
    filename
):

    filepath = find_uploaded_dataset(
        filename
    )


    extension = (
        Path(
            filename
        )
        .suffix
        .lower()
        .lstrip(".")
    )


    if extension == "zip":

        return extract_zip_dataset(
            filepath
        )


    return load_dataset(
        filepath,
        extension
    )


def get_available_datasets():

    connection = get_db_connection()


    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                filename,
                upload_date,
                rows,
                columns_count,
                quality_score
            FROM datasets
            ORDER BY id DESC
            """
        )

        dataset_rows = (
            cursor.fetchall()
        )


    finally:

        connection.close()


    available_datasets = []

    seen_filenames = set()


    for dataset in dataset_rows:

        filename = dataset[1]

        safe_filename = clean_filename(
            filename
        )

        filepath = (
            UPLOAD_FOLDER
            /
            safe_filename
        )


        if (
            filename not in seen_filenames
            and
            filepath.is_file()
        ):

            available_datasets.append(
                dataset
            )

            seen_filenames.add(
                filename
            )


    return available_datasets


# =========================================================
# DASHBOARD
# =========================================================

@app.get(
    "/",
    response_class=HTMLResponse
)
async def dashboard(
    request: Request
):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request
        }
    )


# =========================================================
# UPLOAD PAGE
# =========================================================

@app.get(
    "/upload",
    response_class=HTMLResponse
)
@app.get(
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
            "request": request
        }
    )


# =========================================================
# UPLOAD DATASET
# =========================================================

@app.post(
    "/upload",
    response_class=HTMLResponse
)
@app.post(
    "/upload/",
    response_class=HTMLResponse,
    include_in_schema=False
)
async def upload_file(
    request: Request,
    file: UploadFile = File(...)
):

    global latest_metrics


    try:

        filename = clean_filename(
            file.filename
        )


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


        filepath = (
            UPLOAD_FOLDER
            /
            filename
        )


        with open(
            filepath,
            "wb"
        ) as output_file:

            while True:

                chunk = await file.read(
                    1024 * 1024
                )

                if not chunk:

                    break

                output_file.write(
                    chunk
                )


        await file.close()


        if not filepath.is_file():

            raise ValueError(
                "The uploaded file could not be saved."
            )


        if filepath.stat().st_size == 0:

            raise ValueError(
                "The uploaded file is empty."
            )


        if extension == "zip":

            dataframe = extract_zip_dataset(
                filepath
            )

        else:

            dataframe = load_dataset(
                filepath,
                extension
            )


        if not isinstance(
            dataframe,
            pd.DataFrame
        ):

            raise ValueError(
                "The uploaded file did not produce "
                "a valid dataset."
            )


        metrics = calculate_dataset_metrics(
            dataframe
        )


        timestamp = (
            datetime.datetime.now()
            .strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )


        connection = get_db_connection()


        try:

            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO datasets (
                    filename,
                    upload_date,
                    rows,
                    columns_count,
                    missing_values,
                    duplicates,
                    quality_score,
                    memory_usage
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    filename,
                    timestamp,
                    metrics["rows"],
                    metrics["columns"],
                    metrics["missing_values"],
                    metrics["duplicates"],
                    metrics["quality_score"],
                    metrics["memory_usage"]
                )
            )

            connection.commit()


        finally:

            connection.close()


        dtypes = (
            dataframe.dtypes
            .astype(str)
            .to_dict()
        )


        null_counts = (
            dataframe.isnull()
            .sum()
            .sort_values(
                ascending=False
            )
            .to_dict()
        )


        preview = (
            dataframe.head(10)
            .to_html(
                classes="table",
                index=False,
                border=0,
                escape=True
            )
        )


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

            stats = (
                statistics_dataframe
                .to_html(
                    classes="table",
                    border=0,
                    escape=True
                )
            )

        except Exception:

            stats = (
                "<p>Descriptive statistics are not "
                "available for this dataset.</p>"
            )


        summary = (
            f"Dataset contains {metrics['rows']:,} rows "
            f"and {metrics['columns']:,} columns. "
            f"It contains {metrics['missing_values']:,} "
            f"missing values and {metrics['duplicates']:,} "
            f"duplicate rows. The calculated quality score "
            f"is {metrics['quality_score']}/100."
        )


        latest_metrics = {
            "filename": filename,
            **metrics
        }


        chart_html = ""


        numeric_columns = (
            dataframe
            .select_dtypes(
                include="number"
            )
            .columns
            .tolist()
        )


        if numeric_columns:

            chart_column = (
                numeric_columns[0]
            )


            try:

                figure = px.histogram(
                    dataframe,
                    x=chart_column,
                    title=f"Distribution of {chart_column}",
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


                chart_html = pio.to_html(
                    figure,
                    full_html=False,
                    include_plotlyjs="cdn"
                )


            except Exception:

                chart_html = ""


        return templates.TemplateResponse(
            request=request,
            name="profile.html",
            context={
                "request": request,
                "filename": filename,
                "rows": metrics["rows"],
                "columns": metrics["columns"],
                "missing_values": metrics["missing_values"],
                "duplicates": metrics["duplicates"],
                "quality_score": metrics["quality_score"],
                "memory_usage": metrics["memory_usage"],
                "dtypes": dtypes,
                "null_counts": null_counts,
                "preview": preview,
                "stats": stats,
                "summary": summary,
                "chart_html": chart_html
            }
        )


    except Exception as error:

        error_message = html.escape(
            str(error)
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
# DATASET HISTORY
# =========================================================

@app.get(
    "/datasets",
    response_class=HTMLResponse
)
async def dataset_catalog(
    request: Request
):

    connection = get_db_connection()


    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM datasets
            ORDER BY id DESC
            """
        )

        datasets = (
            cursor.fetchall()
        )


    finally:

        connection.close()


    return templates.TemplateResponse(
        request=request,
        name="datasets.html",
        context={
            "request": request,
            "datasets": datasets
        }
    )


# =========================================================
# ANALYTICS
# =========================================================

@app.get(
    "/analytics",
    response_class=HTMLResponse
)
async def analytics(
    request: Request
):

    connection = get_db_connection()


    try:

        cursor = connection.cursor()


        cursor.execute(
            """
            SELECT COUNT(*)
            FROM datasets
            """
        )

        total_datasets = (
            cursor.fetchone()[0]
            or 0
        )


        cursor.execute(
            """
            SELECT AVG(quality_score)
            FROM datasets
            """
        )

        avg_quality = (
            cursor.fetchone()[0]
            or 0
        )


        cursor.execute(
            """
            SELECT SUM(rows)
            FROM datasets
            """
        )

        total_rows = (
            cursor.fetchone()[0]
            or 0
        )


        cursor.execute(
            """
            SELECT SUM(memory_usage)
            FROM datasets
            """
        )

        total_memory = (
            cursor.fetchone()[0]
            or 0
        )


    finally:

        connection.close()


    return templates.TemplateResponse(
        request=request,
        name="analytics.html",
        context={
            "request": request,
            "total_datasets": total_datasets,
            "avg_quality": round(
                avg_quality,
                1
            ),
            "total_rows": f"{total_rows:,}",
            "total_memory": round(
                total_memory,
                2
            )
        }
    )


# =========================================================
# AI ANALYST
# =========================================================

@app.get(
    "/ai",
    response_class=HTMLResponse
)
async def ai_page(
    request: Request
):

    return templates.TemplateResponse(
        request=request,
        name="ai.html",
        context={
            "request": request,
            "response": ""
        }
    )


@app.post(
    "/ai",
    response_class=HTMLResponse
)
async def ai_analyze(
    request: Request
):

    form = await request.form()


    question = str(
        form.get(
            "question",
            ""
        )
    ).strip()


    safe_question = html.escape(
        question
    )


    response = f"""
Question:
{safe_question}

Suggested Analysis

• Review missing values
• Check duplicate records
• Verify column data types
• Analyze potential outliers
• Validate data quality
• Create automated quality checks
• Review ETL pipeline requirements
"""


    return templates.TemplateResponse(
        request=request,
        name="ai.html",
        context={
            "request": request,
            "response": response
        }
    )


# =========================================================
# CLEANING STUDIO
# =========================================================

@app.get(
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
            "request": request,
            "datasets": available_datasets,
            "selected_filename": "",
            "original_metrics": None,
            "cleaned_metrics": None,
            "original_preview": "",
            "cleaned_preview": "",
            "operations": [],
            "download_filename": "",
            "error_message": ""
        }
    )


@app.post(
    "/clean",
    response_class=HTMLResponse
)
async def run_cleaning_studio(
    request: Request
):

    form = await request.form()


    selected_filename = str(
        form.get(
            "filename",
            ""
        )
    ).strip()


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


    export_format = str(
        form.get(
            "export_format",
            "csv"
        )
    ).lower()


    available_datasets = (
        get_available_datasets()
    )


    try:

        if not selected_filename:

            raise ValueError(
                "Select a dataset before running "
                "the cleaning pipeline."
            )


        dataframe = load_uploaded_dataset(
            selected_filename
        )


        original_metrics = (
            calculate_dataset_metrics(
                dataframe
            )
        )


        cleaned_dataframe, operations = (
            apply_cleaning_operations(
                dataframe=dataframe,
                remove_duplicates=remove_duplicates,
                missing_strategy=missing_strategy,
                numeric_fill_strategy=numeric_fill_strategy,
                text_fill_strategy=text_fill_strategy,
                custom_text_value=custom_text_value,
                trim_spaces=trim_spaces,
                standardize_columns=standardize_columns,
                reset_index=reset_index
            )
        )


        cleaned_metrics = (
            calculate_dataset_metrics(
                cleaned_dataframe
            )
        )


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


        unique_identifier = (
            uuid.uuid4()
            .hex[:8]
        )


        if export_format == "xlsx":

            download_filename = (
                f"{safe_stem}_cleaned_"
                f"{unique_identifier}.xlsx"
            )


            output_path = (
                CLEANED_FOLDER
                /
                download_filename
            )


            cleaned_dataframe.to_excel(
                output_path,
                index=False,
                engine="openpyxl"
            )


        else:

            download_filename = (
                f"{safe_stem}_cleaned_"
                f"{unique_identifier}.csv"
            )


            output_path = (
                CLEANED_FOLDER
                /
                download_filename
            )


            cleaned_dataframe.to_csv(
                output_path,
                index=False,
                encoding="utf-8"
            )


        return templates.TemplateResponse(
            request=request,
            name="clean.html",
            context={
                "request": request,
                "datasets": available_datasets,
                "selected_filename": selected_filename,
                "original_metrics": original_metrics,
                "cleaned_metrics": cleaned_metrics,
                "original_preview": original_preview,
                "cleaned_preview": cleaned_preview,
                "operations": operations,
                "download_filename": download_filename,
                "error_message": ""
            }
        )


    except Exception as error:

        return templates.TemplateResponse(
            request=request,
            name="clean.html",
            context={
                "request": request,
                "datasets": available_datasets,
                "selected_filename": selected_filename,
                "original_metrics": None,
                "cleaned_metrics": None,
                "original_preview": "",
                "cleaned_preview": "",
                "operations": [],
                "download_filename": "",
                "error_message": str(
                    error
                )
            },
            status_code=400
        )


# =========================================================
# DOWNLOAD CLEANED DATASET
# =========================================================

@app.get(
    "/download-cleaned/{filename}"
)
async def download_cleaned_dataset(
    filename: str
):

    safe_filename = safe_download_filename(
        filename
    )


    filepath = (
        CLEANED_FOLDER
        /
        safe_filename
    )


    if not filepath.is_file():

        return HTMLResponse(
            content="""
            <!DOCTYPE html>

            <html lang="en">

            <head>
                <meta charset="UTF-8">
                <title>Cleaned File Not Found</title>
            </head>

            <body>

                <h1>
                    Cleaned dataset not found
                </h1>

                <p>
                    The requested cleaned dataset
                    is no longer available.
                </p>

                <a href="/clean">
                    Return to Cleaning Studio
                </a>

            </body>

            </html>
            """,
            status_code=404
        )


    extension = (
        filepath
        .suffix
        .lower()
    )


    if extension == ".xlsx":

        media_type = (
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )

    else:

        media_type = "text/csv"


    return FileResponse(
        path=str(
            filepath
        ),
        media_type=media_type,
        filename=safe_filename
    )


# =========================================================
# PDF REPORT
# =========================================================

@app.get(
    "/report"
)
async def generate_report():

    report_path = (
        REPORT_FOLDER
        /
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


    pretty_names = {
        "filename": "Dataset",
        "rows": "Rows",
        "columns": "Columns",
        "missing_values": "Missing Values",
        "duplicates": "Duplicate Rows",
        "quality_score": "Quality Score",
        "memory_usage": "Memory Usage (KB)"
    }


    for key, value in latest_metrics.items():

        label = pretty_names.get(
            key,
            key
        )


        safe_label = html.escape(
            str(
                label
            )
        )


        safe_value = html.escape(
            str(
                value
            )
        )


        if key == "quality_score":

            safe_value += "/100"


        content.append(
            Paragraph(
                f"<b>{safe_label}:</b> {safe_value}",
                styles["BodyText"]
            )
        )


        content.append(
            Spacer(
                1,
                8
            )
        )


    document.build(
        content
    )


    return FileResponse(
        path=str(
            report_path
        ),
        media_type="application/pdf",
        filename="DataForge_Report.pdf"
    )


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get(
    "/health"
)
async def health_check():

    database_exists = (
        DATABASE_PATH.is_file()
    )

    templates_exist = (
        TEMPLATE_DIRECTORY.is_dir()
    )


    status = (
        "healthy"
        if database_exists
        and templates_exist
        else "degraded"
    )


    return {
        "status": status,
        "application": "DataForge AI",
        "version": "1.0.0",
        "phase": 6,
        "database": (
            "available"
            if database_exists
            else "missing"
        ),
        "templates": (
            "available"
            if templates_exist
            else "missing"
        ),
        "packaged": bool(
            getattr(
                sys,
                "frozen",
                False
            )
        )
    }


# =========================================================
# DEVELOPMENT STARTUP
#
# The packaged EXE should use launcher.py instead.
# =========================================================

if __name__ == "__main__":

    import uvicorn


    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8010,
        reload=False,
        log_level="info"
    )