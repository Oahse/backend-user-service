from fastapi import APIRouter, Depends, status, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from core.database import get_db
from services.payments import PaymentService
from schemas.payments import PaymentCreate, PaymentUpdate, PaymentSchema
from services.stripe import StripeService
from core.config import settings

router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])

@router.post("/", response_model=PaymentSchema, status_code=status.HTTP_201_CREATED)
async def create_payment(payment_in: PaymentCreate, db: AsyncSession = Depends(get_db)):
    service = PaymentService(db)
    payment = await service.create_payment(payment_in)
    return payment

@router.get("/{payment_id}", response_model=PaymentSchema)
async def get_payment(payment_id: UUID, db: AsyncSession = Depends(get_db)):
    service = PaymentService(db)
    payment = await service.get_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment

@router.put("/{payment_id}", response_model=PaymentSchema)
async def update_payment(payment_id: UUID, payment_in: PaymentUpdate, db: AsyncSession = Depends(get_db)):
    service = PaymentService(db)
    payment = await service.update_payment(payment_id, payment_in)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment

@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment(payment_id: UUID, db: AsyncSession = Depends(get_db)):
    service = PaymentService(db)
    success = await service.delete_payment(payment_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return {"message": "Payment deleted successfully"}

@router.get("/", response_model=List[PaymentSchema])
async def get_all_payments(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    service = PaymentService(db)
    payments = await service.get_all_payments(skip=skip, limit=limit)
    return payments

# Stripe Endpoints
stripe_service = StripeService()

@router.post("/create-checkout-session")
async def create_checkout_session(order_id: UUID, amount: float, currency: str, db: AsyncSession = Depends(get_db)):
    try:
        # In a real application, you would fetch order details from your DB
        # and construct line_items based on the order.
        line_items = [
            {
                "price_data": {
                    "currency": currency,
                    "product_data": {
                        "name": f"Order {order_id}",
                    },
                    "unit_amount": int(amount * 100),  # Amount in cents
                },
                "quantity": 1,
            }
        ]
        success_url = f"{settings.DOMAIN}/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{settings.DOMAIN}/cancel"
        checkout_session = await stripe_service.create_checkout_session(line_items, success_url, cancel_url)
        
        # Optionally, save the checkout_session_id to your payment record
        # payment_in = PaymentCreate(order_id=order_id, amount=amount, currency=currency, method="Stripe", stripe_checkout_session_id=checkout_session.id)
        # payment = await PaymentService(db).create_payment(payment_in)

        return {"id": checkout_session.id, "url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    try:
        event = await stripe_service.construct_webhook_event(payload, sig_header)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        # Fulfill the purchase...
        # You would typically update your order/payment status here
        print(f"Checkout session completed: {session.id}")
        # Example: Update payment status in your DB
        # payment_service = PaymentService(db)
        # await payment_service.update_payment_status_by_session_id(session.id, PaymentStatus.Completed)

    elif event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        print(f"PaymentIntent was successful: {payment_intent.id}")
        # Example: Update payment status in your DB
        # payment_service = PaymentService(db)
        # await payment_service.update_payment_status_by_payment_intent_id(payment_intent.id, PaymentStatus.Completed)

    # ... handle other event types

    return {"status": "success"}

@router.get("/payment-status/{session_id}")
async def get_payment_status(session_id: str):
    try:
        checkout_session = await stripe_service.retrieve_checkout_session(session_id)
        payment_intent_id = checkout_session.payment_intent
        payment_intent = await stripe_service.retrieve_payment_intent(payment_intent_id)
        return {"status": payment_intent.status, "amount": payment_intent.amount / 100, "currency": payment_intent.currency}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
