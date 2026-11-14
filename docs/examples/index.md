# Examples

Complete pieces of a small shop, to copy and adapt.

| Example | What it shows |
| --- | --- |
| [FastAPI webhook](fastapi-webhook.md) | A webhook endpoint that delivers each order exactly once, with SQLite |
| [Django checkout](django-checkout.md) | Models, a fulfilment function with idempotency keys and a webhook view |
| [Price list](price-list.md) | Every offer of every category with your margin, to CSV |
| [Balance alert](balance-alert.md) | A cron job that writes to Telegram when the balance runs low |
| [Reconcile unknown orders](reconcile.md) | A job that settles orders whose outcome was unknown |
