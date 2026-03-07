```javascript
import { useTranslation } from 'next-i18next';

const NewsFeed = () => {
  const { t } = useTranslation();

  return (
    <div className="p-4 bg-gray-800 rounded-lg">
      <h2 className="text-xl font-bold mb-2">{t('common.settings')}</h2>
      <p className="text-sm text-gray-400">{t('common.welcome')}</p>
    </div>
  );
};

export default NewsFeed;
```