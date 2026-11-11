import sys

from fastapi import (
    APIRouter,
    Request
)

from fastapi.responses import (
    HTMLResponse,
    FileResponse
)

from fastapi.templating import (
    Jinja2Templates
)

from config import (
    DATABASE_PATH,
    TEMPLATE_DIRECTORY
)

from database import (
    check_database_connection,
    get_database_type
)

from services.reports import (
    create_executive_report
)


from services.storage import (
    check_storage,
    get_storage_mode
)


import routes.upload as upload_routes


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    tags=[
        "Core"
    ]
)


# =========================================================
# TEMPLATES
# =========================================================

templates = Jinja2Templates(
    directory=str(
        TEMPLATE_DIRECTORY
    )
)


# =========================================================
# DASHBOARD
# =========================================================

@router.get(
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
            "request":
                request
        }
    )


# =========================================================
# PDF REPORT
# =========================================================

@router.get(
    "/report"
)
async def generate_report():

    report_path = (
        create_executive_report(
            upload_routes.latest_upload_metrics
        )
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

@router.get(
    "/health"
)
async def health_check():

    database_available = (
        check_database_connection()
    )

    storage_available = (
        check_storage()
    )

    templates_available = (
        TEMPLATE_DIRECTORY.is_dir()
    )


    status = (
        "healthy"
        if (
            database_available
            and storage_available
            and templates_available
        )
        else "degraded"
    )


    return {
        "status":
            status,

        "application":
            "DataForge AI",

        "version":
            "1.0.0",

        "phase":
            7,

        "database":
            (
                "available"
                if database_available
                else "unavailable"
            ),

        "database_type":
            get_database_type(),

        "storage":
            (
                "available"
                if storage_available
                else "unavailable"
            ),

        "storage_mode":
            get_storage_mode(),

        "templates":
            (
                "available"
                if templates_available
                else "missing"
            ),

        "packaged":
            bool(
                getattr(
                    sys,
                    "frozen",
                    False
                )
            )
    }