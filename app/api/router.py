from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.models import User, Favorite, Exchange
from app.schemas.schemas import *
from app.services.changenow import changenow_service
from app import database
from datetime import datetime
import logging

logger = logging.getLogger("cris")
router = APIRouter()


# ── Простая защита API-ключом (пока хватит) ──
async def verify_api_key(x_api_key: str = Header(default="")):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    if x_api_key != settings.AUTH_API_KEY:
        logger.warning(f"Invalid API key: {x_api_key[:12]}...")
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key


# ── Пользователи ──

@router.post("/users", response_model=UserResponse)
async def create_user(request: UserCreate, db: Session = Depends(database.get_db), _=Depends(verify_api_key)):
    if not request.firebase_token:
        raise HTTPException(status_code=400, detail="firebase_token is required")
    user = db.query(User).filter(User.firebase_token == request.firebase_token).first()
    if user:
        return user
    user = User(firebase_token=request.firebase_token)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ── Валюты (публичный) ──

@router.get("/currencies", response_model=list[CurrencyResponse])
async def get_currencies():
    try:
        currencies = await changenow_service.get_currencies()
        return [
            CurrencyResponse(
                ticker=c.get("ticker", ""),
                name=c.get("name", c.get("ticker", "")),
                network=c.get("network"),
                min_amount=c.get("minAmount"),
                max_amount=c.get("maxAmount"),
            )
            for c in currencies
        ]
    except Exception as e:
        logger.error(f"Failed to fetch currencies: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch currencies from ChangeNOW")


# ── Расчёт ──

@router.post("/exchange/calculate", response_model=ExchangeCalculateResponse)
async def calculate_exchange(request: ExchangeCalculateRequest):
    if not request.from_currency or not request.to_currency:
        raise HTTPException(status_code=400, detail="from_currency and to_currency are required")
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="amount must be positive")

    try:
        result = await changenow_service.get_exchange_amount(
            request.from_currency, request.to_currency, request.amount,
            request.from_network, request.to_network
        )
    except Exception as e:
        logger.error(f"ChangeNOW amount error: {e}")
        raise HTTPException(status_code=502, detail=f"ChangeNOW error: {str(e)}")

    rate = float(result.get("rate", 0))
    raw_amount = float(result.get("estimatedAmount", result.get("amount", 0)))
    commission = round(raw_amount * (settings.COMMISSION_PERCENT / 100), 8)
    final = round(raw_amount - commission, 8)

    return ExchangeCalculateResponse(
        amount_send=request.amount,
        amount_receive=final,
        raw_amount_receive=raw_amount,
        rate=rate,
        commission_percent=settings.COMMISSION_PERCENT,
        commission_amount=commission
    )


# ── Создание обмена ──

@router.post("/exchange/create", response_model=ExchangeCreateResponse)
async def create_exchange(request: ExchangeCreateRequest, db: Session = Depends(database.get_db), _=Depends(verify_api_key)):
    if not request.address:
        raise HTTPException(status_code=400, detail="address is required")

    user = db.query(User).filter(User.firebase_token == request.firebase_token).first()
    if not user:
        user = User(firebase_token=request.firebase_token)
        db.add(user)
        db.commit()
        db.refresh(user)

    # Расчёт с комиссией
    calc = await changenow_service.get_exchange_amount(
        request.from_currency, request.to_currency, request.amount,
        request.from_network, request.to_network
    )
    raw_amount = float(calc.get("estimatedAmount", calc.get("amount", 0)))
    commission = round(raw_amount * (settings.COMMISSION_PERCENT / 100), 8)
    final = round(raw_amount - commission, 8)

    try:
        cn_result = await changenow_service.create_exchange(
            from_currency=request.from_currency,
            to_currency=request.to_currency,
            address=request.address,
            amount=request.amount,
            from_network=request.from_network,
            to_network=request.to_network
        )
    except Exception as e:
        logger.error(f"ChangeNOW create error: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to create exchange: {str(e)}")

    exchange_id = cn_result.get("id", cn_result.get("exchangeId", ""))
    deposit_address = cn_result.get("depositAddress", cn_result.get("payinAddress", ""))

    exchange = Exchange(
        user_id=user.id,
        from_currency=request.from_currency,
        to_currency=request.to_currency,
        from_network=request.from_network,
        to_network=request.to_network,
        amount_send=request.amount,
        amount_receive_before_commission=raw_amount,
        amount_receive=final,
        commission_percent=settings.COMMISSION_PERCENT,
        commission_amount=commission,
        deposit_address=deposit_address,
        exchange_id=exchange_id,
        status="waiting"
    )
    db.add(exchange)
    db.commit()
    db.refresh(exchange)

    logger.info(
        f"Exchange created | id={exchange.id} cn_id={exchange_id} user={user.id} "
        f"{exchange.amount_send} {exchange.from_currency} -> "
        f"{exchange.amount_receive} {exchange.to_currency} "
        f"commission={commission} ({settings.COMMISSION_PERCENT}%)"
    )

    return ExchangeCreateResponse(
        id=exchange.id,
        exchange_id=exchange_id,
        deposit_address=deposit_address,
        amount_send=exchange.amount_send,
        amount_receive=exchange.amount_receive,
        commission_percent=exchange.commission_percent,
        commission_amount=exchange.commission_amount,
        status=exchange.status
    )


# ── Статус ──

@router.get("/exchange/status/{exchange_id}", response_model=ExchangeStatusResponse)
async def get_exchange_status(exchange_id: str, db: Session = Depends(database.get_db)):
    exchange = db.query(Exchange).filter(Exchange.exchange_id == exchange_id).first()
    if not exchange:
        raise HTTPException(status_code=404, detail="Exchange not found")

    try:
        status_data = await changenow_service.get_exchange_status(exchange_id)
        new_status = status_data.get("status")
        if new_status and new_status != exchange.status:
            exchange.status = new_status
            exchange.updated_at = datetime.utcnow()
            db.commit()
    except Exception as e:
        logger.warning(f"Status check failed for {exchange_id}: {e}")

    return _exchange_to_status_response(exchange)


# ── История ──

@router.get("/exchanges/history/{firebase_token}", response_model=list[ExchangeStatusResponse])
async def get_exchange_history(firebase_token: str, db: Session = Depends(database.get_db), _=Depends(verify_api_key)):
    if not firebase_token:
        raise HTTPException(status_code=400, detail="firebase_token is required")

    user = db.query(User).filter(User.firebase_token == firebase_token).first()
    if not user:
        return []

    exchanges = db.query(Exchange).filter(
        Exchange.user_id == user.id
    ).order_by(Exchange.created_at.desc()).limit(100).all()

    return [_exchange_to_status_response(e) for e in exchanges]


# ── Избранное ──

@router.post("/favorites", response_model=FavoriteResponse)
async def add_favorite(request: FavoriteAddRequest, db: Session = Depends(database.get_db), _=Depends(verify_api_key)):
    if not request.firebase_token or not request.ticker:
        raise HTTPException(status_code=400, detail="firebase_token and ticker are required")

    user = db.query(User).filter(User.firebase_token == request.firebase_token).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing = db.query(Favorite).filter(
        Favorite.user_id == user.id,
        Favorite.ticker == request.ticker,
        Favorite.network == request.network
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Already in favorites")

    favorite = Favorite(user_id=user.id, ticker=request.ticker, network=request.network)
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return favorite


@router.get("/favorites/{firebase_token}", response_model=list[FavoriteResponse])
async def get_favorites(firebase_token: str, db: Session = Depends(database.get_db), _=Depends(verify_api_key)):
    if not firebase_token:
        raise HTTPException(status_code=400, detail="firebase_token is required")
    user = db.query(User).filter(User.firebase_token == firebase_token).first()
    if not user:
        return []
    return user.favorites


# ── Helpers ──

def _exchange_to_status_response(e: Exchange) -> ExchangeStatusResponse:
    return ExchangeStatusResponse(
        id=e.id,
        exchange_id=e.exchange_id,
        status=e.status,
        amount_send=e.amount_send,
        amount_receive=e.amount_receive,
        commission_percent=e.commission_percent,
        commission_amount=e.commission_amount,
        from_currency=e.from_currency,
        to_currency=e.to_currency,
        created_at=e.created_at.isoformat() if e.created_at else None
    )