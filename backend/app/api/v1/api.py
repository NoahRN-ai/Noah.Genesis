from fastapi import APIRouter

from backend.app.api.v1.endpoints import chat, history, patient_data, user_profiles

api_router_v1 = APIRouter()

api_router_v1.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router_v1.include_router(history.router, prefix="/sessions", tags=["Session History"])
api_router_v1.include_router(patient_data.router, prefix="/patient-data-logs", tags=["Patient Data Logs"])
api_router_v1.include_router(user_profiles.router, prefix="/users", tags=["User Profiles"])
# Add other v1 routers here as the application grows
