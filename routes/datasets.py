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
    get_dataset_history
)


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    tags=[
        "Datasets"
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
# DATASET HISTORY
# =========================================================

@router.get(
    "/datasets",
    response_class=HTMLResponse
)
async def dataset_catalog(
    request: Request
):

    datasets = (
        get_dataset_history()
    )

    return templates.TemplateResponse(
        request=request,
        name="datasets.html",
        context={
            "request":
                request,

            "datasets":
                datasets
        }
    )