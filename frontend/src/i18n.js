```javascript
import { configure } from 'react-intl';
import messages from './locale/en.json';
import hiMessages from './locale/hi.json';
import esMessages from './locale/es.json';

const languages = {
  en: messages,
  hi: hiMessages,
  es: esMessages,
};

export const getLocale = () => 'en'; // Default to English

export const setLocale = (locale) => {
  configure({ locale });
};

export const useIntl = () => ({
  formatMessage: (msg) => languages[getLocale()][msg.id],
});

export const messages = {
  en: messages,
  hi: hiMessages,
  es: esMessages,
};
```