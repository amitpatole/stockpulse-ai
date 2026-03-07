```python
from fastapi import APIRouter, HTTPException
from backend.api.data_providers.crypto_data_provider import CryptoDataProvider
from backend.models.crypto_models import CryptoTicker, CryptoPrice
from datetime import datetime

router = APIRouter()
crypto_data_provider = CryptoDataProvider()

@router.get("/api/v1/crypto/tickers", response_model=List[CryptoTicker])
def get_crypto_tickers():
    tickers = crypto_data_provider.get_crypto_tickers()
    return [ticker.dict() for ticker in tickers]

@router.get("/api/v1/crypto/prices", response_model=Dict[str, float])
def get_crypto_prices(tickers: List[str]):
    prices = crypto_data_provider.get_crypto_prices(tickers)
    return prices

@router.get("/api/v1/crypto/historical/prices", response_model=Dict[str, float])
def get_historical_crypto_prices(ticker: str, date_range: str):
    prices = crypto_data_provider.get_historical_crypto_prices(ticker, date_range)
    return prices
```