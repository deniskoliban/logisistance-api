from fastapi import APIRouter

from app.api.routes import auth, reference, users, vehicles

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(vehicles.router)
api_router.include_router(reference.router)
