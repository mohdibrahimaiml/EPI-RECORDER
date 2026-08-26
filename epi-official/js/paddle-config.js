/* ═══════════════════════════════════════════════════════════════════
   PADDLE LIVE CONFIG — EDIT THIS FILE
   Values come from your Paddle live dashboard. Never commit real
   tokens to a public repo — this file is referenced by .env.example
   and is intended to be filled in locally / via your deploy pipeline.
   ═══════════════════════════════════════════════════════════════════ */

window.EPI_PADDLE_CONFIG = {
  /* Paddle > Developer tools > Authentication > Client-side tokens.
     LIVE tokens are prefixed `live_`. */
  clientToken: "",

  /* "production" for live. NEVER leave this empty — the site fails loudly
     rather than guessing which Paddle account to talk to. */
  environment: "production",

  /* Success redirect after completed checkout. */
  successUrl: "/welcome/",

  /* If your users sign in somewhere, stash their email in
     localStorage under this key and checkout will pre-fill it. */
  emailStorageKey: "epi-user-email",

  /* ── Tier definitions — edit freely ──
     priceId values are Paddle price IDs (pri_...) from your LIVE catalog:
     one monthly + one yearly price per tier. */
  tiers: [
    {
      name: "Starter",
      description: "Seal and verify agent runs for a small team.",
      features: [
        "Up to 3 org members",
        "100 sealed runs / month",
        "Offline verify + embedded viewer",
        "Community support",
      ],
      featured: false,
      priceId: { month: "", year: "" }
    },
    {
      name: "Pro",
      description: "For teams shipping agents into regulated workflows.",
      features: [
        "Unlimited org members",
        "Unlimited sealed runs",
        "Org keys + trust bundles",
        "Policy rules + fault analyzer",
        "Priority support",
      ],
      featured: true,
      priceId: { month: "", year: "" }
    },
    {
      name: "Advanced",
      description: "Hosted custody, retention, and SCITT for enterprises.",
      features: [
        "Everything in Pro",
        "Hosted receipts + 7-year retention",
        "Remote SCITT registration",
        "Hosted verify at volume",
        "SLA + procurement support",
      ],
      featured: false,
      priceId: { month: "", year: "" }
    }
  ]
};
