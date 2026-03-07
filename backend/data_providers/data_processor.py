```python
from ticker_pulse.data_providers.cryptocurrencies import CryptocurrenciesDataProvider

def process_data(data_provider):
    data = data_provider.get_data()
    # Process data as needed
    return data
```