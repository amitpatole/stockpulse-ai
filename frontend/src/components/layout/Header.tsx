```javascript
import { useTranslation } from 'next-i18next';
import { Link } from 'next/link';

interface HeaderProps {
  title: string;
  subtitle: string;
}

const Header = ({ title, subtitle }: HeaderProps) => {
  const { t } = useTranslation();

  return (
    <header className="bg-slate-950 text-slate-200 p-4">
      <div className="container mx-auto flex justify-between items-center">
        <Link href="/" passHref>
          <a className="text-2xl font-bold">{t('common.welcome')}</a>
        </Link>
        <nav className="flex space-x-4">
          <Link href="/settings" passHref>
            <a className="text-sm text-slate-500 hover:text-slate-300">{t('common.settings')}</a>
          </Link>
        </nav>
      </div>
    </header>
  );
};

export default Header;
```