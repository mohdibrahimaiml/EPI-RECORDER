/**
 * Seed EPI Labs product catalog in Paddle (sandbox or live).
 *
 * Sandbox (default):
 *   $env:PADDLE_API_KEY = "pdl_sdbx_..."
 *   node scripts/seed-paddle-catalog.mjs
 *
 * Live (explicit):
 *   $env:PADDLE_API_KEY = "pdl_live_..."   # or pdl_... live key
 *   $env:PADDLE_ENV = "live"
 *   $env:PADDLE_ALLOW_LIVE = "1"
 *   node scripts/seed-paddle-catalog.mjs
 *
 * Amounts are lowest-denomination strings (USD 10.00 => "1000").
 * Creates 3 products × (monthly + yearly) with 7-day trial and
 * country overrides for GB (GBP), IE (EUR), AU (AUD).
 */
import { writeFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const API_KEY = (process.env.PADDLE_API_KEY || process.env.PADDLE_LIVE_API_KEY || "").trim();
const ENV = (process.env.PADDLE_ENV || "sandbox").toLowerCase();
const IS_LIVE = ENV === "live" || ENV === "production";
const BASE = IS_LIVE
  ? "https://api.paddle.com"
  : "https://sandbox-api.paddle.com";

if (!API_KEY) {
  console.error(
    "Missing PADDLE_API_KEY.\n\n" +
      "Live:  https://vendors.paddle.com/authentication-v2\n" +
      "Sandbox: https://sandbox-vendors.paddle.com/authentication-v2\n" +
      "Scopes: product.write, price.write (or full access).\n\n" +
      "Live example (PowerShell):\n" +
      '  $env:PADDLE_API_KEY = "pdl_..."\n' +
      '  $env:PADDLE_ENV = "live"\n' +
      '  $env:PADDLE_ALLOW_LIVE = "1"\n' +
      "  node scripts/seed-paddle-catalog.mjs\n",
  );
  process.exit(1);
}

// Safety rails
const looksSandbox = /sdbx/i.test(API_KEY);
if (IS_LIVE) {
  if (process.env.PADDLE_ALLOW_LIVE !== "1") {
    console.error(
      "Live mode blocked: set PADDLE_ALLOW_LIVE=1 to confirm you want production catalog changes.",
    );
    process.exit(1);
  }
  if (looksSandbox) {
    console.error(
      "PADDLE_ENV=live but API key looks like sandbox (contains sdbx). Refusing.",
    );
    process.exit(1);
  }
} else {
  if (!looksSandbox && process.env.PADDLE_ALLOW_LIVE !== "1") {
    console.error(
      "Sandbox mode but key does not look like pdl_sdbx_... .\n" +
        "If this is intentional, set PADDLE_ALLOW_LIVE=1, or set PADDLE_ENV=live for production.",
    );
    process.exit(1);
  }
}

/**
 * PPP-style starting overrides (adjust later in dashboard).
 * Multipliers vs USD face amount (marketing-round):
 *   GB ~0.80 in GBP, IE ~0.90 in EUR, AU ~1.50 in AUD
 */
function overrides(usdCents) {
  const gbp = String(Math.round(usdCents * 0.8));
  const eur = String(Math.round(usdCents * 0.9));
  const aud = String(Math.round(usdCents * 1.5));
  return [
    {
      country_codes: ["GB"],
      unit_price: { amount: gbp, currency_code: "GBP" },
    },
    {
      country_codes: ["IE"],
      unit_price: { amount: eur, currency_code: "EUR" },
    },
    {
      country_codes: ["AU"],
      unit_price: { amount: aud, currency_code: "AUD" },
    },
  ];
}

const TRIAL = { interval: "day", frequency: 7 };

const CATALOG = [
  {
    name: "Starter",
    description:
      "EPI Labs Starter — hosted verify volume and API access for individuals getting started.",
    tax_category: "saas",
    prices: [
      {
        key: "monthly",
        description: "Starter monthly USD base",
        amount: "1000", // $10.00
        interval: "month",
      },
      {
        key: "yearly",
        description: "Starter yearly USD base",
        amount: "10000", // $100.00
        interval: "year",
      },
    ],
  },
  {
    name: "Pro",
    description:
      "EPI Labs Pro — higher hosted verification limits, API keys, remote SCITT for practitioners.",
    tax_category: "saas",
    prices: [
      {
        key: "monthly",
        description: "Pro monthly USD base",
        amount: "4000", // $40.00
        interval: "month",
      },
      {
        key: "yearly",
        description: "Pro yearly USD base",
        amount: "40000", // $400.00
        interval: "year",
      },
    ],
  },
  {
    name: "Advanced",
    description:
      "EPI Labs Advanced — team-scale hosted limits, more API keys, priority support path.",
    tax_category: "saas",
    prices: [
      {
        key: "monthly",
        description: "Advanced monthly USD base",
        amount: "12000", // $120.00
        interval: "month",
      },
      {
        key: "yearly",
        description: "Advanced yearly USD base",
        amount: "120000", // $1200.00
        interval: "year",
      },
    ],
  },
];

async function api(method, path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${API_KEY}`,
      "Content-Type": "application/json",
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  let json;
  try {
    json = JSON.parse(text);
  } catch {
    json = { raw: text };
  }
  if (!res.ok) {
    const err = new Error(
      `Paddle ${method} ${path} → ${res.status}: ${JSON.stringify(json, null, 2)}`,
    );
    err.status = res.status;
    err.body = json;
    throw err;
  }
  return json.data ?? json;
}

function fmtMoney(amountStr, currency) {
  const n = Number(amountStr);
  return `${currency} ${(n / 100).toFixed(2)}`;
}

async function seed() {
  const report = {
    environment: IS_LIVE ? "live" : "sandbox",
    api_base: BASE,
    created_at: new Date().toISOString(),
    tax_category: "saas",
    trial: "7 days on all recurring prices",
    regional_multipliers: {
      GB: "0.80 × USD face → GBP",
      IE: "0.90 × USD face → EUR",
      AU: "1.50 × USD face → AUD",
    },
    products: [],
  };

  console.log(
    `Seeding Paddle ${report.environment.toUpperCase()} catalog for EPI Labs...\n` +
      `API: ${BASE}\n`,
  );

  for (const plan of CATALOG) {
    const product = await api("POST", "/products", {
      name: plan.name,
      description: plan.description,
      tax_category: plan.tax_category,
      type: "standard",
    });

    const productRow = {
      name: plan.name,
      product_id: product.id,
      tax_category: plan.tax_category,
      prices: [],
    };

    console.log(`✓ Product ${plan.name}: ${product.id}`);

    for (const p of plan.prices) {
      const usd = Number(p.amount);
      const price = await api("POST", "/prices", {
        product_id: product.id,
        description: p.description,
        name: `${plan.name} ${p.interval === "month" ? "Monthly" : "Yearly"}`,
        type: "standard",
        billing_cycle: { interval: p.interval, frequency: 1 },
        trial_period: TRIAL,
        unit_price: { amount: p.amount, currency_code: "USD" },
        unit_price_overrides: overrides(usd),
        quantity: { minimum: 1, maximum: 1 },
      });

      const o = overrides(usd);
      const priceRow = {
        key: p.key,
        price_id: price.id,
        billing_cycle: p.interval,
        trial_days: 7,
        base: {
          currency: "USD",
          amount: p.amount,
          display: fmtMoney(p.amount, "USD"),
        },
        overrides: o.map((x) => ({
          countries: x.country_codes,
          currency: x.unit_price.currency_code,
          amount: x.unit_price.amount,
          display: fmtMoney(x.unit_price.amount, x.unit_price.currency_code),
        })),
      };
      productRow.prices.push(priceRow);

      console.log(
        `  ✓ ${p.key} ${price.id}  base ${fmtMoney(p.amount, "USD")} / ${p.interval}` +
          ` | GB ${fmtMoney(o[0].unit_price.amount, "GBP")}` +
          ` | IE ${fmtMoney(o[1].unit_price.amount, "EUR")}` +
          ` | AU ${fmtMoney(o[2].unit_price.amount, "AUD")}` +
          ` | trial 7d`,
      );
    }

    report.products.push(productRow);
  }

  const starterMo = report.products[0].prices.find((p) => p.key === "monthly");
  const starterYr = report.products[0].prices.find((p) => p.key === "yearly");
  const proMo = report.products[1].prices.find((p) => p.key === "monthly");
  const proYr = report.products[1].prices.find((p) => p.key === "yearly");
  const advancedMo = report.products[2].prices.find((p) => p.key === "monthly");
  const advancedYr = report.products[2].prices.find((p) => p.key === "yearly");

  report.suggested_env = {
    PADDLE_SANDBOX: IS_LIVE ? "false" : "true",
    PADDLE_STARTER_PRICE_ID_MONTHLY: starterMo?.price_id,
    PADDLE_STARTER_PRICE_ID_YEARLY: starterYr?.price_id,
    PADDLE_PRO_PRICE_ID: proMo?.price_id,
    PADDLE_PRO_PRICE_ID_YEARLY: proYr?.price_id,
    PADDLE_ADVANCED_PRICE_ID: advancedMo?.price_id,
    PADDLE_ADVANCED_PRICE_ID_YEARLY: advancedYr?.price_id,
    PADDLE_TEAM_PRICE_ID: advancedMo?.price_id,
  };

  const outDir = resolve(dirname(fileURLToPath(import.meta.url)), "..");
  const outName = IS_LIVE
    ? "paddle-catalog-live.json"
    : "paddle-catalog-sandbox.json";
  const outPath = resolve(outDir, outName);
  writeFileSync(outPath, JSON.stringify(report, null, 2), "utf8");

  console.log("\n========== CATALOG MAPPING ==========\n");
  console.log(JSON.stringify(report, null, 2));
  console.log(`\nWrote ${outPath}`);
  console.log("\nSuggested env:");
  for (const [k, v] of Object.entries(report.suggested_env)) {
    console.log(`  ${k}=${v}`);
  }
}

seed().catch((e) => {
  console.error("\nSeed failed:", e.message || e);
  if (e.status === 401 || e.status === 403) {
    console.error(
      "\nCheck API key permissions: product.write + price.write on the correct environment (live vs sandbox).",
    );
  }
  process.exit(1);
});
