# Known Limitations

This file tracks gaps between what the product can do and what a user might
reasonably expect. Each entry names the gap honestly, not as a bug report but as
a current boundary. No implied promises — just what's true right now.

---

## Pre-execution commitment (llm.pre_commit)

**Streaming calls skip pre-commit entirely.** Both `openai.py` and `anthropic.py`
generate `llm.pre_commit` entries for non-streaming API calls, but streaming
paths (`stream=True`) silently fall back to the old behavior with no pre-commit
entry. No error, no warning — the chain just doesn't include the commitment step.

This affects anyone using streaming responses. The pricing page now notes
"(non-streaming calls)" next to this feature.

---

## Hosted infrastructure

**Render free tier.** The verify API, SCITT service, and account system all run
on a single Render free-tier instance (`render.yaml: plan: free`). This means:

- 750 hours/month limit (~31 days)
- Sleeps after 15 minutes of inactivity
- Cold starts cause 2-5 second delays on first request
- No horizontal scaling
- No SLA, no uptime guarantee

The status page (`/status`) discloses this and the pricing page says "shared
infrastructure, cold starts happen." Offline CLI verify works regardless.

---

## verification_class auto-population

**The model_validator doesn't fire during recording.** Steps are serialized as
raw dicts in `packer.py`, bypassing Pydantic's `model_validator`. The
classification is computed inline via `_compute_verification_class()` in
`packer.py`. If a new step kind is added without updating that function, it gets
`None` instead of a classification.

---

## Starter tier in $1 vs $10

**The Paddle catalog was seeded with $10 Starter prices first, then replaced
with $1 prices.** The Render env vars must be kept in sync manually — if someone
pushes the old `PADDLE_STARTER_PRICE_ID_MONTHLY=pri_01kyg26d8sf...` (the $10
price), the Starter tier on the pricing page will show $10. There's no automated
sync between the Paddle dashboard and Render env vars.

---

## Last updated

2026-07-27 — created after the pre-commit + notarization + verification_class build session.
