import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.changenow.io/v2"
API_KEY = settings.CHANGENOW_API_KEY
COMMISSION = float(settings.COMMISSION_PERCENT) / 100

HEADERS = {
    "x-changenow-api-key": API_KEY,
    "Content-Type": "application/json"
}


async def get_currencies():
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{BASE_URL}/exchange/currencies?active=true&flow=standard",
            headers=HEADERS
        )
        return r.json()


async def get_estimated_amount(
    from_currency: str,
    to_currency: str,
    from_amount: float,
    from_network: str = None,
    to_network: str = None
):
    params = {
        "fromCurrency": from_currency.lower(),
        "toCurrency": to_currency.lower(),
        "fromAmount": str(from_amount),
        "flow": "standard"
    }
    if from_network:
        params["fromNetwork"] = from_network.lower()
    if to_network:
        params["toNetwork"] = to_network.lower()

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{BASE_URL}/exchange/estimated-amount",
            params=params,
            headers=HEADERS
        )
        logger.info(f"ChangeNOW estimated-amount response: {r.status_code} {r.text}")

        if r.status_code != 200:
            logger.error(f"ChangeNOW estimated-amount error: {r.text}")
            raise Exception(f"ChangeNOW error: {r.text}")

        data = r.json()
        raw_amount = float(data.get("toAmount", 0) or 0)
        commission_amount = raw_amount * COMMISSION
        final_amount = raw_amount - commission_amount

        return {
            "toAmount": final_amount,
            "rawAmount": raw_amount,
            "commissionAmount": commission_amount,
            "commissionPercent": float(settings.COMMISSION_PERCENT),
            "fromAmount": from_amount,
            "fromCurrency": from_currency.lower(),
            "toCurrency": to_currency.lower(),
            "fromNetwork": from_network,
            "toNetwork": to_network
        }


async def create_exchange(
    from_currency: str,
    to_currency: str,
    from_amount: float,
    address: str,
    from_network: str = None,
    to_network: str = None
):
    payload = {
        "fromCurrency": from_currency.lower(),
        "toCurrency": to_currency.lower(),
        "fromAmount": from_amount,
        "address": address,
        "flow": "standard",
        "type": "direct"
    }
    if from_network:
        payload["fromNetwork"] = from_network.lower()
    if to_network:
        payload["toNetwork"] = to_network.lower()

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{BASE_URL}/exchange",
            json=payload,
            headers=HEADERS
        )
        logger.info(f"ChangeNOW create exchange response: {r.status_code} {r.text}")

        if r.status_code != 200:
            logger.error(f"ChangeNOW create exchange error: {r.text}")
            raise Exception(f"ChangeNOW error: {r.text}")

        return r.json()


async def get_exchange_status(exchange_id: str):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{BASE_URL}/exchange/by-id",
            params={"id": exchange_id},
            headers=HEADERS
        )
        logger.info(f"ChangeNOW status response: {r.status_code} {r.text}")
        return r.json()


class ChangenowService:
    async def get_currencies(self):
        return await get_currencies()

    async def get_estimated_amount(
        self,
        from_currency,
        to_currency,
        from_amount,
        from_network=None,
        to_network=None
    ):
        return await get_estimated_amount(
            from_currency, to_currency, from_amount, from_network, to_network
        )

    async def get_exchange_amount(
        self,
        from_currency,
        to_currency,
        from_amount,
        from_network=None,
        to_network=None
    ):
        return await get_estimated_amount(
            from_currency, to_currency, from_amount, from_network, to_network
        )

    async def create_exchange(
        self,
        from_currency,
        to_currency,
        from_amount,
        address,
        from_network=None,
        to_network=None
    ):
        return await create_exchange(
            from_currency, to_currency, from_amount, address, from_network, to_network
        )

    async def get_exchange_status(self, exchange_id):
        return await get_exchange_status(exchange_id)


changenow_service = ChangenowService()
