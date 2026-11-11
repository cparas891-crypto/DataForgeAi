import json
import re

import pandas as pd


# =========================================================
# MAKE COMPLEX VALUES HASHABLE
#
# Used when duplicate detection encounters values
# such as lists or dictionaries.
# =========================================================

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
# STANDARDIZE COLUMN NAME
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

    # Replace spaces and special characters
    # with underscores.

    column_name = re.sub(
        r"[^a-z0-9]+",
        "_",
        column_name
    )

    # Collapse repeated underscores.

    column_name = re.sub(
        r"_+",
        "_",
        column_name
    )

    # Remove underscores at the ends.

    column_name = (
        column_name
        .strip(
            "_"
        )
    )

    # Prevent empty column names.

    if not column_name:

        column_name = (
            "unnamed_column"
        )

    return column_name


# =========================================================
# MAKE COLUMN NAMES UNIQUE
# =========================================================

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

            unique_name = (
                f"{base_name}_"
                f"{sequence_number}"
            )

            final_names.append(
                unique_name
            )

    return final_names


# =========================================================
# TRIM TEXT COLUMNS
# =========================================================

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


# =========================================================
# FILL NUMERIC MISSING VALUES
# =========================================================

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

        # -------------------------------------------------
        # Zero
        # -------------------------------------------------

        if strategy == "zero":

            cleaned_dataframe[column] = (
                cleaned_dataframe[column]
                .fillna(
                    0
                )
            )


        # -------------------------------------------------
        # Mean
        # -------------------------------------------------

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


        # -------------------------------------------------
        # Median
        # -------------------------------------------------

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


# =========================================================
# FILL TEXT MISSING VALUES
# =========================================================

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

        # -------------------------------------------------
        # Custom replacement
        # -------------------------------------------------

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


        # -------------------------------------------------
        # Most common value
        # -------------------------------------------------

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


# =========================================================
# REMOVE DUPLICATE ROWS
# =========================================================

def remove_duplicate_rows(
    dataframe
):

    cleaned_dataframe = (
        dataframe.copy()
    )

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

        # Some JSON datasets can contain dict/list
        # values that normal duplicate detection
        # cannot hash.

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

    return (
        cleaned_dataframe,
        rows_removed
    )


# =========================================================
# APPLY CLEANING OPERATIONS
# =========================================================

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
    # REMOVE DUPLICATES
    # -----------------------------------------------------

    if remove_duplicates:

        cleaned_dataframe, rows_removed = (
            remove_duplicate_rows(
                cleaned_dataframe
            )
        )

        operations.append(
            f"Removed {rows_removed:,} "
            "duplicate rows"
        )


    # -----------------------------------------------------
    # DROP ROWS WITH MISSING VALUES
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


    # -----------------------------------------------------
    # DROP COLUMNS WITH MISSING VALUES
    # -----------------------------------------------------

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
    # FILL NUMERIC VALUES
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
    # FILL TEXT VALUES
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

        if (
            text_fill_strategy
            == "custom"
        ):

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
                "Filled missing text values "
                "using the most common value"
            )


    # -----------------------------------------------------
    # TRIM TEXT
    # -----------------------------------------------------

    if trim_spaces:

        cleaned_dataframe = (
            trim_text_columns(
                cleaned_dataframe
            )
        )

        operations.append(
            "Trimmed leading and trailing "
            "spaces from text values"
        )


    # -----------------------------------------------------
    # STANDARDIZE COLUMN NAMES
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
    # RESET INDEX
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


    # -----------------------------------------------------
    # NO OPERATIONS
    # -----------------------------------------------------

    if not operations:

        operations.append(
            "No cleaning operations were selected"
        )


    return (
        cleaned_dataframe,
        operations
    )