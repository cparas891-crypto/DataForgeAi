import json

import pandas as pd


# =========================================================
# MAKE COMPLEX VALUES HASHABLE
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
# CALCULATE DATASET METRICS
# =========================================================

def calculate_dataset_metrics(
    dataframe
):

    # -----------------------------------------------------
    # Rows
    # -----------------------------------------------------

    rows = len(
        dataframe
    )


    # -----------------------------------------------------
    # Columns
    # -----------------------------------------------------

    columns = len(
        dataframe.columns
    )


    # -----------------------------------------------------
    # Missing values
    # -----------------------------------------------------

    missing_values = int(
        dataframe
        .isnull()
        .sum()
        .sum()
    )


    # -----------------------------------------------------
    # Duplicate rows
    # -----------------------------------------------------

    try:

        duplicates = int(
            dataframe
            .duplicated()
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


    # -----------------------------------------------------
    # Total cells
    # -----------------------------------------------------

    total_cells = (
        rows
        *
        columns
    )


    # -----------------------------------------------------
    # Missing-value ratio
    # -----------------------------------------------------

    if total_cells > 0:

        missing_ratio = (
            missing_values
            /
            total_cells
        )

    else:

        missing_ratio = 0


    # -----------------------------------------------------
    # Duplicate ratio
    # -----------------------------------------------------

    if rows > 0:

        duplicate_ratio = (
            duplicates
            /
            rows
        )

    else:

        duplicate_ratio = 0


    # -----------------------------------------------------
    # Data-quality score
    #
    # Missing values:
    # 70% weighting
    #
    # Duplicate rows:
    # 30% weighting
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # Memory usage
    # -----------------------------------------------------

    memory_usage = round(
        dataframe
        .memory_usage(
            deep=True
        )
        .sum()
        /
        1024,
        2
    )


    # -----------------------------------------------------
    # Results
    # -----------------------------------------------------

    return {
        "rows":
            rows,

        "columns":
            columns,

        "missing_values":
            missing_values,

        "duplicates":
            duplicates,

        "quality_score":
            quality_score,

        "memory_usage":
            memory_usage
    }