import pytest


@pytest.mark.asyncio
async def test_mock_initialize_payment():
    from app.services.payments import MockPaymentClient
    client = MockPaymentClient()
    result = await client.initialize_payment("test@example.com", 100.0, "ref-001")
    assert result["status"] is True
    assert "authorization_url" in result["data"]


@pytest.mark.asyncio
async def test_mock_verify_payment():
    from app.services.payments import MockPaymentClient
    client = MockPaymentClient()
    result = await client.verify_payment("ref-001")
    assert result["data"]["status"] == "success"


def test_mock_webhook_signature():
    from app.services.payments import MockPaymentClient
    import hashlib
    client = MockPaymentClient()
    body = b'{"event":"charge.success"}'
    sig = hashlib.sha256(body).hexdigest()
    assert client.verify_webhook_signature(body, sig) is True


@pytest.mark.asyncio
async def test_get_payment_client_returns_mock():
    from app.services.payments import get_payment_client, MockPaymentClient
    client = get_payment_client("paystack")
    assert isinstance(client, MockPaymentClient)
