import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getMarketOverview } from '../api/marketOverviewApi';
import { MarketOverviewData } from '../types';

const MarketOverview: React.FC = () => {
    const [marketData, setMarketData] = useState<MarketOverviewData | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            const data = await getMarketOverview();
            setMarketData(data);
        };

        fetchData();
    }, []);

    return (
        <div className="market-overview">
            {marketData && (
                <div className="market-overview__content">
                    <h1>Market Overview</h1>
                    <p>{marketData.summary}</p>
                    <div className="market-overview__stats">
                        <div className="market-overview__stat">
                            <span className="market-overview__stat-label">Total Companies</span>
                            <span className="market-overview__stat-value">{marketData.totalCompanies}</span>
                        </div>
                        <div className="market-overview__stat">
                            <span className="market-overview__stat-label">Active Trades</span>
                            <span className="market-overview__stat-value">{marketData.activeTrades}</span>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default MarketOverview;