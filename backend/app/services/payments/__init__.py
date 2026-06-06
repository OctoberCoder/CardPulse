from .paystack import PaystackClient
from .flutterwave import FlutterwaveClient
from .mock import MockPaymentClient
from .base import PaymentGateway


def get_payment_client(name: str = "paystack") -> PaymentGateway:
    from app.config import get_settings
    settings = get_settings()
    if name == "paystack":
        if not settings.paystack_secret_key:
            return MockPaymentClient()
        return PaystackClient()
    elif name == "flutterwave":
        if not settings.flutterwave_secret_key:
            return MockPaymentClient()
        return FlutterwaveClient()
    return MockPaymentClient()
