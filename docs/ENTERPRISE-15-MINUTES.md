# Enterprise in 15 minutes

**For:** customer engineers on a pilot.  
**Not for:** Render, admin keys, or curl (those are EPI Labs ops only).

## What you get

A **sealed evidence file** (`.epi`) you can check offline, plus an **auditor pack** zip.

## Steps

```bash
pip install epi-recorder

# 1) Company kit (keys, trust bundle, policy, CI recipe)
epi enterprise setup

# 2) Record one real agent run into a .epi
#    (your code with record() / wrap_openai, or epi demo)

# 3) Build the pack to hand to audit / security
epi enterprise pack your-run.epi
```

That’s it.

| File | Who can see it |
|------|----------------|
| `org-trust-bundle.zip` | CI, auditors (public keys only) |
| `auditor-pack.zip` | Auditors |
| Private keys in `~/.epi/keys/` | **Never commit / never share** |

## Online checks (optional)

If your plan is Pro / Team / Enterprise:

1. Sign in at https://epilabs.org/account  
2. Open **Verify a file**  
3. Drop the `.epi` — **no API key needed** in the browser  

API keys are only for **CI/scripts** (Advanced on the account page).

## Full inventory

```bash
epi enterprise capabilities
```

See also: [ENTERPRISE-CAPABILITY.md](./ENTERPRISE-CAPABILITY.md) · full guide: [COMPLETE-PRODUCT-GUIDE.md](./COMPLETE-PRODUCT-GUIDE.md).
