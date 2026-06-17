import httpx
from app.core.config import settings
from typing import Optional

class ChangeNOWService:
    def __init__(self):
        self.api_key = settings.CHANGENOW_API_KEY
        self.base_url = settings.CHANGENOW_BASE_URL
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    async def get_currencies(self) -> list[dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/exchange/currencies",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def get_exchange_amount(
        self,
        from_currency: str,
        to_currency: str,
        amount: float,
        from_network: Optional[str] = None,
        to_network: Optional[str] = None
    ) -> dict:
        params = {
            "fromCurrency": from_currency.upper(),
            "toCurrency": to_currency.upper(),
            "amount": amount,
        }
        if from_network:
            params["fromNetwork"] = from_network
        if to_network:
            params["toNetwork"] = to_network

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/exchange/amount",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json()

    async def create_exchange(
        self,
        from_currency: str,
        to_currency: str,
        address: str,
        amount: float,
        refund_address: Optional[str] = None,
        from_network: Optional[str] = None,
        to_network: Optional[str] = None
    ) -> dict:
        payload = {
            "fromCurrency": from_currency.upper(),
            "toCurrency": to_currency.upper(),
            "toAddress": address,
            "amount": str(amount),
        }
        if from_network:
            payload["fromNetwork"] = from_network
        if to_network:
            payload["toNetwork"] = to_network
        if refund_address:
            payload["refundAddress"] = refund_address

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/exchange",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()

    async def get_exchange_status(self, exchange_id: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/transactions/{exchange_id}/status",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

changenow_service = ChangeNOWService()