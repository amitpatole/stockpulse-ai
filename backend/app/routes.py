```python
from fastapi import APIRouter
from .api.technical_indicators import router as technical_indicators_router

router = APIRouter()

router.include_router(technical_indicators_router, prefix='/api', tags=['Technical Indicators'])
```