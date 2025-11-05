from fastapi import APIRouter

from api.dependencies import GetUserDep

router = APIRouter()


@router.get("/whoami", response_model=int)
def get_user_id(
    db_user: GetUserDep,
):
    """
    Get the user id of the authenticated user.
    """
    return db_user.user_id
