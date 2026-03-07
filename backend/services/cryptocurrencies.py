```python
from app.models import Cryptocurrency
from requests import get

def get_cryptocurrency_data(symbol):
    # Fetch data from a cryptocurrency data provider (e.g., CoinGecko API)
    response = get(f'{get_crypto_api_url()}/simple/price?ids={symbol}&vs_currencies=usd')
    data = response.json()[symbol]
    return data
```