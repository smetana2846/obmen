from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    firebase_token: str

class UserResponse(BaseModel):
    id: int
    firebase_token: Optional[str]

    class Config:
        from_attributes = True

class CurrencyResponse(BaseModel):
    ticker: str
    name: str
    network: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    rate: Optional[float] = None

class ExchangeCalculateRequest(BaseModel):
    from_currency: str
    to_currency: str
    amount: float
    from_network: Optional[str] = None
    to_network: Optional[str] = None

class ExchangeCalculateResponse(BaseModel):
    amount_send: float
    amount_receive: float
    raw_amount_receive: float
    rate: float
    commission_percent: float
    commission_amount: float

class ExchangeCreateRequest(BaseModel):
    firebase_token: str
    from_currency: str
    to_currency: str
    amount: float
    address: str
    from_network: Optional[str] = None
    to_network: Optional[str] = None

class ExchangeCreateResponse(BaseModel):
    id: int
    exchange_id: str
    deposit_address: str
    amount_send: float
    amount_receive: float
    commission_percent: float
    commission_amount: float
    status: str

class ExchangeStatusResponse(BaseModel):
    id: int
    exchange_id: str
    status: str
    amount_send: float
    amount_receive: float
    commission_percent: float
    commission_amount: float
    from_currency: str
    to_currency: str
    created_at: Optional[str] = None

class FavoriteAddRequest(BaseModel):
    firebase_token: str
    ticker: str
    network: Optional[str] = None

class FavoriteResponse(BaseModel):
    id: int
    ticker: str
    network: Optional[str]

    class Config:
        from_attributes = True