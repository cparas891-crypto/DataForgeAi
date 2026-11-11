from fastapi import FastAPI

from database import (
    initialize_database
)


# =========================================================
# SERVICE EXPORTS
#
# These imports are intentionally retained so our existing
# automated tests can continue importing service functions
# from app.py.
# =========================================================

from services.loaders import (
    clean_filename,
    load_json_dataset,
    load_dataset,
    extract_zip_dataset,
    find_uploaded_dataset,
    load_uploaded_dataset
)

from services.profiler import (
    make_values_hashable,
    calculate_dataset_metrics
)

from services.cleaner import (
    standardize_column_name,
    make_unique_column_names,
    trim_text_columns,
    fill_numeric_missing_values,
    fill_text_missing_values,
    apply_cleaning_operations
)


# =========================================================
# ROUTERS
# =========================================================

from routes.core import (
    router as core_router
)

from routes.upload import (
    router as upload_router
)

from routes.datasets import (
    router as datasets_router
)

from routes.cleaning import (
    router as cleaning_router
)

from routes.analytics import (
    router as analytics_router
)

from routes.ai import (
    router as ai_router
)


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="DataForge AI",
    description=(
        "Dataset profiling, cleaning, analytics, "
        "and reporting platform"
    ),
    version="1.0.0"
)


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

initialize_database()


# =========================================================
# REGISTER ROUTERS
# =========================================================

app.include_router(
    core_router
)

app.include_router(
    upload_router
)

app.include_router(
    datasets_router
)

app.include_router(
    cleaning_router
)

app.include_router(
    analytics_router
)

app.include_router(
    ai_router
)


# =========================================================
# DEVELOPMENT STARTUP
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