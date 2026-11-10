import pandas as pd

from app import calculate_dataset_metrics


def test_perfect_dataset():

    dataframe = pd.DataFrame(
        {
            "name": ["Alice", "Bob", "Charlie"],
            "score": [90, 85, 95]
        }
    )

    metrics = calculate_dataset_metrics(dataframe)

    assert metrics["rows"] == 3
    assert metrics["columns"] == 2
    assert metrics["missing_values"] == 0
    assert metrics["duplicates"] == 0
    assert metrics["quality_score"] == 100


def test_dataset_with_missing_values():

    dataframe = pd.DataFrame(
        {
            "name": ["Alice", "Bob", None],
            "score": [90, None, 95]
        }
    )

    metrics = calculate_dataset_metrics(dataframe)

    assert metrics["rows"] == 3
    assert metrics["columns"] == 2
    assert metrics["missing_values"] == 2
    assert metrics["quality_score"] < 100


def test_dataset_with_duplicates():

    dataframe = pd.DataFrame(
        {
            "name": ["Alice", "Bob", "Alice"],
            "score": [90, 85, 90]
        }
    )

    metrics = calculate_dataset_metrics(dataframe)

    assert metrics["duplicates"] == 1
    assert metrics["quality_score"] < 100


def test_empty_dataset():

    dataframe = pd.DataFrame()

    metrics = calculate_dataset_metrics(dataframe)

    assert metrics["rows"] == 0
    assert metrics["columns"] == 0
    assert metrics["missing_values"] == 0
    assert metrics["duplicates"] == 0
    assert metrics["quality_score"] == 100


def test_mixed_dataset():

    dataframe = pd.DataFrame(
        {
            "name": [
                "Alice",
                "Bob",
                "Alice",
                None
            ],
            "score": [
                90,
                85,
                90,
                None
            ]
        }
    )

    metrics = calculate_dataset_metrics(dataframe)

    assert metrics["rows"] == 4
    assert metrics["columns"] == 2
    assert metrics["missing_values"] == 2
    assert metrics["duplicates"] == 1
    assert metrics["quality_score"] < 100