```python
import requests

async def handle_webhook_delivery(webhook: Webhook) -> WebhookDelivery:
    try:
        response = requests.post(webhook.webhook_url, json={"event_type": webhook.event_type})
        response.raise_for_status()
        webhook.status = "success"
        webhook.last_delivery_status = "success"
        return {"status": "success", "message": "Webhook delivered successfully"}
    except requests.exceptions.RequestException as e:
        webhook.status = "failed"
        webhook.last_delivery_status = "failed"
        return {"status": "failed", "message": str(e)}
```