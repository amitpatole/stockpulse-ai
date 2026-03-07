```python
from typing import List, Dict, Optional
import requests
from backend.models.crypto_models import CryptoTicker, CryptoPrice

class CryptoDataProvider:
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"

    def get_crypto_tickers(self) -> List[CryptoTicker]:
        url = f"{self.base_url}/tickers"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        tickers = [CryptoTicker(**ticker) for ticker in data]
        return tickers

    def get_crypto_prices(self, tickers: List[str]) -> Dict[str, float]:
        url = f"{self.base_url}/simple/price"
        params = {"ids": ",".join(tickers), "vs_currencies": "usd"}
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        prices = {ticker: data[ticker]["usd"] for ticker in tickers}
        return prices

    def get_historical_crypto_prices(self, ticker: str, date_range: str) -> Dict[str, float]:
        url = f"{self.base_url}/coins/{ticker}/history"
        params = {"date": date_range}
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        prices = {day: float(data["market_data"]["current_price"]["usd"]) for day in data["market_data"]["price_change_percentage_24h_in_currency"]}
        return prices
```