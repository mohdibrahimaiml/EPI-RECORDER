# EPI Labs operator runbook (internal)

**Customers never need this.** Hosted ops only.  
Customer/pilot docs: [PILOT.md](./PILOT.md) · [README.md](./README.md) · [KNOWN_LIMITATIONS.md](./KNOWN_LIMITATIONS.md).

---

## Plan keys (source of truth)

Backend plans after `normalize_plan` (see `verify_portal/auth.py`, `tier_gating.py`):

| Plan key | Public label | Notes |
|----------|--------------|--------|
| `free` | Free / Open Source | Default after GitHub sign-in |
| `hosted` | Hosted (~$15) | Self-serve Paddle SKU |
| `team` | Team | Design partners / higher volume |
| `enterprise` | Enterprise | Invoice / pilot / custom |

**Aliases** (accepted by set-plan and webhooks):

- `pro`, `starter` → **`hosted`**
- `advanced`, `advance`, `business` → **`team`**

Account UI shows **Hosted**, not “Pro”, for paid self-serve.

---

## Render environment checklist

Service: **epi-verify-portal** (or current Render service name).  
Redeploy after changing env.

### Auth (required for sign-in)

| Variable | Purpose |
|----------|---------|
| `GITHUB_CLIENT_ID` | GitHub OAuth App client id |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth secret |
| `EPI_FRONTEND_URL` | `https://epilabs.org` |
| `EPI_VERIFY_BASE_URL` | Public API origin, e.g. `https://epi-verify-portal.onrender.com` |

GitHub OAuth App **Authorization callback URL** must be:

```text
https://epi-verify-portal.onrender.com/api/auth/github/callback
```

(Use your real Render hostname if different.)

### Durable auth DB

| Variable | Purpose |
|----------|---------|
| Turso / remote auth config used by `verify_portal.db` | Prefer durable backend so plans survive deploys |

Check: `GET https://epilabs.org/api/auth/status` → `oauth_configured: true`, `db_durable: true` when healthy.

### Admin (manual plan promote)

| Variable | Purpose |
|----------|---------|
| `EPI_ADMIN_API_KEY` | Long random secret; header `X-Admin-Key` |

### Paddle (self-serve Hosted)

| Variable | Purpose |
|----------|---------|
| `PADDLE_ENV` | `live` or `sandbox` |
| `PADDLE_SANDBOX` | `false` for live, `true` for sandbox |
| `PADDLE_CLIENT_TOKEN` | Client-side token (`live_…` / `test_…`) — powers checkout UI |
| `PADDLE_API_KEY` | Server API key (customer lookup, ops) |
| `PADDLE_WEBHOOK_SECRET` | **Endpoint secret** from Paddle notification destination |
| `PADDLE_HOSTED_PRICE_ID_MONTHLY` | Hosted monthly price id `pri_…` |
| `PADDLE_HOSTED_PRICE_ID_YEARLY` | Hosted yearly price id `pri_…` |
| `PADDLE_PRO_PRICE_ID` / `_YEARLY` | Optional legacy; still mapped → `hosted` |
| `PADDLE_ADVANCED_PRICE_ID` / `_YEARLY` | Optional → `team` |
| `PADDLE_ENTERPRISE_PRICE_ID` | Optional → `enterprise` |

Verify checkout config (no secrets leaked beyond public client token + price ids):

```powershell
Invoke-RestMethod "https://epilabs.org/api/paddle/config"
# Expect: client_token set, environment production|sandbox,
# tiers.hosted.month / year = pri_...
```

---

## Paddle webhook setup

1. Paddle Dashboard (Live or Sandbox matching `PADDLE_ENV`).
2. **Developer tools → Notifications** (webhooks).
3. Destination URL (prefer Render, avoid extra hops):

```text
https://epi-verify-portal.onrender.com/api/paddle/webhook
```

Also valid if Cloudflare proxy is healthy:

```text
https://epilabs.org/api/paddle/webhook
```

4. Subscribe at least:

- `subscription.created`
- `subscription.updated`
- `subscription.activated`
- `subscription.canceled`
- `subscription.paused`
- `subscription.past_due`

5. Copy **endpoint secret** → Render `PADDLE_WEBHOOK_SECRET`.
6. Redeploy Render.

### Signature verification (code)

`verify_portal/billing.py` validates:

- Header `Paddle-Signature`: `ts=…;h1=…`
- `h1` = **HMAC-SHA256** of `ts:rawBody` with the webhook secret  
- Plain SHA-256 of the body is **rejected**

If the secret is wrong or missing while Paddle sends a signature, webhooks return **401** and buyers stay **Free**.

### How plan attaches after purchase

1. Buyer must **Sign in with GitHub** first (creates user row in Turso/auth DB).
2. Pricing checkout sends `customData.user_id` + email (requires `epi_token` + `epi_user` in browser).
3. Webhook applies plan in order: **user_id** → **email** → **customer_id**.
4. Success URL: `/account?checkout=success` — user should see plan badge after refresh if webhook is fast.

---

## Promote a user plan (no Paddle / safety net)

Use for: invoice paid, webhook miss, email mismatch, enterprise pilot, QA.

### Prerequisites

1. User signed in **once** at https://epilabs.org/account (creates the user).
2. `EPI_ADMIN_API_KEY` set on Render.
3. You know their **GitHub account email** (shown on Account) or internal `user_id`.

### PowerShell

```powershell
$admin = "YOUR_EPI_ADMIN_API_KEY"

# Hosted (paid package)
$body = @{
  email = "user@example.com"   # exact email on Account page
  plan  = "hosted"               # free | hosted | pro | team | enterprise
} | ConvertTo-Json -Compress

Invoke-RestMethod `
  -Method Post `
  -Uri "https://epilabs.org/api/admin/set-plan" `
  -Headers @{ "X-Admin-Key" = $admin } `
  -ContentType "application/json; charset=utf-8" `
  -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
```

By user id:

```powershell
$body = @{ user_id = "uuid-from-db"; plan = "enterprise" } | ConvertTo-Json -Compress
# same Invoke-RestMethod
```

### Expected results

| HTTP | Meaning |
|------|---------|
| 200 | Plan updated; user refreshes `/account` |
| 401 | Wrong/missing admin key |
| 404 | User never signed in with that email / bad user_id |
| 400 | Missing email and user_id |

Plans accepted: `free` | `hosted` | `pro` (→ hosted) | `team` | `enterprise`.

---

## Buyer path (what to tell customers)

1. Open https://epilabs.org/account → **Continue with GitHub**.  
2. Open https://epilabs.org/pricing → **Subscribe — Hosted**.  
3. Complete Paddle checkout (use the same email as GitHub when possible).  
4. Land on Account → confirm plan **Hosted**.  
5. If still Free after 1–2 minutes: contact ops (webhook/email mismatch) → use **set-plan**.

Checkout while logged out redirects to Account with a hint (by design).

---

## Smoke checks

### Auth

```powershell
Invoke-RestMethod "https://epilabs.org/api/auth/status"
# oauth_configured should be true
Invoke-RestMethod "https://epilabs.org/api/ping"
```

### Paddle public config

```powershell
Invoke-RestMethod "https://epilabs.org/api/paddle/config"
```

### Hosted verify (API key)

```powershell
curl.exe -sS -X POST "https://epilabs.org/api/verify" `
  -H "X-API-Key: epi_..." `
  -F "file=@run.epi"
```

### SCITT remote gate

- Free / anonymous: often HTTP **402**  
- Hosted+ session or paid API key: allowed when SCITT service is configured  

---

## Ops failure cheat sheet

| Symptom | Likely fix |
|---------|------------|
| Sign-in fails / oauth_not_configured | GitHub env + callback URL on Render |
| Subscribe → “Sign in” / no overlay | Missing client token or price ids on Render |
| Paid but Account still Free | Webhook secret, signature 401, or user never signed in / email mismatch → **set-plan** |
| set-plan 404 | User must OAuth once first |
| Cold start 30s on first hit | Free Render plan; wake via `/api/ping`; UX already retries |

---

## Customer path (send them this instead)

See [ENTERPRISE-15-MINUTES.md](./ENTERPRISE-15-MINUTES.md) · [PILOT.md](./PILOT.md).

---

## Last updated

2026-08-01 — Hosted plan keys, HOSTED price env vars, webhook HMAC, checkout requires sign-in, set-plan PowerShell.
