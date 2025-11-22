# app/api/auth.py
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token, UserLogin
from app.services.auth_service import AuthService
from app.utils.security import create_access_token
from app.config import settings

router = APIRouter()

@router.post("/login")
async def login_compat(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Совместимый эндпоинт для логина
    """
    auth_service = AuthService(db)
    
    print("=== LOGIN COMPAT REQUEST ===")
    
    # Получаем данные разными способами
    content_type = request.headers.get("content-type", "")
    raw_data = {}
    
    try:
        if "application/json" in content_type:
            raw_data = await request.json()
        elif "application/x-www-form-urlencoded" in content_type:
            form_data = await request.form()
            raw_data = dict(form_data)
        else:
            # Пробуем оба способа
            try:
                raw_data = await request.json()
            except:
                try:
                    form_data = await request.form()
                    raw_data = dict(form_data)
                except:
                    pass
    except Exception as e:
        print(f"Error parsing data: {e}")
    
    print(f"Received data: {raw_data}")
    
    # Проверяем обязательные поля
    if not raw_data or 'username' not in raw_data or 'password' not in raw_data:
        return {
            "error": "Missing credentials",
            "instruction": "Send username and password in request body",
            "example_json": {
                "username": "your_username",
                "password": "your_password"
            },
            "example_form": "username=your_username&password=your_password"
        }
    
    username = raw_data['username']
    password = raw_data['password']
    
    # Аутентифицируем пользователя
    user = await auth_service.authenticate_user(username, password)
    if not user:
        return {
            "error": "Invalid username or password",
            "received_username": username
        }
    
    if not user.is_active:
        return {"error": "Account is deactivated"}
    
    await auth_service.update_last_login(user.id)
    
    # Создаем токен
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    # Получаем данные пользователя
    user_dict = await auth_service.get_user_dict(user.id)
    user_response = UserResponse(**user_dict)
    
    print(f"✅ Login successful for user: {username}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user_response,
        "instructions": {
            "save_token": "Save this access_token in localStorage or app state",
            "usage": "Include in headers: Authorization: Bearer YOUR_TOKEN",
            "example": f"Authorization: Bearer {access_token[:50]}...",
            "protected_endpoints": [
                "/api/auth/logout-compat",
                "/api/auth/check-auth", 
                "/api/auth/me",
                "/api/users/profile"
            ]
        }
    }

@router.post("/logout")
async def logout_compat(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Совместимый эндпоинт для logout с инвалидацией токена
    """
    print("=== LOGOUT COMPAT REQUEST ===")
    
    # Получаем все заголовки
    headers = dict(request.headers)
    
    # Пытаемся получить токен
    token = None
    auth_header = headers.get('authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
    
    if token:
        print(f"Token found: {token[:50]}...")
        
        try:
            # Декодируем токен чтобы получить user_id
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM]
            )
            user_id = payload.get("sub")
            
            if user_id:
                auth_service = AuthService(db)
                
                # Инвалидируем токен
                await auth_service.invalidate_token(token)
                
                # Логируем выход
                await auth_service.logout_user(int(user_id))
                
                print("✅ Logout compat successful - token invalidated")
                return {
                    "message": "Успешный выход из системы",
                    "user_id": user_id,
                    "token_invalidated": True
                }
        
        except JWTError as e:
            print(f"Token validation error: {str(e)}")
            return {"message": "Выход выполнен (ошибка токена)"}
    
    print("❌ No token found in request")
    return {
        "message": "Выход выполнен (токен не найден)",
        "token_invalidated": False
    }

@router.post("/register")
async def register_compat(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Совместимый эндпоинт для регистрации с обработкой разных форматов
    """
    auth_service = AuthService(db)
    
    print("=== REGISTER COMPAT REQUEST ===")
    
    # Получаем все возможные данные
    content_type = request.headers.get("content-type", "")
    body = await request.body()
    
    print(f"Content-Type: {content_type}")
    print(f"Raw body: {body}")
    
    # Пытаемся получить данные разными способами
    raw_data = {}
    
    try:
        if "application/json" in content_type and body:
            raw_data = await request.json()
            print(f"JSON data: {raw_data}")
        elif "application/x-www-form-urlencoded" in content_type and body:
            form_data = await request.form()
            raw_data = dict(form_data)
            print(f"Form data: {raw_data}")
        else:
            # Если тело пустое, пытаемся получить из query parameters
            query_params = dict(request.query_params)
            if query_params:
                raw_data = query_params
                print(f"Query params: {raw_data}")
    except Exception as e:
        print(f"Error parsing data: {e}")
    
    # Если данные все еще пустые, возвращаем инструкцию
    if not raw_data:
        return {
            "error": "No data received",
            "instruction": "Send data as JSON in request body or as form data",
            "required_fields": ["username", "email", "password", "password_confirm"],
            "example_json": {
                "username": "testuser",
                "email": "test@example.com", 
                "password": "password123",
                "password_confirm": "password123"
            }
        }
    
    # Проверяем обязательные поля
    required_fields = ['username', 'email', 'password']
    missing_fields = [field for field in required_fields if field not in raw_data]
    
    if missing_fields:
        return {
            "error": f"Missing required fields: {', '.join(missing_fields)}",
            "received_data": raw_data,
            "required_fields": required_fields
        }
    
    try:
        # Создаем UserCreate
        user_data = UserCreate(
            username=raw_data['username'],
            email=raw_data['email'],
            password=raw_data['password'],
            password_confirm=raw_data.get('password_confirm', raw_data['password']),
            phone=raw_data.get('phone'),
            first_name=raw_data.get('first_name'),
            last_name=raw_data.get('last_name'),
        )
        
        # Проверяем существующих пользователей
        existing_user = await auth_service.get_user_by_username(user_data.username)
        if existing_user:
            return {
                "error": "Пользователь с таким именем уже существует",
                "username": user_data.username
            }
        
        existing_email = await auth_service.get_user_by_email(user_data.email)
        if existing_email:
            return {
                "error": "Пользователь с таким email уже существует", 
                "email": user_data.email
            }

        user = await auth_service.create_user(user_data)

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )

        background_tasks.add_task(auth_service.send_welcome_email, user)
        
        # Получаем данные пользователя
        user_dict = await auth_service.get_user_dict(user.id)
        user_response = UserResponse(**user_dict)
        
        print("✅ Register compat successful")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": user_response
        }
        
    except Exception as e:
        print(f"Register compat error: {str(e)}")
        return {
            "error": f"Registration failed: {str(e)}",
            "received_data": raw_data
        }

@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Обновление JWT токена
    """
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(current_user.id)}, expires_delta=access_token_expires
    )
    
    # Создаем UserResponse напрямую из данных
    user_response = UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        phone=current_user.phone,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        avatar_url=current_user.avatar_url,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        email_verified=current_user.email_verified,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        last_login=current_user.last_login,
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user_response
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Получение информации о текущем пользователе
    """
    # Создаем UserResponse напрямую из данных
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        phone=current_user.phone,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        avatar_url=current_user.avatar_url,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        email_verified=current_user.email_verified,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        last_login=current_user.last_login,
    )

@router.get("/check-auth")
async def check_auth(current_user: User = Depends(get_current_user)):
    """Проверка аутентификации пользователя"""
    return {
        "authenticated": True,
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email
        }
    }