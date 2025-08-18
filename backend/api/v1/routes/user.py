from fastapi import APIRouter, Depends, HTTPException,Query,BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.utils.response import Response
from models.user import UserRole
from services.user import AuthService, UUID,Optional

from schemas.user import (
    UserCreate, UserLogin, UserRead, UserUpdate,
    PasswordReset, PasswordResetConfirm, EmailVerification,
    RefreshTokenRequest,EmailChangeConfirm,EmailChangeRequest
)

router = APIRouter(prefix='/api/v1/users', tags=["Users"])
security = HTTPBearer()

def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    return await auth_service.get_current_user(credentials.credentials)

# Dependency to check admin role
async def get_current_admin_user(
    current_user=Depends(get_current_user)
):
    if current_user.role != UserRole.Admin:
        raise HTTPException(status_code=403, detail="Admin privileges required.")
    return current_user

@router.post("/register")
async def register(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    auth_service: AuthService = Depends(get_auth_service)
):
    user = await auth_service.register_user(user_data, background_tasks)
    return Response(data=user.to_dict(), message="User registered successfully", code=201)


@router.post("/login")
async def login(
    login_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    token_data = await auth_service.login_user(login_data)
    return Response(data=token_data, message="User logged in successfully", code=200)


@router.post("/refresh")
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    token_data = await auth_service.refresh_access_token(refresh_data.refresh_token)
    return Response(data=token_data, message="Access token refreshed", code=200)


@router.post("/logout")
async def logout(
    current_user=Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    await auth_service.logout_user(current_user.id)
    return Response(data=True, message="Successfully logged out", code=200)


@router.post("/verify-email")
async def verify_email(
    verification_data: EmailVerification,
    auth_service: AuthService = Depends(get_auth_service)
):
    await auth_service.verify_email(verification_data)
    return Response(data=True, message="Email verified successfully", code=200)


@router.post("/request-password-reset")
async def request_password_reset(
    reset_data: PasswordReset,
    background_tasks: BackgroundTasks,
    auth_service: AuthService = Depends(get_auth_service)
):
    await auth_service.request_password_reset(reset_data,background_tasks)
    return Response(data=True, message="Password reset OTP sent to email", code=200)


@router.post("/confirm-password-reset")
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    auth_service: AuthService = Depends(get_auth_service)
):
    await auth_service.confirm_password_reset(reset_data)
    return Response(data=True, message="Password reset successfully", code=200)


@router.get("/me")
async def get_current_user_info(
    current_user=Depends(get_current_user)
):
    return Response(data=current_user.to_dict(), message="Current user info fetched", code=200)

@router.get("/activate")
async def activate_account(
    token: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    await auth_service.activate_user_by_token(token)
    return Response(data=True, message="Account activated successfully", code=200)

# admin-only route to get all users
@router.get("/admin/users")
async def get_all_users(
    limit: Optional[int] = Query(10, ge=1, le=100),   # max 100 per page
    offset: Optional[int] = Query(0, ge=0),
    admin_user=Depends(get_current_admin_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    users = await auth_service.get_all_users(limit=limit, offset=offset)
    return Response(data=[u.to_dict() for u in users], message="All users fetched (admin)", code=200)


@router.get("/admin/users/{user_id}")
async def get_user_by_id(
    user_id: str,
    admin_user=Depends(get_current_admin_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    print(user_id,'=====================================')
    user = await auth_service._get_user_by_id(UUID(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return Response(data=user.to_dict(), message="User fetched (admin)", code=200)

@router.put("/me")
async def update_profile(
    update_data: UserUpdate,
    current_user=Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    updated_user = await auth_service.update_user_profile(current_user.id, update_data)
    return Response(data=updated_user.to_dict(), message="Profile updated successfully", code=200)

@router.post("/me/deactivate")
async def deactivate_own_account(
    current_user=Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    user = await auth_service._get_user_by_id(current_user.id)
    user.active = False
    await auth_service.db.commit()
    return Response(data=True, message="Account deactivated", code=200)

@router.post("/admin/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    admin_user=Depends(get_current_admin_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    user = await auth_service._get_user_by_id(UUID(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.active = False
    await auth_service.db.commit()
    return Response(data=True, message="User deactivated", code=200)


@router.post("/admin/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    admin_user=Depends(get_current_admin_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    user = await auth_service._get_user_by_id(UUID(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.active = True
    await auth_service.db.commit()
    return Response(data=True, message="User activated", code=200)

@router.post("/resend-verification-otp")
async def resend_verification_otp(
    email_verification: EmailVerification,
    auth_service: AuthService = Depends(get_auth_service)
):
    user = await auth_service._get_user_by_email(email_verification.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    await auth_service._send_verification_otp(user.email)
    return Response(data=True, message="Verification OTP resent", code=200)

@router.get("/roles")
async def get_roles():
    roles = [role.value for role in UserRole]
    return Response(data=roles, message="User roles fetched", code=200)

@router.get("/admin/search/users")
async def search_users(
    email: Optional[str] = Query(None),
    role: Optional[UserRole] = Query(None),
    active: Optional[bool] = Query(None),
    limit: Optional[int] = Query(10, ge=1, le=100),
    offset: Optional[int] = Query(0, ge=0),
    admin_user=Depends(get_current_admin_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    users = await auth_service.search_users(
        email=email,
        role=role,
        active=active,
        limit=limit,
        offset=offset,
    )
    return Response(data=[u.to_dict() for u in users], message="Filtered users fetched", code=200)


@router.get("/admin/user/by-email")
async def get_user_by_email(
    email: str = Query(...),
    admin_user=Depends(get_current_admin_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    user = await auth_service._get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return Response(data=user.to_dict(), message="User fetched by email (admin)", code=200)

@router.delete("/me")
async def delete_own_account(
    current_user=Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    await auth_service.delete_user(current_user.id)
    return Response(data=True, message="Account deleted successfully", code=200)

@router.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: str,
    admin_user=Depends(get_current_admin_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    await auth_service.delete_user(UUID(user_id))
    return Response(data=True, message="User deleted successfully", code=200)

@router.post("/me/request-email-change")
async def request_email_change(
    data: EmailChangeRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    await auth_service.request_email_change(current_user.id, data.new_email, background_tasks)
    return Response(data=True, message="Email change requested. Confirmation sent to new email.", code=200)

@router.post("/me/confirm-email-change")
async def confirm_email_change(
    data: EmailChangeConfirm,
    current_user=Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    await auth_service.confirm_email_change(current_user.id, data.token)
    return Response(data=True, message="Email address updated successfully.", code=200)