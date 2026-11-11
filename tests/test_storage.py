from services.storage import (
    safe_filename,
    save_bytes,
    file_exists,
    get_file_size,
    delete_file,
    get_storage_mode
)
import pandas as pd

from services.storage import (
    save_dataframe
)


def test_save_csv_dataframe():

    filename = (
        "storage_dataframe_test.csv"
    )

    dataframe = pd.DataFrame(
        {
            "name": [
                "Alice",
                "Bob"
            ],
            "score": [
                90,
                85
            ]
        }
    )

    filepath = save_dataframe(
        "cleaned",
        filename,
        dataframe
    )

    assert filepath.is_file()

    loaded = pd.read_csv(
        filepath
    )

    assert len(loaded) == 2

    filepath.unlink()


def test_save_xlsx_dataframe():

    filename = (
        "storage_dataframe_test.xlsx"
    )

    dataframe = pd.DataFrame(
        {
            "name": [
                "Alice",
                "Bob"
            ],
            "score": [
                90,
                85
            ]
        }
    )

    filepath = save_dataframe(
        "cleaned",
        filename,
        dataframe
    )

    assert filepath.is_file()

    loaded = pd.read_excel(
        filepath,
        engine="openpyxl"
    )

    assert len(loaded) == 2

    filepath.unlink()

def test_storage_mode():

    assert get_storage_mode() == "local"


def test_safe_filename():

    filename = safe_filename(
        "../Bad File Name!.csv"
    )

    assert filename == (
        "Bad_File_Name_.csv"
    )


def test_save_file():

    filename = (
        "storage_test.csv"
    )

    data = (
        b"name,score\n"
        b"Alice,90\n"
    )

    filepath = save_bytes(
        "uploads",
        filename,
        data
    )

    assert filepath.is_file()

    assert file_exists(
        "uploads",
        filename
    )


def test_file_size():

    filename = (
        "storage_size_test.csv"
    )

    data = (
        b"name,score\n"
        b"Alice,90\n"
    )

    save_bytes(
        "uploads",
        filename,
        data
    )

    size = get_file_size(
        "uploads",
        filename
    )

    assert size > 0

    delete_file(
        "uploads",
        filename
    )


def test_delete_file():

    filename = (
        "storage_delete_test.csv"
    )

    save_bytes(
        "uploads",
        filename,
        b"test"
    )

    assert file_exists(
        "uploads",
        filename
    )

    result = delete_file(
        "uploads",
        filename
    )

    assert result is True

    assert not file_exists(
        "uploads",
        filename
    )