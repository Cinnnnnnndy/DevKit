import { existsSync, mkdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import {
  ARTIFACTS_DIR,
  artifactBaseName,
  artifactFileName,
  parseTarVerboseMetadata,
  parseJsonValue,
  PROJECT_ROOT,
  parseChecksumFile,
  RELEASE_DEVELOPMENT_OVERRIDE,
  RELEASE_TARGETS,
  RELEASE_VERSION,
  resetGeneratedDirectory,
  run,
  sha256File,
  VERIFY_WORK_DIR,
  validateArchiveEntries,
  validateLinuxArchiveModes,
  validateManifest,
  validateThirdPartyLicenseIndex,
  verifyExecutable,
} from "./release-lib.js";

const checksumPath = join(ARTIFACTS_DIR, "SHA256SUMS");
if (!existsSync(checksumPath))
  throw new Error(`Missing ${checksumPath}; run bun run package:all first`);
const checksums = parseChecksumFile(readFileSync(checksumPath, "utf8"));
if (checksums.size !== RELEASE_TARGETS.length) {
  throw new Error(`Expected ${RELEASE_TARGETS.length} checksums, received ${checksums.size}`);
}

resetGeneratedDirectory(VERIFY_WORK_DIR, join(PROJECT_ROOT, ".codex_tmp"));
const allowDevelopment = process.env[RELEASE_DEVELOPMENT_OVERRIDE] === "1";
for (const target of RELEASE_TARGETS) {
  const fileName = artifactFileName(target);
  const archivePath = join(ARTIFACTS_DIR, fileName);
  if (!existsSync(archivePath)) throw new Error(`Missing ${fileName}`);
  const expectedHash = checksums.get(fileName);
  const actualHash = await sha256File(archivePath);
  if (expectedHash !== actualHash) throw new Error(`SHA-256 mismatch for ${fileName}`);

  const entries = (await run(["tar", "-tf", archivePath], { capture: true }))
    .split(/\r?\n/)
    .filter(Boolean);
  const payloadName = artifactBaseName(target);
  validateArchiveEntries(entries, payloadName);
  const required = [
    `${payloadName}/${target.binaryName}`,
    `${payloadName}/README.md`,
    `${payloadName}/NOTICE.md`,
    `${payloadName}/LICENSE.txt`,
    `${payloadName}/manifest.json`,
    `${payloadName}/licenses/index.json`,
  ];
  for (const entry of required) {
    if (!entries.includes(entry)) throw new Error(`${fileName} is missing ${entry}`);
  }
  if (target.os === "linux") {
    const metadata = parseTarVerboseMetadata(
      await run(["tar", "-tvf", archivePath], { capture: true }),
    );
    validateLinuxArchiveModes(metadata, payloadName);
  }

  const extractDir = join(VERIFY_WORK_DIR, target.id);
  mkdirSync(extractDir, { recursive: true });
  await run(["tar", "-xf", archivePath, "-C", extractDir]);
  const payload = join(extractDir, payloadName);
  const manifest = parseJsonValue(
    readFileSync(join(payload, "manifest.json"), "utf8"),
    "manifest.json",
  );
  validateManifest(manifest, target, { allowDevelopment });
  const licenseIndex = parseJsonValue(
    readFileSync(join(payload, "licenses", "index.json"), "utf8"),
    "licenses/index.json",
  );
  validateThirdPartyLicenseIndex(licenseIndex, target, new Set(entries), payloadName);
  verifyExecutable(join(payload, target.binaryName), target);

  if (target.os === "windows") {
    const version = await run([join(payload, target.binaryName), "--version"], { capture: true });
    const help = await run([join(payload, target.binaryName), "--help"], { capture: true });
    const smoke = await run([join(payload, target.binaryName), "--smoke-render"], {
      capture: true,
    });
    if (
      version !== `devkitai ${RELEASE_VERSION}` ||
      !help.includes("Usage: devkitai") ||
      !smoke.includes("devkitai smoke-render ok")
    ) {
      throw new Error(`Extracted Windows smoke failed: ${version}`);
    }
  }
  console.log(`verified ${fileName}`);
}

console.log(`Verified ${RELEASE_TARGETS.length} package(s), manifests and SHA-256 checksums`);
