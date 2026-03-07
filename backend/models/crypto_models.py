```python
from typing import List
from pydantic import BaseModel

class CryptoTicker(BaseModel):
    id: str
    symbol: str
    name: str

class CryptoPrice(BaseModel):
    ticker: str
    price: float
```