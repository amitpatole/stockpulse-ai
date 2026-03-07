```javascript
import { useTranslation } from 'next-i18next';

const KPICards = () => {
  const { t } = useTranslation();

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div className="p-4 bg-gray-800 rounded-lg">
        <h2 className="text-xl font-bold mb-2">{t('common.settings')}</h2>
        <p className="text-sm text-gray-400">{t('common.welcome')}</p>
      </div>
      <div className="p-4 bg-gray-800 rounded-lg">
        <h2 className="text-xl font-bold mb-2">{t('common.settings')}</h2>
        <p className="text-sm text-gray-400">{t('common.welcome')}</p>
      </div>
      <div className="p-4 bg-gray-800 rounded-lg">
        <h2 className="text-xl font-bold mb-2">{t('common.settings')}</h2>
        <p className="text-sm text-gray-400">{t('common.welcome')}</p>
      </div>
    </div>
  );
};

export default KPICards;
```