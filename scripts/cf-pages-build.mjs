/**
 * Cloudflare Pages build step.
 *
 * Canonical static site lives in website/. CF Pages needs a build output
 * directory — we copy website/ → site/ with no transform.
 *
 * Build command:        npm run build
 * Build output directory: site (wrangler.toml: pages_build_output_dir = "site")
 * Root directory:       (repo root, leave empty)
 */
import { cpSync, existsSync, mkdirSync, rmSync, writeFileSync, readFileSync } from "node:fs";
import { join } from "node:path";

const SRC = "website";
const DESTINATIONS = ["site", "dist"];

if (!existsSync(SRC)) {
  console.error(`ERROR: ${SRC}/ not found. Cloudflare Pages must build from repo root.`);
  process.exit(1);
}
if (!existsSync(join(SRC, "index.html"))) {
  console.error(`ERROR: ${SRC}/index.html missing.`);
  process.exit(1);
}

for (const DEST of DESTINATIONS) {
  rmSync(DEST, { recursive: true, force: true });
  mkdirSync(DEST, { recursive: true });
  cpSync(SRC, DEST, { recursive: true });

  // Never ship directory-style pricing/ (old Starter/Pro SaaS page).
  // Canonical is flat pricing.html — directory routes can shadow it on CF.
  const stalePricing = join(DEST, "pricing");
  if (existsSync(stalePricing)) {
    rmSync(stalePricing, { recursive: true, force: true });
    console.log(`Removed stale ${DEST}/pricing/ directory`);
  }

  // Ensure CF treats this as a static site (not a Worker-only project)
  const routesPath = join(DEST, "_routes.json");
  writeFileSync(
    routesPath,
    JSON.stringify(
      {
        version: 1,
        include: ["/*"],
        exclude: [],
      },
      null,
      2,
    ),
  );

  const count = (() => {
    try {
      return readFileSync(join(DEST, "index.html"), "utf8").length;
    } catch {
      return 0;
    }
  })();
  const pricingHead = (() => {
    try {
      return readFileSync(join(DEST, "pricing.html"), "utf8").slice(0, 200);
    } catch {
      return "";
    }
  })();
  if (pricingHead && !pricingHead.includes("Agent Evidence Sprint") && !pricingHead.includes("$1,500") && !pricingHead.includes("$1500")) {
    console.warn(`WARNING: ${DEST}/pricing.html may not be the honest sprint page`);
  }
  console.log(`Cloudflare Pages build OK: copied ${SRC}/ → ${DEST}/ (index.html ${count} bytes)`);
}
