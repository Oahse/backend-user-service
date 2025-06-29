from redis import asyncio as aioredis
from fastapi import FastAPI
from typing import List
from core.config import Settings
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware

from routes.user import router as user_router
from routes.address import router as address_router
from core.utils.response import Response, RequestValidationError 

app = FastAPI(
    title="User Service API",
    description="Handles user authentication, management, and address operations.",
    version="1.0.0"
)
settings = Settings()

# Add CORS middleware if configured
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

        
# Include the routers
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

# Handle validation errors globally
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        e = {}
        e['type'] = error['type']
        e['loc'] = error['loc']
        e['msg'] = error['msg']
        if 'ctx' in error.keys():
            e['ctx'] = error['ctx']['error']

        errors.append(e)
    errors = errors[0] if len(errors) == 1 else errors

    return Response(message=errors, success=False, code=422)


