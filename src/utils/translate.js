```javascript
import { getLocale } from './Settings';

const messages = {
  en: require('./locales/en.json'),
  es: require('./locales/es.json'),
  hi: require('./locales/hi.json'),
};

const getLocaleMessages = (locale) => messages[locale];

const getLocale = () => {
  const settings = window.localStorage.getItem('settings');
  if (settings) {
    return JSON.parse(settings).language;
  }
  return 'en';
};

export { getLocale, getLocaleMessages };
```