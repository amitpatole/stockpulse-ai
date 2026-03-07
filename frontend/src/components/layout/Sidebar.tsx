```javascript
import { useTranslation } from 'next-i18next';

const Sidebar = () => {
  const { t } = useTranslation();

  return (
    <aside className="w-64 p-4 bg-slate-900 text-slate-200">
      <h2 className="text-xl font-bold mb-4">{t('common.settings')}</h2>
      <nav>
        <ul>
          <li>
            <a href="/settings" className="text-sm text-slate-500 hover:text-slate-300">{t('common.welcome')}</a>
          </li>
        </ul>
      </nav>
    </aside>
  );
};

export default Sidebar;
```