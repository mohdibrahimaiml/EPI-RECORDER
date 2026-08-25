/* Runtime verification of the browser verifier logic in Node.
 * Loads js/epi-verify-core.js (same code served to browsers) and runs it
 * against assets/sample.epi — plus tampered and truncated failure modes.
 *
 * Node 24 has WebCrypto (crypto.subtle) at globalThis.crypto, so the
 * Ed25519 path executes for real. JSZip is loaded from the vendored file.
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const WEB = path.resolve(__dirname, "..", "website");
const sandbox = {
  console,
  crypto: globalThis.crypto,
  fetch: async () => { throw new Error("no fetch in test"); },
  atob: (s) => Buffer.from(s, "base64").toString("binary"),
  btoa: (s) => Buffer.from(s, "binary").toString("base64"),
  setTimeout,
  TextEncoder,
  TextDecoder,
};
sandbox.window = sandbox;
sandbox.globalThis = sandbox;
vm.createContext(sandbox);

// Load vendored JSZip
const jszipSrc = fs.readFileSync(path.join(WEB, "js", "jszip.min.js"), "utf8");
vm.runInContext(jszipSrc, sandbox);

// Load epi-verify-core.js
const coreSrc = fs.readFileSync(path.join(WEB, "js", "epi-verify-core.js"), "utf8");
vm.runInContext(coreSrc, sandbox);

function toBlobLike(bytes) {
  // verifyEPI only calls .arrayBuffer() on its input
  return {
    arrayBuffer: async () => bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength),
    name: "sample.epi",
  };
}

async function main() {
  const verify = sandbox.window.verifyEPI;
  if (typeof verify !== "function") throw new Error("window.verifyEPI missing");
  if (typeof sandbox.JSZip === "undefined") throw new Error("JSZip missing");

  const original = new Uint8Array(fs.readFileSync(path.join(WEB, "assets", "sample.epi")));
  const results = {};

  // 1. Happy path
  const ok = await verify(toBlobLike(original));
  results.valid = {
    structure: ok.structure,
    integrity: ok.integrity,
    signature: ok.signature,
    trust_level: ok.trust_level,
    signer: ok.signer ? String(ok.signer).slice(0, 12) + "..." : null,
    hash: ok.hash ? ok.hash.slice(0, 12) + "..." : null,
  };

  // 2. Tampered byte INSIDE the ZIP payload (near end of file — past the
  //    embedded viewer HTML, which is intentionally outside the seal).
  const tampered = original.slice();
  const flipAt = tampered.length - Math.floor(tampered.length * 0.05) - 1;
  tampered[flipAt] ^= 0xff;
  const bad = await verify(toBlobLike(tampered));
  results.tampered = {
    flipped_offset: flipAt,
    file_len: tampered.length,
    integrity: bad.integrity,
    signature: bad.signature,
    trust_level: bad.trust_level,
    mismatches: (bad.mismatches || []).length,
  };

  // 3. Truncated file
  const trunc = await verify(toBlobLike(original.slice(0, 1000)));
  results.truncated = {
    structure: trunc.structure,
    trust_level: trunc.trust_level,
    message: (trunc.message || "").slice(0, 80),
  };
  // 4. Garbage input
  const garbage = await verify(toBlobLike(new TextEncoder().encode("this is not an epi file at all")));
  results.garbage = {
    structure: garbage.structure,
    trust_level: garbage.trust_level,
    message: (garbage.message || "").slice(0, 60),
  };

  console.log(JSON.stringify(results, null, 2));

  // Assertions
  const a = [];
  a.push(["valid.structure", results.valid.structure === true]);
  a.push(["valid.integrity", results.valid.integrity === true]);
  a.push(["valid.signature===true", results.valid.signature === true]);
  a.push(["valid.trust=UNVERIFIED_IDENTITY", results.valid.trust_level === "UNVERIFIED_IDENTITY"]);
  a.push(["valid.hasSigner", !!results.valid.signer]);
  a.push(["tampered.fails", results.tampered.integrity === false || results.tampered.signature === false]);
  a.push(["truncated.rejected", results.truncated.structure === false || /not|invalid|small|zip/i.test(results.truncated.message || "")]);
  a.push(["garbage.rejected", results.garbage.structure === false && /not/i.test(results.garbage.message || "")]);

  let failed = 0;
  for (const [name, pass] of a) {
    console.log((pass ? "PASS" : "FAIL") + "  " + name);
    if (!pass) failed++;
  }
  process.exit(failed ? 1 : 0);
}

main().catch((e) => { console.error("TEST ERROR:", e); process.exit(2); });
