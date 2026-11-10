import json
import zipfile

import pandas as pd

from app import (
    load_dataset,
    extract_zip_dataset
)


def test_csv_loader(tmp_path):

    file_path = tmp_path / "test.csv"

    file_path.write_text(
        "name,score\n"
        "Alice,90\n"
        "Bob,85\n",
        encoding="utf-8"
    )

    dataframe = load_dataset(
        file_path,
        "csv"
    )

    assert len(dataframe) == 2
    assert list(dataframe.columns) == [
        "name",
        "score"
    ]
    assert dataframe.loc[0, "name"] == "Alice"


def test_json_loader(tmp_path):

    file_path = tmp_path / "test.json"

    data = [
        {
            "name": "Alice",
            "score": 90
        },
        {
            "name": "Bob",
            "score": 85
        }
    ]

    file_path.write_text(
        json.dumps(data),
        encoding="utf-8"
    )

    dataframe = load_dataset(
        file_path,
        "json"
    )

    assert len(dataframe) == 2
    assert "name" in dataframe.columns
    assert "score" in dataframe.columns


def test_json_lines_loader(tmp_path):

    file_path = tmp_path / "test.json"

    file_path.write_text(
        '{"name":"Alice","score":90}\n'
        '{"name":"Bob","score":85}\n',
        encoding="utf-8"
    )

    dataframe = load_dataset(
        file_path,
        "json"
    )

    assert len(dataframe) == 2
    assert dataframe.loc[1, "name"] == "Bob"


def test_xlsx_loader(tmp_path):

    file_path = tmp_path / "test.xlsx"

    source_dataframe = pd.DataFrame(
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

    source_dataframe.to_excel(
        file_path,
        index=False,
        engine="openpyxl"
    )

    dataframe = load_dataset(
        file_path,
        "xlsx"
    )

    assert len(dataframe) == 2

    assert list(
        dataframe.columns
    ) == [
        "name",
        "score"
    ]


def test_zip_with_csv(tmp_path):

    csv_path = (
        tmp_path
        / "dataset.csv"
    )

    csv_path.write_text(
        "name,score\n"
        "Alice,90\n"
        "Bob,85\n",
        encoding="utf-8"
    )

    zip_path = (
        tmp_path
        / "dataset.zip"
    )

    with zipfile.ZipFile(
        zip_path,
        "w"
    ) as archive:

        archive.write(
            csv_path,
            arcname="dataset.csv"
        )

    dataframe = extract_zip_dataset(
        zip_path
    )

    assert len(dataframe) == 2
    assert "name" in dataframe.columns


def test_zip_prefers_csv_over_json(tmp_path):

    csv_path = (
        tmp_path
        / "actual_data.csv"
    )

    csv_path.write_text(
        "name,score\n"
        "Alice,90\n",
        encoding="utf-8"
    )

    json_path = (
        tmp_path
        / "metadata.json"
    )

    json_path.write_text(
        json.dumps(
            {
                "description":
                    "metadata"
            }
        ),
        encoding="utf-8"
    )

    zip_path = (
        tmp_path
        / "mixed.zip"
    )

    with zipfile.ZipFile(
        zip_path,
        "w"
    ) as archive:

        archive.write(
            json_path,
            arcname="metadata.json"
        )

        archive.write(
            csv_path,
            arcname="actual_data.csv"
        )

    dataframe = extract_zip_dataset(
        zip_path
    )

    assert "name" in dataframe.columns
    assert "score" in dataframe.columns
    assert len(dataframe) == 1


def test_invalid_extension(tmp_path):

    file_path = (
        tmp_path
        / "test.txt"
    )

    file_path.write_text(
        "hello",
        encoding="utf-8"
    )

    try:

        load_dataset(
            file_path,
            "txt"
        )

        assert False

    except ValueError as error:

        assert (
            "Unsupported dataset type"
            in str(error)
        )