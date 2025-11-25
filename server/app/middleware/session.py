import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Проверяем или устанавливаем session_id
        session_id = request.cookies.get("session_id")
        if not session_id:
            session_id = f"anon_{uuid.uuid4().hex}"
        
        response = await call_next(request)
        
        # Устанавливаем cookie, если ее не было
        if not request.cookies.get("session_id"):
            response.set_cookie(
                key="session_id",
                value=session_id,
                max_age=30*24*60*60,  # 30 дней
                httponly=True,
                samesite="lax"
            )
        
        return response
