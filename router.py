from fastapi import APIRouter
from auth.route import route as auth_route
router = APIRouter()

router.include_router(auth_route, prefix="/auth")