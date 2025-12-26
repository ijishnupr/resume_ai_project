from fastapi.params import Depends
from fastapi import APIRouter
from src.shared.dependency import has_access
from src.authv1.route import route as authv1_route
from src.auth.route import route as auth_route

from src.interview.route import route as interview_route

router = APIRouter()
PROTECTED = [Depends(has_access)]

router.include_router(auth_route, prefix="/auth")
router.include_router(authv1_route, prefix="/authv1")
router.include_router(interview_route, prefix="/interview", dependencies=PROTECTED)
