```python
from typing import List, Dict
import pandas as pd
import numpy as np
from scipy.stats import norm
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy import and_

from tickerpulse.database import Database
from tickerpulse.app.models import StockData, TechnicalIndicators
from tickerpulse.app.schemas import TechnicalIndicatorsSchema
from tickerpulse.app.dependencies import get_db_session

router = APIRouter()

def calculate_rsi(data: pd.DataFrame, window: int = 14) -> pd.Series:
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(data: pd.DataFrame) -> pd.DataFrame:
    ema_12 = data['Close'].ewm(span=12, adjust=False).mean()
    ema_26 = data['Close'].ewm(span=26, adjust=False).mean()
    macd_line = ema_12 - ema_26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    return pd.DataFrame({'MACD': macd_line, 'Signal': signal_line})

def calculate_bollinger_bands(data: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    sma = data['Close'].rolling(window).mean()
    std_dev = data['Close'].rolling(window).std()
    upper_band = sma + (2 * std_dev)
    lower_band = sma - (2 * std_dev)
    return pd.DataFrame({'Upper': upper_band, 'Lower': lower_band})

def calculate_moving_averages(data: pd.DataFrame, short_window: int = 50, long_window: int = 200) -> pd.DataFrame:
    sma = data['Close'].rolling(window=short_window).mean()
    ema = data['Close'].ewm(span=long_window, adjust=False).mean()
    return pd.DataFrame({'SMA': sma, 'EMA': ema})

@router.get('/api/technical_indicators/{stock_symbol}', response_model=List[TechnicalIndicatorsSchema])
async def get_technical_indicators(stock_symbol: str, db_session: AsyncSession = Depends(get_db_session)):
    query = select(StockData).where(StockData.symbol == stock_symbol)
    result = await db_session.execute(query)
    stock_data = result.scalars().first()
    if not stock_data:
        raise HTTPException(status_code=404, detail=f"Stock data for {stock_symbol} not found")

    data = pd.DataFrame(stock_data.data)
    rsi = calculate_rsi(data)
    macd = calculate_macd(data)
    bollinger_bands = calculate_bollinger_bands(data)
    moving_averages = calculate_moving_averages(data)

    technical_indicators = pd.concat([data, rsi, macd, bollinger_bands, moving_averages], axis=1)
    technical_indicators = technical_indicators.reset_index().rename(columns={'index': 'Date'})

    return [TechnicalIndicatorsSchema(**row) for row in technical_indicators.to_dict('records')]

@router.post('/api/chart_data', response_model=List[TechnicalIndicatorsSchema])
async def get_chart_data(stock_symbols: List[str], db_session: AsyncSession = Depends(get_db_session)):
    query = select(StockData).where(StockData.symbol.in_(stock_symbols))
    result = await db_session.execute(query)
    stock_data = result.scalars().all()
    if not stock_data:
        raise HTTPException(status_code=404, detail="Stock data not found")

    data_list = []
    for stock in stock_data:
        data = pd.DataFrame(stock.data)
        rsi = calculate_rsi(data)
        macd = calculate_macd(data)
        bollinger_bands = calculate_bollinger_bands(data)
        moving_averages = calculate_moving_averages(data)

        technical_indicators = pd.concat([data, rsi, macd, bollinger_bands, moving_averages], axis=1)
        technical_indicators = technical_indicators.reset_index().rename(columns={'index': 'Date'})
        data_list.extend(technical_indicators.to_dict('records'))

    return [TechnicalIndicatorsSchema(**row) for row in data_list]
```