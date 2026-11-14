# Balance alert

Orders fail when the balance runs out. This job checks the balance and writes to a Telegram chat when it drops below a threshold. Run it every 15 minutes from cron.

```python
import os
import sys
from decimal import Decimal

import httpx

from fazercards_sdk import FazerCards, FazerCardsError

THRESHOLD = Decimal(os.environ.get("FAZERCARDS_MIN_BALANCE", "50"))
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT = os.environ["TELEGRAM_CHAT_ID"]


def notify(text: str) -> None:
    httpx.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
               json={"chat_id": CHAT, "text": text}, timeout=15).raise_for_status()


def main() -> int:
    try:
        with FazerCards() as fc:
            balance = fc.balance()
    except FazerCardsError as exc:
        notify(f"FazerCards balance check failed: {exc}")
        return 1
    if balance.amount < THRESHOLD:
        notify(f"FazerCards balance is {balance.amount} {balance.currency}, below {THRESHOLD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

```text
*/15 * * * * cd /srv/shop && .venv/bin/python balance_alert.py
```

Windows Task Scheduler, from CMD:

```bat
schtasks /Create /SC MINUTE /MO 15 /TN "fazercards balance" /TR "C:\shop\.venv\Scripts\python.exe C:\shop\balance_alert.py"
```

The comparison is between two `Decimal` values, so `49.999` is below `50` and `50.00` is not.
