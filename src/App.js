```javascript
import React from 'react';
import { IntlProvider } from 'react-intl';
import { Provider } from 'react-redux';
import store from './store';
import AppRouter from './components/AppRouter';
import { getLocale } from './utils/translate';

function App() {
  const locale = getLocale(); // Fetch the locale from the settings or default to 'en'
  return (
    <Provider store={store}>
      <IntlProvider locale={locale} messages={messages[locale]}>
        <AppRouter />
      </IntlProvider>
    </Provider>
  );
}

export default App;
```