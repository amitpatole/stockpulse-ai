```typescript
import React from 'react';
import { useQuery, useMutation } from '@apollo/client';
import { GET_WEBHOOKS, DELETE_WEBHOOK, UPDATE_WEBHOOK } from './Webhooks.gql';
import { useRecoilState } from 'recoil';
import { webhooksState } from '../../state/webhooksState';
import { Webhook } from '../../types/Webhook';

const WebhooksList: React.FC = () => {
  const [webhooks, setWebhooks] = useRecoilState(webhooksState);
  const { loading, error, data } = useQuery(GET_WEBHOOKS);
  const [deleteWebhook] = useMutation(DELETE_WEBHOOK);
  const [updateWebhook] = useMutation(UPDATE_WEBHOOK);

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error: {error.message}</p>;

  return (
    <div>
      <h2>Webhooks</h2>
      <ul>
        {data.webhooks.map((webhook: Webhook) => (
          <li key={webhook.id}>
            <strong>{webhook.webhook_url}</strong>
            <button onClick={() => updateWebhook({ variables: { id: webhook.id, input: webhook } })}>Update</button>
            <button onClick={() => deleteWebhook({ variables: { id: webhook.id } })}>Delete</button>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default WebhooksList;
```