from fastapi import APIRouter

router = APIRouter()


@router.get("", tags=["Healthcheck"])
async def healthcheck():
    """Healthcheck endpoint for the API. This endpoint is used to determine if the API is up and running"""
    return {"status": "ok"}
