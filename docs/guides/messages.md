# Messages

Every message the SDK produces is in `fazercards_sdk/messages.yaml`, and any of them can be replaced at runtime, for example to show input errors to customers in their language.

```python
from fazercards_sdk import messages

messages.use({
    "value.username": "Telegram istifadəçi adı 4-32 hərf, rəqəm və ya _ olmalıdır, verildi: {value!r}",
    "value.amount_scale": "{field} {value} iki onluq rəqəmdən çoxdur",
})
```

Or from a file with only the keys you change:

```yaml
value:
  range: "{field} {low} ilə {high} arasında tam ədəd olmalıdır, verildi: {value!r}"
error:
  signature: Webhook imzası uyğun gəlmir
```

```python
messages.use("messages.az.yaml")
```

Rules:

- Unknown keys raise `KeyError`.
- Keep the `{placeholders}`.
- The change applies to the whole process; `messages.reset()` restores the defaults.

```python
for key, text in sorted(messages.catalog().items()):
    print(key, "=", text)
```

| Group | Used for |
| --- | --- |
| `settings.*` | Descriptions of the settings |
| `value.*` | Arguments refused before sending |
| `error.*` | Errors from FazerCards, the network and webhook checks |

The default file: [src/fazercards_sdk/messages.yaml](https://github.com/qiyascc/fazercards-python-sdk/blob/main/src/fazercards_sdk/messages.yaml).
