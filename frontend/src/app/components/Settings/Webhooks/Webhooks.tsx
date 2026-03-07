```typescript
import React, { useState } from 'react';
import { useMutation } from '@apollo/client';
import { CREATE_WEBHOOK, DELETE_WEBHOOK, UPDATE_WEBHOOK } from './Webhooks.gql';
import { Webhook } from '../../types/Webhook';

const Webhooks: React.FC = () => {
  const [webhook, setWebhook] = useState<Webhook>({
    id: '',
    user_id: '',
    webhook_url: '',
    event_type: '',
    status: '',
    last_delivery_status: ''
  });

  const [createWebhook] = useMutation(CREATE_WEBHOOK);
  const [deleteWebhook] = useMutation(DELETE_WEBHOOK);
  const [updateWebhook] = useMutation(UPDATE_WEBHOOK);

  const handleCreateWebhook = async () => {
    const { data } = await createWebhook({ variables: { input: webhook } });
    setWebhook({ ...webhook, id: data.createWebhook.id });
  };

  const handleDeleteWebhook = async () => {
    const { data } = await deleteWebhook({ variables: { id: webhook.id } });
    setWebhook({ ...webhook, id: '' });
  };

  const handleUpdateWebhook = async () => {
    const { data } = await updateWebhook({ variables: { id: webhook.id, input: webhook } });
    setWebhook({ ...webhook, id: data.updateWebhook.id });
  };

  return (
    <div>
      <h2>Create Webhook</h2>
      <form onSubmit={(e) => { e.preventDefault(); handleCreateWebhook() }}>
        <input type="text" value={webhook.webhook_url} onChange={(e) => setWebhook({ ...webhook, webhook_url: e.target.value })} />
        <input type="text" value={webhook.event_type} onChange={(e) => setWebhook({ ...webhook, event_type: e.target.value })} />
        <button type="submit">Create</button>
      </form>
      <h2>Manage Webhooks</h2>
      <WebhooksList />
    </div>
  );
};

export default Webhooks;
```