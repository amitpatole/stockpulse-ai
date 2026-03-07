```javascript
import React, { useState } from 'react';
import { FormattedMessage, useIntl } from 'react-intl';
import { useSettings } from '../../hooks/useSettings';

const Settings = () => {
  const [selectedLanguage, setSelectedLanguage] = useState('en');
  const { updateSettings } = useSettings();

  const handleLanguageChange = (language) => {
    setSelectedLanguage(language);
    updateSettings({ language });
  };

  return (
    <div>
      <h2>Settings</h2>
      <label>
        <FormattedMessage id="settings.language" defaultMessage="Language" />
        <select value={selectedLanguage} onChange={(e) => handleLanguageChange(e.target.value)}>
          <option value="en">English</option>
          <option value="hi">Hindi</option>
          <option value="es">Spanish</option>
        </select>
      </label>
    </div>
  );
};

export default Settings;
```