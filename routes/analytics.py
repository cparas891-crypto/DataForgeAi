from fastapi import (
    APIRouter,
    Request
)

from fastapi.responses import (
    HTMLResponse
)

from fastapi.templating import (
    Jinja2Templates
)

from config import (
    TEMPLATE_DIRECTORY
)

from database import (
    get_analytics_metrics
)


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    tags=[
        "Analytics"
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
# ANALYTICS
# =========================================================

@router.get(
    "/analytics",
    response_class=HTMLResponse
)
async def analytics(
    request: Request
):

    metrics = (
        get_analytics_metrics()
    )

    return templates.TemplateResponse(
        request=request,
        name="analytics.html",
        context={
            "request":
                request,

            "total_datasets":
                metrics[
                    "total_datasets"
                ],

            "avg_quality":
                round(
                    metrics[
                        "avg_quality"
                    ],
                    1
                ),

            "total_rows":
                f"{metrics['total_rows']:,}",

            "total_memory":
                round(
                    metrics[
                        "total_memory"
                    ],
                    2
                )
        }
    )