```javascript
import { useTranslation } from 'next-i18next';

const Settings = () => {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col">
      <h1 className="text-2xl font-bold mb-4">{t('common.welcome')}</h1>
      <div className="flex-1 p-6">
        <h2 className="text-xl font-bold mb-4">{t('common.settings')}</h2>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-white">{t('common.settings')}</h2>
        </div>
        <div className="p-4 bg-gray-800 rounded-lg">
          <h2 className="text-xl font-bold mb-2">{t('common.welcome')}</h2>
          <p className="text-sm text-gray-400">{t('common.settings')}</p>
        </div>
      </div>
    </div>
  );
};

export default Settings;
```