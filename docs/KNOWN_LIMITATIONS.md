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

## Hosted billing (Paddle) vs operator set-plan

**Self-serve Subscribe is only live when Paddle env vars are configured** on the
hosted API (client token, price IDs, webhook secret, etc.). If those are empty,
pricing CTAs should fall back to sign-in / contact — not a working checkout.

**Pilot / invoice path (works without Paddle):** user signs in once at
`/account`, then EPI Labs promotes the plan with the admin **set-plan** endpoint
(see [OPERATOR-RUNBOOK.md](./OPERATOR-RUNBOOK.md) — operators only).

Public tiers (product gates): Free (low hosted cap) · **Pro** (~10k hosted
checks/mo) · **Team** (higher volume) · **Enterprise** (custom). Offline CLI
verify is unlimited free. Hosted PDF API is **not** implemented (HTTP 501);
use CLI Annex PDF.

There is **no automated sync** between the Paddle dashboard and Render env vars —
ops must keep them aligned when self-serve is enabled.

---

## Last updated

2026-07-31 — pricing/billing note aligned with Pro/Team/Enterprise + set-plan path.
