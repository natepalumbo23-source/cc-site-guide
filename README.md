# Credit Cowboy Guide (prototype)

Mobile-first funnel → mock paywall → 4-tile home for
**The Credit Cowboy Guide to Buy Side Interviews**.

## Run

```bash
cd /workspace/cc-guide-site
.venv/bin/python app.py
```

Open http://127.0.0.1:5055 on a phone-width viewport (~390px).

## Flow

1. Funnel (one question per screen, progress bar at bottom)
2. Paywall / create account (payment mocked — no Stripe charge)
3. Home with Q&As, Paper LBO, Model Tests, Resume Builder
4. Each tile opens a placeholder section page

Leads and accounts land in `data/guide.db`. Dev list: `GET /api/leads`.

## Stripe later

`/api/account` has a comment hook where Checkout Session creation goes.
The current Get Access button is labeled **Test · No Charge**.
