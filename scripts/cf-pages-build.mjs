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
  console.log(`Cloudflare Pages build OK: copied ${SRC}/ → ${DEST}/ (index.html ${count} bytes)`);
}
