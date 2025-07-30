"""
Authentication service with user management and JWT token handling.
"""
import secrets,string, re
from datetime import datetime, timedelta
from typing import Optional,List
from uuid import UUID
from sqlalchemy.orm import selectinload  # or use joinedload if you prefer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException, status, BackgroundTasks
from services.email import EmailService
from models.user import User, UserRole,EmailChangeRequestModel,Address
from schemas.user import (
    UserCreate,
    UserLogin,
    UserUpdate,
    PasswordReset,
    PasswordResetConfirm,
    EmailVerification
)
from core.utils.file import ImageFile, GoogleDrive  # Assuming your classes are in utils.py

from core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token
)
from core.config import settings
from core.utils.redis import redis_client


class AuthService:
    """Authentication service for user management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_user(self, user_data: UserCreate,background_tasks: BackgroundTasks) -> User:
        """Register a new user with email verification."""
        # Check email
        if await self._get_user_by_email(user_data.email):
            raise HTTPException(status_code=400, detail="Email already registered.")

        # Check phone
        if user_data.phone:
            existing_phone = await self._get_user_by_phone(user_data.phone)
            if existing_phone:
                raise HTTPException(status_code=400, detail="Phone number already registered.")

        hashed_password = get_password_hash(user_data.password)

        # Step 1: Create user without picture link
        db_user = User(
            email=user_data.email,
            phone=user_data.phone,
            password_hash=hashed_password,
            firstname=user_data.firstname,
            lastname=user_data.lastname,
            role=user_data.role,
            verified=False,
            active=True,
            telegram=user_data.telegram,
            age=user_data.age,
            picture=None,  # temporarily None
            whatsapp=user_data.whatsapp,
            gender=user_data.gender,
        )
        # After creating db_user
        if user_data.addresses:
            for addr in user_data.addresses:
                address = Address(
                    user_id=db_user.id,
                    street=addr.street,
                    city=addr.city,
                    state=addr.state,
                    country=addr.country,
                    post_code=addr.post_code,
                    kind=addr.kind
                )
                self.db.add(address)
            await self.db.commit()
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)  # Now db_user.id exists!

        # Step 2: Upload image with user ID as filename
        if user_data.picture:
            google_drive = GoogleDrive(jsonkey=settings.google_service_account_info)
            picture = google_drive.upload_base64_image_as_webp(
                base64_str=user_data.picture,
                filename=f"{db_user.id}.webp",
                folder_id=None,
                quality=30
            )

            # Step 3: Update user picture link
            db_user.picture = picture['link']
            self.db.add(db_user)
            await self.db.commit()
            await self.db.refresh(db_user)

        # Step 4: Send verification OTP
        # email_service = EmailService(background_tasks)
        # await email_service._send_verification_otp(db_user.email, background_tasks)
        return db_user

    async def login_user(self, login_data: UserLogin) -> dict:
        """Authenticate user and return JWT tokens."""
        user = await self._get_user_by_email(login_data.email)
        if not user or not verify_password(login_data.password_hash, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        if not user.active:
            raise HTTPException(status_code=403, detail="User account is deactivated.")

        payload = {"sub": str(user.id), "email": user.email, "role": user.role.value}
        access_token = create_access_token(payload)
        refresh_token = create_refresh_token(payload)

        await redis_client.setex(
            f"refresh_token:{user.id}",
            timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            refresh_token
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": user.to_dict()
        }

    async def refresh_access_token(self, refresh_token: str) -> dict:
        """Generate new access token using refresh token."""
        try:
            payload = verify_token(refresh_token, "refresh")
            user_id = payload.get("sub")

            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token.")

            stored_token = await redis_client.get(f"refresh_token:{user_id}")
            if not stored_token or stored_token != refresh_token:
                raise HTTPException(status_code=401, detail="Refresh token expired or invalid.")

            user = await self._get_user_by_id(UUID(user_id))
            if not user or not user.active:
                raise HTTPException(status_code=403, detail="User not found or inactive.")

            token_data = {"sub": str(user.id), "email": user.email, "role": user.role.value}
            new_access_token = create_access_token(token_data)

            return {
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }

        except Exception:
            raise HTTPException(status_code=401, detail="Invalid refresh token.")

    async def logout_user(self, user_id: UUID) -> bool:
        """Logout user by invalidating refresh token."""
        await redis_client.delete(f"refresh_token:{user_id}")
        return True

    async def verify_email(self, verification_data: EmailVerification) -> bool:
        """Verify user email with OTP."""
        user = await self._get_user_by_email(verification_data.email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        stored_otp = await redis_client.get(f"email_otp:{user.email}")
        if not stored_otp or stored_otp != verification_data.otp:
            raise HTTPException(status_code=400, detail="Invalid or expired OTP.")

        user.verified = True
        user.updated_at = datetime.utcnow()
        await self.db.commit()
        await redis_client.delete(f"email_otp:{user.email}")
        return True

    async def request_password_reset(self, reset_data: PasswordReset,background_tasks: BackgroundTasks) -> bool:
        """Request password reset with OTP."""
        user = await self._get_user_by_email(reset_data.email)
        if user:
            email_service = EmailService(background_tasks)
            await email_service._send_password_reset_otp(user.email,background_tasks)
        return True  # Always return True for security

    async def confirm_password_reset(self, reset_data: PasswordResetConfirm) -> bool:
        """Confirm password reset and set new password."""
        user = await self._get_user_by_email(reset_data.email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        stored_otp = await redis_client.get(f"password_reset_otp:{user.email}")
        if not stored_otp or stored_otp != reset_data.otp:
            raise HTTPException(status_code=400, detail="Invalid or expired OTP.")

        user.password_hash = get_password_hash(reset_data.new_password)
        user.updated_at = datetime.utcnow()
        await self.db.commit()

        await redis_client.delete(f"password_reset_otp:{user.email}")
        await redis_client.delete(f"refresh_token:{user.id}")

        return True

    async def update_user_profile(self, user_id: UUID, update_data: UserUpdate) -> User:
        """Update user profile."""
        user = await self._get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        if update_data.phone and update_data.phone != user.phone:
            existing_user = await self._get_user_by_phone(update_data.phone)
            if existing_user and existing_user.id != user.id:
                raise HTTPException(status_code=400, detail="Phone number is already in use.")
        
        update_fields = update_data.model_dump(exclude_unset=True)
        # ✅ Handle address updates
        if "addresses" in update_fields:
            new_addresses = update_fields["addresses"]

            # Strategy: delete missing, update existing, add new
            existing_addr_ids = {str(a.id): a for a in user.addresses if a.id}
            new_ids = {str(a.id) for a in new_addresses if a.id}

            # Delete removed addresses
            for addr in user.addresses:
                if str(addr.id) not in new_ids:
                    await self.db.delete(addr)

            # Update or add addresses
            for addr in new_addresses:
                if addr.id and str(addr.id) in existing_addr_ids:
                    db_addr = existing_addr_ids[str(addr.id)]
                    for field, value in addr.model_dump(exclude_unset=True).items():
                        setattr(db_addr, field, value)
                else:
                    new_addr = Address(
                        user_id=user.id,
                        street=addr.street,
                        city=addr.city,
                        state=addr.state,
                        country=addr.country,
                        post_code=addr.post_code,
                        kind=addr.kind
                    )
                    self.db.add(new_addr)
        # Handle profile picture update
        if "picture" in update_fields and update_fields["picture"]:
            google_drive = GoogleDrive(jsonkey=settings.google_service_account_info)

            # ✅ Step 1: Delete previous image (if exists and is a Drive link)
            if user.picture and "drive.google.com" in user.picture:
                match = re.search(r'/d/([a-zA-Z0-9_-]+)', user.picture)
                if match:
                    old_file_id = match.group(1)
                    try:
                        google_drive.delete_file(old_file_id)
                    except Exception as e:
                        print(f"Failed to delete old image: {e}")

            # ✅ Step 2: Upload new image
            upload_result = google_drive.upload_base64_image_as_webp(
                base64_str=update_fields["picture"],
                filename=f"{user.id}.webp",
                folder_id=None,
                quality=30
            )
            update_fields["picture"] = upload_result['link']

        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)

        user.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_current_user(self, token: str) -> User:
        """Get current user from access token."""
        try:
            payload = verify_token(token)
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token.")

            user = await self._get_user_by_id(UUID(user_id))
            if not user or not user.active:
                raise HTTPException(status_code=403, detail="User not found or inactive.")

            return user

        except Exception:
            raise HTTPException(status_code=401, detail="Could not validate credentials.")
    
    async def get_all_users(self, limit: int = 10, offset: int = 0) -> List[User]:
        query = select(User).options(selectinload(User.addresses)).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def search_users(
        self,
        email: Optional[str] = None,
        role: Optional[UserRole] = None,
        active: Optional[bool] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[User]:
        query = select(User)

        if email:
            query = query.where(User.email.ilike(f"%{email}%"))
        if role:
            query = query.where(User.role == role)
        if active is not None:
            query = query.where(User.active == active)

        query = query.options(selectinload(User.addresses)).limit(limit).offset(offset)

        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def delete_user(self, user_id: UUID) -> None:
        user = await self._get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        # Soft delete example:
        user.active = False
        # user.deleted_at = datetime.utcnow()
        await self.db.commit()

    async def activate_user_by_token(self, token: str) -> bool:
        """
        Activate user account using verification token.
        Token could be a JWT or a unique token stored in Redis.
        """
        # Example with Redis token lookup:
        user_email = await redis_client.get(f"activation_token:{token}")
        if not user_email:
            raise HTTPException(status_code=400, detail="Invalid or expired activation token.")
        
        user = await self._get_user_by_email(user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")
        
        user.verified = True
        user.active = True
        user.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await redis_client.delete(f"activation_token:{token}")
        return True
    
    async def request_email_change(self, user_id: UUID, new_email: str,background_tasks: BackgroundTasks,):
        user = await self._get_user_by_id(user_id)
        if user.email == new_email:
            raise HTTPException(status_code=400, detail="New email is same as current email.")

        # Check if new_email is already used by another user
        existing_user = await self._get_user_by_email(new_email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email is already in use.")

        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=1)

        # Save to EmailChangeRequest table (you need to implement this DB model)
        email_change_request = EmailChangeRequestModel(
            user_id=user_id,
            new_email=new_email,
            token=token,
            expires_at=expires_at
        )
        self.db.add(email_change_request)
        await self.db.commit()

        # Send confirmation email to new_email with token link or token code
        email_service = EmailService(background_tasks)
        await email_service._send_email_change_confirmation(new_email, token)

    async def confirm_email_change(self, user_id: UUID, token: str):
        # Fetch request by user_id and token
        request = await self.db.execute(
            select(EmailChangeRequestModel).where(
                EmailChangeRequestModel.user_id == user_id,
                EmailChangeRequestModel.token == token,
                EmailChangeRequestModel.expires_at > datetime.utcnow()
            )
        )
        req = request.scalars().first()
        if not req:
            raise HTTPException(status_code=400, detail="Invalid or expired token.")

        user = await self._get_user_by_id(user_id)
        user.email = req.new_email
        await self.db.delete(req)
        await self.db.commit()
    
    # --- Private Methods ---

    async def _get_user_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).options(selectinload(User.addresses)).where(User.email == email))
        return result.scalar_one_or_none()

    async def _get_user_by_phone(self, phone: str) -> Optional[User]:
        result = await self.db.execute(select(User).options(selectinload(User.addresses)).where(User.phone == phone))
        return result.scalar_one_or_none()

    async def _get_user_by_id(self, user_id: UUID) -> Optional[User]:
        result = await self.db.execute(select(User).options(selectinload(User.addresses)).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    
    
    
    