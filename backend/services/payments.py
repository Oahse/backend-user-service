from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.payments import Payment, PaymentStatus, PaymentMethod
from schemas.payments import PaymentCreate, PaymentUpdate, UUID
from services.stripe import StripeService

class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.stripe_service = StripeService()

    async def create_payment(self, payment_in: PaymentCreate) -> Payment:
        try:
            if payment_in.method == PaymentMethod.Stripe:
                # For Stripe payments, we might create a checkout session here
                # and store the session ID. The actual payment status update
                # will happen via webhooks.
                # This part assumes you've already created a Stripe Checkout Session
                # and are now recording the payment attempt in your DB.
                payment = Payment(
                    order_id=payment_in.order_id,
                    user_id=payment_in.user_id,
                    method=payment_in.method,
                    amount=payment_in.amount,
                    currency=payment_in.currency,
                    status=PaymentStatus.Pending,  # Initial status for Stripe payments
                    stripe_customer_id=payment_in.stripe_customer_id,
                    stripe_payment_intent_id=payment_in.stripe_payment_intent_id,
                    stripe_checkout_session_id=payment_in.stripe_checkout_session_id,
                )
            else:
                payment = Payment(
                    order_id=payment_in.order_id,
                    user_id=payment_in.user_id,
                    method=payment_in.method,
                    amount=payment_in.amount,
                    currency=payment_in.currency,
                    status=PaymentStatus.Pending,
                )

            self.db.add(payment)
            await self.db.commit()
            await self.db.refresh(payment)
            return payment
        except Exception as e:
            await self.db.rollback()
            raise e

    async def get_payment(self, payment_id: UUID) -> Optional[Payment]:
        result = await self.db.execute(select(Payment).where(Payment.id == payment_id))
        return result.scalar_one_or_none()

    async def update_payment(self, payment_id: UUID, payment_in: PaymentUpdate) -> Optional[Payment]:
        payment = await self.get_payment(payment_id)
        if not payment:
            return None

        try:
            update_data = payment_in.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(payment, key, value)
            
            await self.db.commit()
            await self.db.refresh(payment)
            return payment
        except Exception as e:
            await self.db.rollback()
            raise e

    async def delete_payment(self, payment_id: UUID) -> bool:
        payment = await self.get_payment(payment_id)
        if not payment:
            return False
        try:
            await self.db.delete(payment)
            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            raise e

    async def get_all_payments(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Payment]:
        result = await self.db.execute(select(Payment).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def update_payment_status_by_session_id(self, session_id: str, status: PaymentStatus):
        result = await self.db.execute(
            select(Payment).where(Payment.stripe_checkout_session_id == session_id)
        )
        payment = result.scalar_one_or_none()
        if payment:
            payment.status = status
            await self.db.commit()
            await self.db.refresh(payment)
        return payment

    async def update_payment_status_by_payment_intent_id(self, payment_intent_id: str, status: PaymentStatus):
        result = await self.db.execute(
            select(Payment).where(Payment.stripe_payment_intent_id == payment_intent_id)
        )
        payment = result.scalar_one_or_none()
        if payment:
            payment.status = status
            await self.db.commit()
            await self.db.refresh(payment)
        return payment
