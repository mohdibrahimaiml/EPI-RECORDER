# Compliance quickstart (redirect)

> **This page is a short pointer.** It replaces an older draft that incorrectly
> mentioned an AGPL dual-license model. **EPI Recorder is MIT licensed**
> (see root `LICENSE` and [README.md](../README.md)).

EPI produces **portable evidence files** (`.epi`). They help with audit trails.  
They are **not** a compliance certificate or legal advice.

---

## Enterprise / pilot path (recommended)

```bash
pip install epi-recorder   # or pin git — see PILOT.md
epi enterprise setup
# record one agent run → your-run.epi
epi enterprise pack your-run.epi
epi verify your-run.epi
```

- Pilot pack: [PILOT.md](./PILOT.md)  
- 15 minutes: [ENTERPRISE-15-MINUTES.md](./ENTERPRISE-15-MINUTES.md)  
- Honest capability matrix: [ENTERPRISE-CAPABILITY.md](./ENTERPRISE-CAPABILITY.md)  

---

## Annex IV tooling (optional technical docs)

If you specifically need Annex IV packaging in the CLI:

```bash
epi annex --help
```

Details: [ANNEX-IV.md](./ANNEX-IV.md).

---

## Hand to an auditor

The **`.epi` file** is the sealed artifact. Auditors can verify offline or in the browser (private mode does not upload the file).

See: [AUDITORS-GUIDE.md](./AUDITORS-GUIDE.md).

---

## Pricing (high level)

- **Open source (MIT):** offline record, seal, verify — free  
- **Hosted Pro / Team / Enterprise:** hosted verify volume, remote SCITT where configured, support — see https://epilabs.org/pricing  

Docs map: [README.md](./README.md).
