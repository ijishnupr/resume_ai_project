from fastapi import status
from fastapi.responses import JSONResponse

from src.shared.dependency import UserPayload


async def me(user: UserPayload, db):
    conn, cur = db
    get_user_info_query = """
    SELECT
        email
    FROM
        candidate_user
    WHERE
        id = %(interview_candidate_id)s
    """
    await cur.execute(get_user_info_query, {"interview_candidate_id": user.user_id})
    user = await cur.fetchone()
    if not user:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Interview Not Found"},
        )
    else:
        return user
