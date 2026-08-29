#!/usr/bin/env node
/**
 * Headless run of the website browser verifier (JSZip + epi-manifest-preimage + epi-verify-core).
 * Usage: node scripts/browser_verify_signature.mjs <file.epi>
 * Prints one JSON object: { signature_valid, integrity_ok, trust_level }
 */
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { webcrypto } from "node:crypto";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const epiPath = process.argv[2];
if (!epiPath) {
  console.error("usage: node scripts/browser_verify_signature.mjs <file.epi>");
  process.exit(2);
}

if (!globalThis.crypto) {
  Object.defineProperty(globalThis, "crypto", { value: webcrypto, configurable: true });
}

function loadScript(rel) {
  const abs = path.join(root, rel);
  const src = fs.readFileSync(abs, "utf8");
  vm.runInThisContext(src, { filename: abs });
}

loadScript("website/js/jszip.min.js");
loadScript("website/js/epi-manifest-preimage.js");
loadScript("website/js/epi-verify-core.js");

if (typeof globalThis.verifyEPI !== "function") {
  console.error("verifyEPI was not installed on globalThis");
  process.exit(2);
}

const buf = fs.readFileSync(epiPath);
const file = new File([buf], path.basename(epiPath), { type: "application/vnd.epi+zip" });
const r = await globalThis.verifyEPI(file);
process.stdout.write(
  JSON.stringify({
    signature_valid: r.signature,
    integrity_ok: r.integrity,
    trust_level: r.trust_level,
  }) + "\n"
);
