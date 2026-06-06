from abc import ABC, abstractmethod


class PaymentGateway(ABC):
    @abstractmethod
    async def initialize_payment(self, email: str, amount: float, reference: str) -> dict:
        ...

    @abstractmethod
    async def verify_payment(self, reference: str) -> dict:
        ...

    @abstractmethod
    def verify_webhook_signature(self, body: bytes, signature: str) -> bool:
        ...
