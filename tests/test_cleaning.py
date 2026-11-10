import pandas as pd

from app import (
    apply_cleaning_operations,
    standardize_column_name,
    make_unique_column_names,
    trim_text_columns,
)


def test_remove_duplicates():

    dataframe = pd.DataFrame(
        {
            "name": [
                "Alice",
                "Bob",
                "Alice"
            ],
            "score": [
                90,
                85,
                90
            ]
        }
    )

    cleaned, operations = apply_cleaning_operations(
        dataframe,
        remove_duplicates=True
    )

    assert len(cleaned) == 2
    assert cleaned.duplicated().sum() == 0


def test_fill_numeric_missing_with_zero():

    dataframe = pd.DataFrame(
        {
            "score": [
                90,
                None,
                75
            ]
        }
    )

    cleaned, operations = apply_cleaning_operations(
        dataframe,
        numeric_fill_strategy="zero"
    )

    assert cleaned["score"].isnull().sum() == 0
    assert cleaned.loc[1, "score"] == 0


def test_fill_numeric_missing_with_median():

    dataframe = pd.DataFrame(
        {
            "score": [
                10,
                None,
                30
            ]
        }
    )

    cleaned, operations = apply_cleaning_operations(
        dataframe,
        numeric_fill_strategy="median"
    )

    assert cleaned["score"].isnull().sum() == 0
    assert cleaned.loc[1, "score"] == 20


def test_fill_text_missing_custom():

    dataframe = pd.DataFrame(
        {
            "status": [
                "Active",
                None,
                "Inactive"
            ]
        }
    )

    cleaned, operations = apply_cleaning_operations(
        dataframe,
        text_fill_strategy="custom",
        custom_text_value="Unknown"
    )

    assert cleaned["status"].isnull().sum() == 0
    assert cleaned.loc[1, "status"] == "Unknown"


def test_trim_text():

    dataframe = pd.DataFrame(
        {
            "name": [
                " Alice ",
                "Bob   ",
                "   Charlie"
            ]
        }
    )

    cleaned = trim_text_columns(
        dataframe
    )

    assert cleaned.loc[0, "name"] == "Alice"
    assert cleaned.loc[1, "name"] == "Bob"
    assert cleaned.loc[2, "name"] == "Charlie"


def test_standardize_column_name():

    assert (
        standardize_column_name(
            "Customer Name"
        )
        == "customer_name"
    )

    assert (
        standardize_column_name(
            "Order-ID"
        )
        == "order_id"
    )

    assert (
        standardize_column_name(
            " Account Status "
        )
        == "account_status"
    )


def test_duplicate_column_names_become_unique():

    columns = [
        "Customer Name",
        "Customer-Name",
        "Customer Name"
    ]

    cleaned_columns = make_unique_column_names(
        columns
    )

    assert cleaned_columns == [
        "customer_name",
        "customer_name_2",
        "customer_name_3"
    ]


def test_drop_rows_with_missing_values():

    dataframe = pd.DataFrame(
        {
            "name": [
                "Alice",
                None,
                "Charlie"
            ],
            "score": [
                90,
                85,
                None
            ]
        }
    )

    cleaned, operations = apply_cleaning_operations(
        dataframe,
        missing_strategy="drop_rows"
    )

    assert len(cleaned) == 1
    assert cleaned.isnull().sum().sum() == 0


def test_multiple_cleaning_operations():

    dataframe = pd.DataFrame(
        {
            "Customer Name": [
                " Alice ",
                " Bob ",
                " Alice "
            ],
            "Score": [
                90,
                None,
                90
            ]
        }
    )

    cleaned, operations = apply_cleaning_operations(
        dataframe,
        remove_duplicates=True,
        numeric_fill_strategy="median",
        trim_spaces=True,
        standardize_columns=True,
        reset_index=True
    )

    assert list(cleaned.columns) == [
        "customer_name",
        "score"
    ]

    assert cleaned["score"].isnull().sum() == 0

    assert cleaned.loc[0, "customer_name"] == "Alice"

    assert list(cleaned.index) == list(
        range(len(cleaned))
    )