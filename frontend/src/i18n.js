```javascript
import { Provider, FormattedMessage } from 'react-intl';
import { useState } from 'react';
import { useTranslation } from 'next-i18next';
import { initReactI18next } from 'next-i18next';
import i18n from 'i18next';

// Define the language options
const languageOptions = [
  { value: 'en', label: 'English' },
  { value: 'hi', label: 'Hindi' },
  { value: 'es', label: 'Spanish' },
];

// Initialize i18next
i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: require('./locale/en.json') },
      hi: { translation: require('./locale/hi.json') },
      es: { translation: require('./locale/es.json') },
    },
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
  });

// Component to handle language selection
const Settings = () => {
  const { t, i18n } = useTranslation();

  const [locale, setLocale] = useState(i18n.language);

  const handleLanguageChange = (e) => {
    setLocale(e.target.value);
    i18n.changeLanguage(e.target.value);
  };

  return (
    <Provider i18n={i18n}>
      <div>
        <label>
          <FormattedMessage id="common.settings" />
        </label>
        <select value={locale} onChange={handleLanguageChange}>
          {languageOptions.map((lang) => (
            <option key={lang.value} value={lang.value}>
              {lang.label}
            </option>
          ))}
        </select>
        <p>
          <FormattedMessage id="common.welcome" />
        </p>
      </div>
    </Provider>
  );
};

export default Settings;
```