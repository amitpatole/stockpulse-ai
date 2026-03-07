```javascript
import React, { useState } from 'react';
import { FormattedMessage } from 'react-intl';

const Settings = () => {
  const [language, setLanguage] = useState('en');

  const handleLanguageChange = (e) => {
    setLanguage(e.target.value);
  };

  return (
    <div>
      <h2>Settings</h2>
      <select value={language} onChange={handleLanguageChange}>
        <option value="en">English</option>
        <option value="es">Spanish</option>
        <option value="hi">Hindi</option>
      </select>
    </div>
  );
};

export default Settings;
```