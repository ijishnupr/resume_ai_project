from src.shared.dependency import UserPayload


async def list_interview(user: UserPayload, db):
    conn, cur = db

    get_interview_query = """
    SELECT 
        id, user_id, created_at, last_date::date
    FROM 
        interview
    WHERE user_id = %(user_id)s
    """
    await cur.execute(get_interview_query, {"user_id": user.user_id})
    interviews = await cur.fetchall()

    return {"interviews": interviews}
