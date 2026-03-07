```javascript
import React from 'react';
import { useTranslation } from 'next-i18next';

const Dashboard = () => {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col">
      <h1 className="text-2xl font-bold mb-4">{t('common.welcome')}</h1>
      <div className="flex-1 p-6">
        {/* KPI Cards Row */}
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-white">{t('common.settings')}</h2>
        </div>
        {/* Main Content: Stock Grid + News Feed */}
        <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-3">
          {/* Stock Grid - Takes up 2 columns on xl */}
          <div className="xl:col-span-2">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-white">{t('common.settings')}</h2>
            </div>
            <div className="p-4 bg-gray-800 rounded-lg">
              <h2 className="text-xl font-bold mb-2">{t('common.welcome')}</h2>
              <p className="text-sm text-gray-400">{t('common.settings')}</p>
            </div>
          </div>

          {/* News Feed - Right sidebar */}
          <div className="xl:col-span-1">
            <div className="p-4 bg-gray-800 rounded-lg">
              <h2 className="text-xl font-bold mb-2">{t('common.welcome')}</h2>
              <p className="text-sm text-gray-400">{t('common.settings')}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
```