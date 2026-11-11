import html

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


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    tags=[
        "AI Analyst"
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
# AI ANALYST PAGE
# =========================================================

@router.get(
    "/ai",
    response_class=HTMLResponse
)
async def ai_page(
    request: Request
):

    return templates.TemplateResponse(
        request=request,
        name="ai.html",
        context={
            "request":
                request,

            "response":
                ""
        }
    )


# =========================================================
# AI ANALYST RESPONSE
# =========================================================

@router.post(
    "/ai",
    response_class=HTMLResponse
)
async def ai_analyze(
    request: Request
):

    form = await request.form()

    question = str(
        form.get(
            "question",
            ""
        )
    ).strip()

    safe_question = html.escape(
        question
    )

    response = f"""
Question:
{safe_question}

Suggested Analysis

• Review missing values
• Check duplicate records
• Verify column data types
• Analyze potential outliers
• Validate data quality
• Create automated quality checks
• Review ETL pipeline requirements
"""

    return templates.TemplateResponse(
        request=request,
        name="ai.html",
        context={
            "request":
                request,

            "response":
                response
        }
    )