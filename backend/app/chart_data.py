```python
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy import and_

from tickerpulse.database import Database
from tickerpulse.app.models import StockData
from tickerpulse.app.dependencies import get_db_session

router = APIRouter()

@router.get('/api/chart_data/{stock_symbol}', response_model=List[Dict[str, Any]])
async def get_chart_data(stock_symbol: str, db_session: AsyncSession = Depends(get_db_session)):
    query = select(StockData).where(StockData.symbol == stock_symbol)
    result = await db_session.execute(query)
    stock_data = result.scalars().first()
    if not stock_data:
        raise HTTPException(status_code=404, detail=f"Stock data for {stock_symbol} not found")

    data = stock_data.data
    return data

@router.post('/api/chart_data', response_model=List[Dict[str, Any]])
async def get_chart_data(stock_symbols: List[str], db_session: AsyncSession = Depends(get_db_session)):
    query = select(StockData).where(StockData.symbol.in_(stock_symbols))
    result = await db_session.execute(query)
    stock_data = result.scalars().all()
    if not stock_data:
        raise HTTPException(status_code=404, detail="Stock data not found")

    data_list = []
    for stock in stock_data:
        data = stock.data
        data_list.append(data)

    return data_list
```