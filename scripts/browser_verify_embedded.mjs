#!/usr/bin/env node
/**
 * Headless run of the EMBEDDED viewer verifier (epi_viewer_static/crypto.js).
 * This is the code baked into every .epi's viewer.html at seal time, not the site verifier.
 * Usage: node scripts/browser_verify_embedded.mjs <file.epi>
 * Prints { signature_valid, integrity_ok }
 * Integrity via JSZip hash check of file_manifest; signature via verifyManifestSignature.
 */
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { webcrypto } from "node:crypto";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const epiPath = process.argv[2];
if (!epiPath) {
  console.error("usage: node scripts/browser_verify_embedded.mjs <file.epi>");
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
// JSZip is inlined in web_viewer/jszip.min.js and also available as epi_viewer_static? Use web_viewer copy.
try {
  loadScript("web_viewer/jszip.min.js");
} catch {
  loadScript("website/js/jszip.min.js");
}
loadScript("epi_viewer_static/crypto.js");

if (typeof globalThis.verifyManifestSignature !== "function") {
  console.error("verifyManifestSignature not installed");
  process.exit(2);
}

// Extract ZIP payload from .epi (handle envelope-v2)
const raw = fs.readFileSync(epiPath);
let zipBytes;
const marker = Buffer.from("\n<!-- EPI_ZIP_PAYLOAD_START -->\n");
const idx = raw.indexOf(marker);
if (idx !== -1) {
  zipBytes = raw.subarray(idx + marker.length);
  // Need to slice to payload length from header (offset 8 u64 LE)
  try {
    const view = new DataView(raw.buffer, raw.byteOffset, raw.length);
    const lo = view.getUint32(8, true);
    const hi = view.getUint32(12, true);
    const len = lo + hi * 0x100000000;
    if (len > 0 && len < zipBytes.length) zipBytes = zipBytes.subarray(0, len);
  } catch {}
} else {
  zipBytes = raw;
}
const JSZip = globalThis.JSZip;
const zip = await JSZip.loadAsync(zipBytes);
const manifestEntry = zip.file("manifest.json");
if (!manifestEntry) {
  console.error("manifest.json missing");
  process.exit(2);
}
const rawManifest = await manifestEntry.async("string");
const manifest = JSON.parse(rawManifest);

// Signature
const sigRes = await globalThis.verifyManifestSignature(manifest, rawManifest);
const signature_valid = sigRes.valid === true;

// Integrity: hash each file_manifest entry
let integrity_ok = true;
const fm = manifest.file_manifest || {};
for (const name of Object.keys(fm)) {
  const expected = (fm[name] || "").toLowerCase();
  const entry = zip.file(name);
  if (!entry) { integrity_ok = false; break; }
  const bytes = await entry.async("uint8array");
  const hash = await globalThis.crypto.subtle.digest("SHA-256", bytes);
  const hex = Buffer.from(hash).toString("hex");
  if (hex !== expected) { integrity_ok = false; break; }
}
process.stdout.write(JSON.stringify({ signature_valid, integrity_ok, reason: sigRes.reason }) + "\n");
