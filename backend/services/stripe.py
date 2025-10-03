import stripe
from core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeService:
    def __init__(self):
        pass

    async def create_checkout_session(self, line_items: list, success_url: str, cancel_url: str):
        try:
            checkout_session = stripe.checkout.Session.create(
                line_items=line_items,
                mode="payment",
                success_url=success_url,
                cancel_url=cancel_url,
            )
            return checkout_session
        except stripe.error.StripeError as e:
            raise Exception(f"Error creating checkout session: {e}")

    async def construct_webhook_event(self, payload: bytes, sig_header: str):
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            return event
        except ValueError as e:
            # Invalid payload
            raise Exception(f"Invalid payload: {e}")
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            raise Exception(f"Invalid signature: {e}")

    async def retrieve_payment_intent(self, payment_intent_id: str):
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return payment_intent
        except stripe.error.StripeError as e:
            raise Exception(f"Error retrieving payment intent: {e}")
