from redis import asyncio as aioredis
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from core.config import Settings
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from routes.user import router as user_router
from routes.address import router as address_router
from core.utils.response import Response, RequestValidationError
from routes.email import router as email_router
from routes.notification import router as notification_router
from core.utils.messages import telegram
from core.utils.redis import redis_client
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    asyncio.create_task(telegram.run_telegram_bot())
    print("Bot is running...")
    
    await redis_client.connect()
    
    yield
    
    # Shutdown
    await telegram.telegram_app.stop()
    print("Bot stopped.")
    await redis_client.disconnect()

app = FastAPI(
    title="User Service API",
    description="Handles user authentication, management, and address operations.",
    version="1.0.0",
    lifespan=lifespan
)
settings = Settings()

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.banwee.com"]
)

app.include_router(email_router)
app.include_router(notification_router)
app.include_router(user_router)
app.include_router(address_router)


@app.get("/")
async def read_root():
    return {
        "service": "User Service API",
        "status": "Running",
        "version": "1.0.0",
        "endpoints": {
            "users": "/users",
            "addresses": "/addresses",
            "login": "/users/login",
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker health checks and monitoring."""
    try:
        # Test Redis connection
        await redis_client.ping()
        return {
            "status": "healthy",
            "service": "User Service API",
            "version": "1.0.0",
            "redis": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "User Service API",
            "version": "1.0.0",
            "redis": "disconnected",
            "error": str(e)
        }

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        e = {
            "type": error.get("type"),
            "loc": error.get("loc"),
            "msg": error.get("msg"),
        }
        if "ctx" in error:
            e["ctx"] = error["ctx"]
        errors.append(e)

    message = errors[0] if len(errors) == 1 else errors

    return Response(message=message, success=False, code=422)
