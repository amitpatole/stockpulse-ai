```sql
-- Insider Trading Tracker Tables
-- Tracks SEC Form 4 filings for insider buying/selling activity

-- Map CIK to ticker for efficient lookups
CREATE TABLE IF NOT EXISTS insiders (
    cik TEXT PRIMARY KEY,
    ticker TEXT NOT NULL,
    company_name TEXT,
    insider_count INTEGER DEFAULT 0,
    last_filing_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(ticker) REFERENCES stocks(ticker) ON DELETE CASCADE
);

-- Individual Form 4 transactions with sentiment scores
CREATE TABLE IF NOT EXISTS insider_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cik TEXT NOT NULL,
    ticker TEXT NOT NULL,
    insider_name TEXT,
    title TEXT,
    transaction_type TEXT NOT NULL,
    shares INTEGER,
    price REAL,
    value REAL,
    filing_date TIMESTAMP,
    transaction_date TIMESTAMP,
    sentiment_score REAL DEFAULT 0.0,
    is_derivative BOOLEAN DEFAULT 0,
    filing_url TEXT,
    form4_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(cik, ticker, insider_name, transaction_date, transaction_type),
    FOREIGN KEY(cik) REFERENCES insiders(cik) ON DELETE CASCADE,
    FOREIGN KEY(ticker) REFERENCES stocks(ticker) ON DELETE CASCADE
);

-- Aggregate metrics for each CIK by date
CREATE TABLE IF NOT EXISTS insider_aggregate_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cik TEXT NOT NULL,
    ticker TEXT NOT NULL,
    aggregate_date DATE NOT NULL,
    net_shares_30d INTEGER DEFAULT 0,
    net_shares_90d INTEGER DEFAULT 0,
    buy_count INTEGER DEFAULT 0,
    sell_count INTEGER DEFAULT 0,
    total_buy_value REAL DEFAULT 0.0,
    total_sell_value REAL DEFAULT 0.0,
    sentiment_avg REAL DEFAULT 0.0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(cik, ticker, aggregate_date),
    FOREIGN KEY(cik) REFERENCES insiders(cik) ON DELETE CASCADE,
    FOREIGN KEY(ticker) REFERENCES stocks(ticker) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_insider_transactions_ticker ON insider_transactions(ticker, filing_date DESC);
CREATE INDEX IF NOT EXISTS idx_insider_transactions_cik ON insider_transactions(cik, filing_date DESC);
CREATE INDEX IF NOT EXISTS idx_insider_transactions_type ON insider_transactions(transaction_type, filing_date DESC);
CREATE INDEX IF NOT EXISTS idx_insider_transactions_sentiment ON insider_transactions(sentiment_score DESC);
CREATE INDEX IF NOT EXISTS idx_insider_aggregate_stats_ticker ON insider_aggregate_stats(ticker, aggregate_date DESC);
CREATE INDEX IF NOT EXISTS idx_insiders_ticker ON insiders(ticker);
```