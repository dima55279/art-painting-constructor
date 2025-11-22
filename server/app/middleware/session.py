import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Устанавливаем session_id для неавторизованных пользователей
        if not request.cookies.get("session_id"):
            session_id = f"anon_{uuid.uuid4().hex}"
            response.set_cookie(
                key="session_id",
                value=session_id,
                max_age=30*24*60*60,  # 30 дней
                httponly=True,
                samesite="lax"
            )
        
        return response
