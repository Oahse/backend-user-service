from fastapi import FastAPI, Request
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from api.v1.routes.user import router as user_router
from api.v1.routes.address import router as address_router
from api.v1.routes.notification import router as notification_router
from api.v1.routes.category import router as category_router
from api.v1.routes.inventory import router as inventory_router
from api.v1.routes.payments import router as payments_router
from api.v1.routes.products import router as products_router
from api.v1.routes.promocode import router as promocode_router
from api.v1.routes.tag import router as tag_router
from api.v1.routes.orders import router as orders_router


from contextlib import asynccontextmanager
from core.config import settings,logger
from core.utils.response import Response, RequestValidationError
from core.utils.messages import telegram
from core.utils.redis import redis_client

import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    asyncio.create_task(telegram.run_telegram_bot())
    logger.info("Bot is running...")

    await redis_client.connect()
    
    yield
    
    # Shutdown
    await telegram.telegram_app.stop()
    logger.error("Bot stopped.")
    await redis_client.disconnect()

app = FastAPI(
    title="User Service API",
    description="Handles user authentication, management, and address operations.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

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

# Include all routers
app.include_router(user_router)
app.include_router(address_router)
app.include_router(notification_router)
app.include_router(category_router)
app.include_router(inventory_router)
app.include_router(payments_router)
app.include_router(products_router)
app.include_router(promocode_router)
app.include_router(tag_router)
app.include_router(orders_router)


@app.get("/")
async def read_root():
    return {
        "service": "Banwee API",
        "status": "Running",
        "version": "1.0.0",
        "endpoints": {
            "users": "/users",
            "login": "/users/login",
            "addresses": "/addresses",
            "notifications": "/notifications",
            "categories": "/categories",
            "inventory": "/inventory",
            "payments": "/payments",
            "products": "/products",
            "promocodes": "/promocodes",
            "tags": "/tags",
            "orders": "/orders"
        },
        "docs": {
            "Swagger": "/docs",
            "ReDoc": "/redoc"
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
            "service": "Banwee API",
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

    return Response(message="Validation error", data=message, success=False, code=422)
