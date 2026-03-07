```javascript
import React, { useState } from 'react';
import { FormattedMessage } from 'react-intl';
import { useTranslation } from 'next-i18next';

const Settings = () => {
  const { t } = useTranslation();

  return (
    <div>
      <h2>{t('common.settings')}</h2>
      <p>{t('common.welcome')}</p>
    </div>
  );
};

export default Settings;
```