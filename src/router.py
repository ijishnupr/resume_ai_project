from fastapi import APIRouter

from src.auth.route import route as auth_route
from src.interview.route import route as interview_route

router = APIRouter()

router.include_router(auth_route, prefix="/auth")
router.include_router(interview_route, prefix="/interview")
