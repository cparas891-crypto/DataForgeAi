import json
import os
import re
import shutil
import tempfile
import zipfile

from pathlib import Path

import pandas as pd

from config import UPLOAD_FOLDER


# =========================================================
# FILENAME
# =========================================================

def clean_filename(filename):

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


# =========================================================
# JSON LOADER
# =========================================================

def load_json_dataset(filepath):

    parser_errors = []

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


    # JSON Lines / NDJSON

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


    # Python JSON parser

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


    # JSON array

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


    # JSON object

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
        "The JSON file is valid, but its top-level value "
        "cannot be converted into a tabular dataset."
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


    if extension == "csv":

        parser_errors = []

        for encoding in [
            "utf-8",
            "utf-8-sig",
            "latin-1"
        ]:

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


    if extension == "json":

        return load_json_dataset(
            filepath
        )


    if extension == "xlsx":

        return pd.read_excel(
            filepath,
            engine="openpyxl"
        )


    raise ValueError(
        f"Unsupported dataset type: {extension}"
    )


# =========================================================
# ZIP LOADER
# =========================================================

def extract_zip_dataset(zip_path):

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

            bad_file = zip_reference.testzip()

            if bad_file is not None:

                raise ValueError(
                    "The ZIP archive appears corrupted. "
                    f"Problem file: {bad_file}"
                )


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
                        )
                        .suffix
                        .lower(),
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
# STORED DATASET HELPERS
# =========================================================

def find_uploaded_dataset(filename):

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


def load_uploaded_dataset(filename):

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