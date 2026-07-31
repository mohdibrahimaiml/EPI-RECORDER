# EPI Labs operator runbook (internal)

**Customers never need this.** Hosted ops only.  
Customer/pilot docs: [PILOT.md](./PILOT.md) · [README.md](./README.md).

## Promote a user plan (no Paddle)

1. User must sign in once at https://epilabs.org/account  
2. Set `EPI_ADMIN_API_KEY` on Render  
3. PowerShell:

```powershell
$admin = "YOUR_ADMIN_KEY"
$body = @{ email = "user@example.com"; plan = "enterprise" } | ConvertTo-Json -Compress
Invoke-RestMethod -Method Post -Uri "https://epilabs.org/api/admin/set-plan" -Headers @{ "X-Admin-Key" = $admin } -ContentType "application/json; charset=utf-8" -Body $body
```

Plans: `free` | `pro` | `team` | `enterprise`

## Smoke hosted verify

```powershell
# After user creates CI key (optional) OR rely on session browser upload
curl.exe -sS -X POST "https://epilabs.org/api/verify" -H "X-API-Key: epi_..." -F "file=@run.epi"
```

## SCITT free gate

- Anonymous/free: HTTP **402**  
- Pro+ key or paid session: allowed when service key configured  

## Paddle (self-serve Pro)

Set on Render when ready: `PADDLE_CLIENT_TOKEN`, `PADDLE_PRO_PRICE_ID`, `PADDLE_API_KEY`, `PADDLE_WEBHOOK_SECRET`, `PADDLE_SANDBOX`.

Webhook: `https://epilabs.org/api/paddle/webhook`

## Customer path (send them this instead)

See [ENTERPRISE-15-MINUTES.md](./ENTERPRISE-15-MINUTES.md).
