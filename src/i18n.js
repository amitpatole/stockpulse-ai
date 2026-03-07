```javascript
import { IntlProvider } from 'react-intl';

const messages = {
  en: require('./locales/en.json'),
  es: require('./locales/es.json'),
  hi: require('./locales/hi.json'),
};

const i18n = {
  defaultLocale: 'en',
  locales: ['en', 'es', 'hi'],
  messages,
};

export default i18n;
```