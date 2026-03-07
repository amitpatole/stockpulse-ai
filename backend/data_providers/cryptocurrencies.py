```python
from flask import current_app
from ticker_pulse.models.crypto import CryptoCurrency
from ticker_pulse.data_providers.base import DataProvider

class CryptocurrenciesDataProvider(DataProvider):
    def __init__(self):
        super().__init__()
        self._data = []

    def fetch_data(self):
        with current_app.app_context():
            self._data = list(CryptoCurrency.query.all())
        return self._data

    def get_data(self):
        return self._data
```