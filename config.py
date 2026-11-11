import sys

from pathlib import Path


# =========================================================
# APPLICATION PATHS
# =========================================================


def get_resource_directory():

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


# =========================================================
# BASE DIRECTORIES
# =========================================================

RESOURCE_DIR = (
    get_resource_directory()
)

DATA_DIR = (
    get_data_directory()
)


# =========================================================
# TEMPLATE DIRECTORY
# =========================================================

TEMPLATE_DIRECTORY = (
    RESOURCE_DIR
    / "templates"
)


# =========================================================
# DATA DIRECTORIES
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


# =========================================================
# DATABASE
# =========================================================

DATABASE_PATH = (
    DATA_DIR
    / "dataforge.db"
)


# =========================================================
# CREATE DIRECTORIES
# =========================================================

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