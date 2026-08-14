import { createHash } from "node:crypto";
import {
  cpSync,
  createReadStream,
  createWriteStream,
  existsSync,
  mkdirSync,
  readdirSync,
  readFileSync,
  rmSync,
  statSync,
  writeFileSync,
} from "node:fs";
import { basename, dirname, isAbsolute, join, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { createGzip } from "node:zlib";
import { pipeline } from "node:stream/promises";

export const PROJECT_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
export const ARTIFACTS_DIR = join(PROJECT_ROOT, "artifacts", "release");
export const RELEASE_WORK_DIR = join(PROJECT_ROOT, ".codex_tmp", "release");
export const VERIFY_WORK_DIR = join(PROJECT_ROOT, ".codex_tmp", "release-verify");

interface RootPackageJson {
  readonly version: string;
  readonly dependencies: Readonly<Record<string, string>>;
  readonly devDependencies: Readonly<Record<string, string>>;
}

/**
 * Keeps JSON.parse's library-level `any` from escaping into application code.
 * Callers must narrow the returned value at the boundary before reading fields.
 */
export function parseJsonValue(contents: string, label: string): unknown {
  try {
    const parsed: unknown = JSON.parse(contents);
    return parsed;
  } catch (cause) {
    throw new Error(`${label} is not valid JSON`, { cause });
  }
}

function parseRootPackageJson(value: unknown): RootPackageJson {
  const packageJson = recordValue(value, "package.json");
  const version = packageJson["version"];
  if (typeof version !== "string" || version === "") {
    throw new Error("package.json must contain a non-empty version");
  }
  return {
    version,
    dependencies: stringRecordValue(packageJson["dependencies"], "package.json dependencies"),
    devDependencies: stringRecordValue(
      packageJson["devDependencies"],
      "package.json devDependencies",
    ),
  };
}

const PACKAGE_JSON = parseRootPackageJson(
  parseJsonValue(readFileSync(join(PROJECT_ROOT, "package.json"), "utf8"), "package.json"),
);

export const RELEASE_VERSION = PACKAGE_JSON.version;
export const BUN_VERSION = requiredVersion(PACKAGE_JSON.devDependencies["bun"], "bun");

function requiredVersion(value: string | undefined, name: string): string {
  if (value === undefined || value === "")
    throw new Error(`Missing locked dependency version: ${name}`);
  return value;
}

export type ReleaseTargetId = "windows-x64" | "linux-x86_64" | "linux-arm64";

export interface ReleaseTarget {
  readonly id: ReleaseTargetId;
  readonly os: "windows" | "linux";
  readonly installOs: "win32" | "linux";
  readonly cpu: "x64" | "arm64";
  readonly arch: "x86_64" | "arm64";
  readonly baseline: boolean;
  readonly bunTarget: string;
  readonly runtimePackage: string;
  readonly runtimeExecutable: string;
  readonly binaryName: "devkitai.exe" | "devkitai";
  readonly archiveExtension: ".zip" | ".tar.gz";
  readonly expectedMachine: number;
  readonly expectedNativeMarker: string;
  readonly nativePackage: string;
}

export const RELEASE_TARGETS: readonly ReleaseTarget[] = [
  {
    id: "windows-x64",
    os: "windows",
    installOs: "win32",
    cpu: "x64",
    arch: "x86_64",
    baseline: true,
    bunTarget: "bun-windows-x64-baseline",
    runtimePackage: "@oven/bun-windows-x64-baseline",
    runtimeExecutable: "bin/bun.exe",
    binaryName: "devkitai.exe",
    archiveExtension: ".zip",
    expectedMachine: 0x8664,
    expectedNativeMarker: "opentui.dll",
    nativePackage: "@opentui/core-win32-x64",
  },
  {
    id: "linux-x86_64",
    os: "linux",
    installOs: "linux",
    cpu: "x64",
    arch: "x86_64",
    baseline: true,
    bunTarget: "bun-linux-x64-baseline",
    runtimePackage: "@oven/bun-linux-x64-baseline",
    runtimeExecutable: "bin/bun",
    binaryName: "devkitai",
    archiveExtension: ".tar.gz",
    expectedMachine: 62,
    expectedNativeMarker: "libopentui.so",
    nativePackage: "@opentui/core-linux-x64",
  },
  {
    id: "linux-arm64",
    os: "linux",
    installOs: "linux",
    cpu: "arm64",
    arch: "arm64",
    baseline: false,
    bunTarget: "bun-linux-arm64",
    runtimePackage: "@oven/bun-linux-aarch64",
    runtimeExecutable: "bin/bun",
    binaryName: "devkitai",
    archiveExtension: ".tar.gz",
    expectedMachine: 183,
    expectedNativeMarker: "libopentui.so",
    nativePackage: "@opentui/core-linux-arm64",
  },
] as const;

export interface ReleaseManifest {
  readonly schemaVersion: 1;
  readonly product: "Kunpeng DevKit AI";
  readonly binary: "devkitai";
  readonly version: string;
  readonly commit: string;
  readonly dirty: boolean;
  readonly builtAt: string;
  readonly target: {
    readonly id: ReleaseTargetId;
    readonly os: "windows" | "linux";
    readonly arch: "x86_64" | "arm64";
    readonly baseline: boolean;
    readonly bunTarget: string;
  };
  readonly toolchain: {
    readonly bun: string;
    readonly typescript: string;
    readonly react: string;
    readonly opentuiCore: string;
    readonly opentuiReact: string;
  };
  readonly nativeVerification: {
    readonly status: "verified" | "native-runtime-unverified";
    readonly checks: readonly string[];
  };
}

export const RELEASE_DEVELOPMENT_OVERRIDE = "DEVKITAI_ALLOW_DEVELOPMENT_RELEASE";
export const REQUIRED_NATIVE_LICENSE_FILES = [
  "LICENSE",
  "LICENSE-LCMS2",
  "LICENSE-LIBWEBP",
  "LICENSE-STB",
  "LICENSE-WUFFS",
  "PATENTS-LIBWEBP",
] as const;

export interface ThirdPartyLicenseEntry {
  readonly name: string;
  readonly version: string;
  readonly declaredLicense: string;
  readonly files: readonly string[];
}

export interface ThirdPartyLicenseIndex {
  readonly schemaVersion: 1;
  readonly target: ReleaseTargetId;
  readonly packages: readonly ThirdPartyLicenseEntry[];
}

export interface ArchiveMetadataEntry {
  readonly path: string;
  readonly type: "directory" | "file";
  readonly mode: number;
}

export function artifactBaseName(target: ReleaseTarget): string {
  return `kunpeng-devkit-ai-tui-${RELEASE_VERSION}-${target.id}`;
}

export function artifactFileName(target: ReleaseTarget): string {
  return `${artifactBaseName(target)}${target.archiveExtension}`;
}

export function assertSafeGeneratedPath(candidate: string, allowedParent: string): void {
  const resolvedCandidate = resolve(candidate);
  const resolvedParent = resolve(allowedParent);
  const relativePath = relative(resolvedParent, resolvedCandidate);
  if (
    resolvedCandidate === resolvedParent ||
    relativePath === "" ||
    relativePath === ".." ||
    relativePath.startsWith(`..${sep}`) ||
    isAbsolute(relativePath)
  ) {
    throw new Error(`Refusing generated-path operation outside child scope: ${resolvedCandidate}`);
  }
}

export function resetGeneratedDirectory(candidate: string, allowedParent: string): void {
  assertSafeGeneratedPath(candidate, allowedParent);
  if (existsSync(candidate)) rmSync(candidate, { recursive: true, force: true });
  mkdirSync(candidate, { recursive: true });
}

export function validateArchiveEntries(entries: readonly string[], expectedRoot: string): void {
  if (entries.length === 0) throw new Error("Archive is empty");
  const normalizedRoot = `${expectedRoot}/`;
  for (const rawEntry of entries) {
    const entry = rawEntry.replaceAll("\\", "/").replace(/^\.\//, "");
    if (
      entry.startsWith("/") ||
      /^[A-Za-z]:\//.test(entry) ||
      entry.split("/").includes("..") ||
      (entry !== expectedRoot && !entry.startsWith(normalizedRoot))
    ) {
      throw new Error(`Unsafe archive entry: ${rawEntry}`);
    }
  }
}

export function inspectExecutableHeader(buffer: Uint8Array): {
  format: "PE" | "ELF";
  machine: number;
} {
  // Read standardized ELF/PE magic bytes and machine offsets instead of trusting filenames.
  if (
    buffer.length >= 64 &&
    buffer[0] === 0x7f &&
    buffer[1] === 0x45 &&
    buffer[2] === 0x4c &&
    buffer[3] === 0x46
  ) {
    if (buffer[4] !== 2 || buffer[5] !== 1)
      throw new Error("Only 64-bit little-endian ELF is supported");
    return {
      format: "ELF",
      machine: new DataView(buffer.buffer, buffer.byteOffset, buffer.byteLength).getUint16(
        18,
        true,
      ),
    };
  }
  if (buffer.length >= 64 && buffer[0] === 0x4d && buffer[1] === 0x5a) {
    const view = new DataView(buffer.buffer, buffer.byteOffset, buffer.byteLength);
    const peOffset = view.getUint32(0x3c, true);
    if (peOffset + 6 > buffer.length) throw new Error("Invalid PE offset");
    if (
      buffer[peOffset] !== 0x50 ||
      buffer[peOffset + 1] !== 0x45 ||
      buffer[peOffset + 2] !== 0 ||
      buffer[peOffset + 3] !== 0
    ) {
      throw new Error("Invalid PE signature");
    }
    return { format: "PE", machine: view.getUint16(peOffset + 4, true) };
  }
  throw new Error("Executable is neither PE nor ELF");
}

export function verifyExecutable(binaryPath: string, target: ReleaseTarget): void {
  const bytes = readFileSync(binaryPath);
  const header = inspectExecutableHeader(bytes);
  const expectedFormat = target.os === "windows" ? "PE" : "ELF";
  if (header.format !== expectedFormat || header.machine !== target.expectedMachine) {
    throw new Error(
      `${target.id} executable mismatch: ${header.format}/${header.machine}, expected ${expectedFormat}/${target.expectedMachine}`,
    );
  }
  if (!bytes.includes(Buffer.from(target.expectedNativeMarker, "utf8"))) {
    throw new Error(`${target.id} does not embed ${target.expectedNativeMarker}`);
  }
}

function exactKeys(
  record: Record<string, unknown>,
  expected: readonly string[],
  label: string,
): void {
  const actual = Object.keys(record).sort();
  const required = [...expected].sort();
  if (actual.length !== required.length || actual.some((key, index) => key !== required[index])) {
    throw new Error(`${label} fields mismatch: ${actual.join(", ")}`);
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function recordValue(value: unknown, label: string): Record<string, unknown> {
  if (!isRecord(value)) {
    throw new Error(`${label} must be an object`);
  }
  return value;
}

function stringRecordValue(value: unknown, label: string): Readonly<Record<string, string>> {
  const record = recordValue(value, label);
  const strings: Record<string, string> = {};
  for (const [key, candidate] of Object.entries(record)) {
    if (typeof candidate !== "string" || candidate === "") {
      throw new Error(`${label}.${key} must be a non-empty string`);
    }
    strings[key] = candidate;
  }
  return strings;
}

function unknownArrayValue(value: unknown, label: string): readonly unknown[] {
  if (!Array.isArray(value)) throw new Error(`${label} must be an array`);
  return value;
}

function stringArrayValue(value: unknown, label: string): readonly string[] {
  const values = unknownArrayValue(value, label);
  if (!values.every((candidate): candidate is string => typeof candidate === "string")) {
    throw new Error(`${label} must contain only strings`);
  }
  return values;
}

/** Node's Readable async iterator is typed as `any`; narrow each runtime chunk at this boundary. */
async function* fileChunks(path: string): AsyncGenerator<Uint8Array> {
  const stream = createReadStream(path) as AsyncIterable<unknown>;
  for await (const chunk of stream) {
    if (!(chunk instanceof Uint8Array)) throw new Error(`${path} emitted a non-binary chunk`);
    yield chunk;
  }
}

export function expectedNativeVerification(
  target: ReleaseTarget,
): ReleaseManifest["nativeVerification"] {
  return target.os === "windows"
    ? {
        status: "verified",
        checks: [
          "PE x86_64 header",
          "embedded OpenTUI DLL",
          "--help",
          "--version",
          "OpenTUI smoke render",
          "third-party licenses",
        ],
      }
    : {
        status: "native-runtime-unverified",
        checks: [
          "ELF architecture header",
          "embedded OpenTUI shared object",
          "archive safety",
          "Unix archive permissions",
          "third-party licenses",
        ],
      };
}

export function validateReleaseGitState(
  git: { commit: string; dirty: boolean },
  allowDevelopment = false,
): void {
  if (!allowDevelopment && (!/^[a-f0-9]{40}$/.test(git.commit) || git.dirty)) {
    throw new Error(
      `Release requires a clean committed tree; set ${RELEASE_DEVELOPMENT_OVERRIDE}=1 only for non-promotable development packages`,
    );
  }
  if (allowDevelopment && git.commit !== "uncommitted" && !/^[a-f0-9]{40}$/.test(git.commit)) {
    throw new Error(`Invalid development commit identity: ${git.commit}`);
  }
}

export function validateManifest(
  value: unknown,
  target: ReleaseTarget,
  options: { allowDevelopment?: boolean } = {},
): asserts value is ReleaseManifest {
  const manifest = recordValue(value, "manifest");
  exactKeys(
    manifest,
    [
      "schemaVersion",
      "product",
      "binary",
      "version",
      "commit",
      "dirty",
      "builtAt",
      "target",
      "toolchain",
      "nativeVerification",
    ],
    "manifest",
  );
  if (
    manifest["schemaVersion"] !== 1 ||
    manifest["product"] !== "Kunpeng DevKit AI" ||
    manifest["binary"] !== "devkitai" ||
    manifest["version"] !== RELEASE_VERSION
  ) {
    throw new Error(`Manifest identity mismatch for ${target.id}`);
  }
  const commit = manifest["commit"];
  const dirty = manifest["dirty"];
  if (typeof commit !== "string" || typeof dirty !== "boolean") {
    throw new Error("Manifest commit metadata is invalid");
  }
  validateReleaseGitState({ commit, dirty }, options.allowDevelopment === true);
  const builtAt = manifest["builtAt"];
  if (
    typeof builtAt !== "string" ||
    !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(builtAt) ||
    Number.isNaN(Date.parse(builtAt)) ||
    new Date(builtAt).toISOString() !== builtAt
  ) {
    throw new Error("Manifest builtAt must be an ISO-8601 UTC instant");
  }

  const manifestTarget = recordValue(manifest["target"], "manifest.target");
  exactKeys(manifestTarget, ["id", "os", "arch", "baseline", "bunTarget"], "manifest.target");
  if (
    manifestTarget["id"] !== target.id ||
    manifestTarget["os"] !== target.os ||
    manifestTarget["arch"] !== target.arch ||
    manifestTarget["baseline"] !== target.baseline ||
    manifestTarget["bunTarget"] !== target.bunTarget
  ) {
    throw new Error(`Manifest target mismatch for ${target.id}`);
  }

  const toolchain = recordValue(manifest["toolchain"], "manifest.toolchain");
  exactKeys(
    toolchain,
    ["bun", "typescript", "react", "opentuiCore", "opentuiReact"],
    "manifest.toolchain",
  );
  const expectedToolchain = {
    bun: BUN_VERSION,
    typescript: requiredVersion(PACKAGE_JSON.devDependencies["typescript"], "typescript"),
    react: requiredVersion(PACKAGE_JSON.dependencies["react"], "react"),
    opentuiCore: requiredVersion(PACKAGE_JSON.dependencies["@opentui/core"], "@opentui/core"),
    opentuiReact: requiredVersion(PACKAGE_JSON.dependencies["@opentui/react"], "@opentui/react"),
  };
  for (const [key, expected] of Object.entries(expectedToolchain)) {
    if (toolchain[key] !== expected) throw new Error(`Manifest toolchain mismatch: ${key}`);
  }

  const verification = recordValue(manifest["nativeVerification"], "manifest.nativeVerification");
  exactKeys(verification, ["status", "checks"], "manifest.nativeVerification");
  const expectedVerification = expectedNativeVerification(target);
  const checks = stringArrayValue(verification["checks"], "manifest.nativeVerification.checks");
  if (
    verification["status"] !== expectedVerification.status ||
    checks.length !== expectedVerification.checks.length ||
    checks.some((check, index) => check !== expectedVerification.checks[index])
  ) {
    throw new Error(`Manifest verification mismatch for ${target.id}`);
  }
}

export async function sha256File(path: string): Promise<string> {
  const hash = createHash("sha256");
  for await (const chunk of fileChunks(path)) hash.update(chunk);
  return hash.digest("hex");
}

export async function run(
  command: readonly string[],
  options: { cwd?: string; env?: Record<string, string | undefined>; capture?: boolean } = {},
): Promise<string> {
  const child = Bun.spawn([...command], {
    cwd: options.cwd ?? PROJECT_ROOT,
    env: { ...process.env, ...options.env },
    stdout: options.capture ? "pipe" : "inherit",
    stderr: options.capture ? "pipe" : "inherit",
  });
  const [exitCode, stdout, stderr] = await Promise.all([
    child.exited,
    options.capture ? new Response(child.stdout).text() : Promise.resolve(""),
    options.capture ? new Response(child.stderr).text() : Promise.resolve(""),
  ]);
  if (exitCode !== 0) {
    throw new Error(`Command failed (${exitCode}): ${command.join(" ")}\n${stderr}`);
  }
  return stdout.trim();
}

export async function gitMetadata(): Promise<{ commit: string; dirty: boolean }> {
  let commit = "uncommitted";
  try {
    commit = await run(["git", "rev-parse", "HEAD"], { capture: true });
  } catch {
    // A first local build is valid before the repository has its initial commit.
  }
  const status = await run(["git", "status", "--porcelain"], { capture: true });
  return { commit, dirty: status.length > 0 };
}

export function createManifest(
  target: ReleaseTarget,
  git: { commit: string; dirty: boolean },
): ReleaseManifest {
  return {
    schemaVersion: 1,
    product: "Kunpeng DevKit AI",
    binary: "devkitai",
    version: RELEASE_VERSION,
    commit: git.commit,
    dirty: git.dirty,
    builtAt: new Date().toISOString(),
    target: {
      id: target.id,
      os: target.os,
      arch: target.arch,
      baseline: target.baseline,
      bunTarget: target.bunTarget,
    },
    toolchain: {
      bun: requiredVersion(BUN_VERSION, "bun"),
      typescript: requiredVersion(PACKAGE_JSON.devDependencies["typescript"], "typescript"),
      react: requiredVersion(PACKAGE_JSON.dependencies["react"], "react"),
      opentuiCore: requiredVersion(PACKAGE_JSON.dependencies["@opentui/core"], "@opentui/core"),
      opentuiReact: requiredVersion(PACKAGE_JSON.dependencies["@opentui/react"], "@opentui/react"),
    },
    nativeVerification: {
      ...expectedNativeVerification(target),
    },
  };
}

export function copyProjectForBuild(stage: string): void {
  for (const file of ["package.json", "bun.lock", "tsconfig.base.json", "tsconfig.build.json"]) {
    cpSync(join(PROJECT_ROOT, file), join(stage, file));
  }
  cpSync(join(PROJECT_ROOT, "src"), join(stage, "src"), { recursive: true });
}

export function writeJson(path: string, value: unknown): void {
  const serialized = JSON.stringify(value, null, 2);
  if (serialized === undefined) throw new Error(`${path} cannot be represented as JSON`);
  writeFileSync(path, `${serialized}\n`, "utf8");
}

export function parseChecksumFile(contents: string): Map<string, string> {
  const checksums = new Map<string, string>();
  for (const line of contents.split(/\r?\n/)) {
    if (line.trim() === "") continue;
    const match = /^([a-f0-9]{64}) {2}(.+)$/.exec(line);
    if (!match) throw new Error(`Invalid SHA256SUMS line: ${line}`);
    const [, hash, file] = match;
    if (hash === undefined || file === undefined)
      throw new Error(`Invalid SHA256SUMS line: ${line}`);
    checksums.set(file, hash);
  }
  return checksums;
}

const LICENSE_FILE_PATTERN = /^(license|licence|notice|patents|copying)(\.|-|$)/i;

function installedPackageDirectories(nodeModules: string): string[] {
  const packages: string[] = [];
  const visitNodeModules = (directory: string): void => {
    if (!existsSync(directory)) return;
    for (const entry of readdirSync(directory, { withFileTypes: true })) {
      if (!entry.isDirectory() || entry.name.startsWith(".")) continue;
      const candidate = join(directory, entry.name);
      if (entry.name.startsWith("@")) {
        for (const scopedEntry of readdirSync(candidate, { withFileTypes: true })) {
          if (scopedEntry.isDirectory()) visitPackage(join(candidate, scopedEntry.name));
        }
      } else {
        visitPackage(candidate);
      }
    }
  };
  const visitPackage = (directory: string): void => {
    const manifest = join(directory, "package.json");
    if (!existsSync(manifest)) return;
    packages.push(directory);
    visitNodeModules(join(directory, "node_modules"));
  };
  visitNodeModules(nodeModules);
  return packages;
}

export function licenseDirectoryName(name: string, version: string): string {
  return `${name.replaceAll("/", "__")}@${version}`;
}

export function collectThirdPartyLicenses(
  buildStage: string,
  payload: string,
  target: ReleaseTarget,
): ThirdPartyLicenseIndex {
  const licensesRoot = join(payload, "licenses");
  mkdirSync(licensesRoot, { recursive: true });
  const indexed = new Map<string, ThirdPartyLicenseEntry>();

  for (const packageDirectory of installedPackageDirectories(join(buildStage, "node_modules"))) {
    const packageManifest = recordValue(
      parseJsonValue(
        readFileSync(join(packageDirectory, "package.json"), "utf8"),
        `${packageDirectory}/package.json`,
      ),
      `${packageDirectory}/package.json`,
    );
    const name = packageManifest["name"];
    const version = packageManifest["version"];
    const license = packageManifest["license"];
    if (typeof name !== "string" || typeof version !== "string") {
      throw new Error(`Installed package has no name/version: ${packageDirectory}`);
    }
    if (typeof license !== "string" || license.length === 0) {
      throw new Error(`Installed package has no declared license: ${name}`);
    }
    const key = `${name}@${version}`;
    if (indexed.has(key)) continue;
    const bundledFiles = readdirSync(packageDirectory, { withFileTypes: true })
      .filter((entry) => entry.isFile() && LICENSE_FILE_PATTERN.test(entry.name))
      .map((entry) => ({ path: join(packageDirectory, entry.name), name: entry.name }));
    const fallbackDirectory = join(
      PROJECT_ROOT,
      "packaging",
      "licenses",
      "npm-overrides",
      licenseDirectoryName(name, version),
    );
    const sourceFiles =
      bundledFiles.length > 0
        ? bundledFiles
        : existsSync(fallbackDirectory)
          ? readdirSync(fallbackDirectory, { withFileTypes: true })
              .filter((entry) => entry.isFile() && LICENSE_FILE_PATTERN.test(entry.name))
              .map((entry) => ({ path: join(fallbackDirectory, entry.name), name: entry.name }))
          : [];
    if (sourceFiles.length === 0) {
      throw new Error(`No complete license text is available for ${key}`);
    }
    const destinationName = licenseDirectoryName(name, version);
    const destination = join(licensesRoot, destinationName);
    mkdirSync(destination, { recursive: true });
    const files = sourceFiles
      .sort((left, right) => left.name.localeCompare(right.name))
      .map((source) => {
        cpSync(source.path, join(destination, source.name));
        return `licenses/${destinationName}/${source.name}`;
      });
    indexed.set(key, {
      name,
      version,
      declaredLicense: license,
      files,
    });
  }

  const bunSource = join(PROJECT_ROOT, "packaging", "licenses", `bun-${BUN_VERSION}`);
  if (!existsSync(bunSource))
    throw new Error(`Missing source-controlled Bun ${BUN_VERSION} notices`);
  const bunDestinationName = licenseDirectoryName("bun-runtime", BUN_VERSION);
  const bunDestination = join(licensesRoot, bunDestinationName);
  mkdirSync(bunDestination, { recursive: true });
  const bunFiles = readdirSync(bunSource, { withFileTypes: true })
    .filter((entry) => entry.isFile() && LICENSE_FILE_PATTERN.test(entry.name))
    .sort((left, right) => left.name.localeCompare(right.name))
    .map((entry) => {
      cpSync(join(bunSource, entry.name), join(bunDestination, entry.name));
      return `licenses/${bunDestinationName}/${entry.name}`;
    });
  if (bunFiles.length === 0) throw new Error(`Bun ${BUN_VERSION} notices are empty`);
  indexed.set(`bun-runtime@${BUN_VERSION}`, {
    name: "bun-runtime",
    version: BUN_VERSION,
    declaredLicense: "MIT and bundled upstream notices",
    files: bunFiles,
  });

  const entries = [...indexed.values()].sort((left, right) =>
    `${left.name}@${left.version}`.localeCompare(`${right.name}@${right.version}`),
  );
  const native = entries.find(
    (entry) => entry.name === target.nativePackage && entry.version === "0.5.1",
  );
  if (native === undefined)
    throw new Error(`Missing native license entry for ${target.nativePackage}`);
  const nativeNames = new Set(native.files.map((path) => basename(path)));
  for (const file of REQUIRED_NATIVE_LICENSE_FILES) {
    if (!nativeNames.has(file)) throw new Error(`${target.nativePackage} is missing ${file}`);
  }
  const index: ThirdPartyLicenseIndex = { schemaVersion: 1, target: target.id, packages: entries };
  writeJson(join(licensesRoot, "index.json"), index);
  return index;
}

export function validateThirdPartyLicenseIndex(
  value: unknown,
  target: ReleaseTarget,
  archiveEntries: ReadonlySet<string>,
  payloadName: string,
): asserts value is ThirdPartyLicenseIndex {
  const index = recordValue(value, "licenses/index.json");
  exactKeys(index, ["schemaVersion", "target", "packages"], "licenses/index.json");
  if (index["schemaVersion"] !== 1 || index["target"] !== target.id) {
    throw new Error(`License index identity mismatch for ${target.id}`);
  }
  const packages = unknownArrayValue(index["packages"], "licenses/index.json packages");
  const seen = new Set<string>();
  const validatedEntries: ThirdPartyLicenseEntry[] = [];
  for (const candidate of packages) {
    const entry = recordValue(candidate, "license package");
    exactKeys(entry, ["name", "version", "declaredLicense", "files"], "license package");
    const name = entry["name"];
    const version = entry["version"];
    const declaredLicense = entry["declaredLicense"];
    const files = stringArrayValue(entry["files"], "license package files");
    if (
      typeof name !== "string" ||
      typeof version !== "string" ||
      typeof declaredLicense !== "string" ||
      files.length === 0
    ) {
      throw new Error("Invalid license package record");
    }
    const key = `${name}@${version}`;
    if (seen.has(key)) throw new Error(`Duplicate license package: ${key}`);
    seen.add(key);
    for (const file of files) {
      if (!file.startsWith("licenses/")) {
        throw new Error(`Unsafe license path for ${key}`);
      }
      if (!archiveEntries.has(`${payloadName}/${file}`)) {
        throw new Error(`Archive is missing license text: ${file}`);
      }
    }
    validatedEntries.push({ name, version, declaredLicense, files });
  }
  if (!seen.has(`bun-runtime@${BUN_VERSION}`)) throw new Error("Bun runtime notice is missing");
  const nativeKey = `${target.nativePackage}@0.5.1`;
  if (!seen.has(nativeKey)) throw new Error(`Native OpenTUI notice is missing: ${nativeKey}`);
  const native = validatedEntries.find((entry) => `${entry.name}@${entry.version}` === nativeKey);
  const nativeFiles = new Set(native?.files.map((path) => basename(path)) ?? []);
  for (const file of REQUIRED_NATIVE_LICENSE_FILES) {
    if (!nativeFiles.has(file)) throw new Error(`${nativeKey} is missing ${file}`);
  }
}

function writeTarString(header: Buffer, offset: number, length: number, value: string): void {
  const bytes = Buffer.from(value, "utf8");
  if (bytes.length > length) throw new Error(`Tar header field is too long: ${value}`);
  bytes.copy(header, offset);
}

function writeTarOctal(header: Buffer, offset: number, length: number, value: number): void {
  const octal = value.toString(8).padStart(length - 1, "0");
  if (octal.length >= length) throw new Error(`Tar numeric field is too large: ${value}`);
  writeTarString(header, offset, length, `${octal}\0`);
}

function splitTarPath(path: string): { name: string; prefix: string } {
  if (Buffer.byteLength(path) <= 100) return { name: path, prefix: "" };
  const trailingSlash = path.endsWith("/");
  const candidate = trailingSlash ? path.slice(0, -1) : path;
  for (
    let separator = candidate.lastIndexOf("/");
    separator > 0;
    separator = candidate.lastIndexOf("/", separator - 1)
  ) {
    const prefix = candidate.slice(0, separator);
    const name = `${candidate.slice(separator + 1)}${trailingSlash ? "/" : ""}`;
    if (Buffer.byteLength(prefix) <= 155 && Buffer.byteLength(name) <= 100) return { name, prefix };
  }
  throw new Error(`Tar path exceeds ustar limits: ${path}`);
}

function createTarHeader(
  path: string,
  type: "directory" | "file",
  size: number,
  mode: number,
  modifiedSeconds: number,
): Buffer {
  // These byte offsets are fixed by the POSIX ustar header; writing them directly keeps
  // Linux permissions deterministic even when packages are produced on Windows.
  const header = Buffer.alloc(512);
  const normalized = type === "directory" && !path.endsWith("/") ? `${path}/` : path;
  const { name, prefix } = splitTarPath(normalized);
  writeTarString(header, 0, 100, name);
  writeTarOctal(header, 100, 8, mode);
  writeTarOctal(header, 108, 8, 0);
  writeTarOctal(header, 116, 8, 0);
  writeTarOctal(header, 124, 12, size);
  writeTarOctal(header, 136, 12, modifiedSeconds);
  header.fill(0x20, 148, 156);
  writeTarString(header, 156, 1, type === "directory" ? "5" : "0");
  writeTarString(header, 257, 6, "ustar\0");
  writeTarString(header, 263, 2, "00");
  writeTarString(header, 265, 32, "root");
  writeTarString(header, 297, 32, "root");
  writeTarString(header, 345, 155, prefix);
  let checksum = 0;
  for (const byte of header) checksum += byte;
  writeTarString(header, 148, 8, `${checksum.toString(8).padStart(6, "0")}\0 `);
  return header;
}

function tarPayloadEntries(
  payload: string,
  payloadName: string,
): Array<{
  source: string;
  path: string;
  type: "directory" | "file";
  size: number;
  mode: number;
  modifiedSeconds: number;
}> {
  const results: Array<{
    source: string;
    path: string;
    type: "directory" | "file";
    size: number;
    mode: number;
    modifiedSeconds: number;
  }> = [];
  const visit = (source: string, archivePath: string): void => {
    const stat = statSync(source);
    if (stat.isDirectory()) {
      results.push({
        source,
        path: archivePath,
        type: "directory",
        size: 0,
        mode: 0o755,
        modifiedSeconds: Math.floor(stat.mtimeMs / 1000),
      });
      for (const child of readdirSync(source).sort())
        visit(join(source, child), `${archivePath}/${child}`);
      return;
    }
    if (!stat.isFile())
      throw new Error(`Release payload may contain only files/directories: ${source}`);
    const isBinary = dirname(source) === payload && basename(source) === "devkitai";
    results.push({
      source,
      path: archivePath,
      type: "file",
      size: stat.size,
      mode: isBinary ? 0o755 : 0o644,
      modifiedSeconds: Math.floor(stat.mtimeMs / 1000),
    });
  };
  visit(payload, payloadName);
  return results;
}

export async function writeLinuxTarGz(
  archivePath: string,
  payload: string,
  payloadName: string,
): Promise<void> {
  const output = createWriteStream(archivePath);
  const gzip = createGzip({ level: 9 });
  const completion = pipeline(gzip, output);
  const write = async (chunk: Uint8Array): Promise<void> => {
    if (!gzip.write(chunk)) {
      await new Promise<void>((resolve) => gzip.once("drain", resolve));
    }
  };
  for (const entry of tarPayloadEntries(payload, payloadName)) {
    await write(
      createTarHeader(entry.path, entry.type, entry.size, entry.mode, entry.modifiedSeconds),
    );
    if (entry.type === "file") {
      for await (const chunk of fileChunks(entry.source)) await write(chunk);
      const padding = (512 - (entry.size % 512)) % 512;
      if (padding > 0) await write(Buffer.alloc(padding));
    }
  }
  await write(Buffer.alloc(1024));
  gzip.end();
  await completion;
}

function permissionBits(token: string): number {
  if (!/^[d-][rwx-]{9}$/.test(token)) throw new Error(`Unsupported tar permission token: ${token}`);
  let mode = 0;
  const bitValues = [0o400, 0o200, 0o100, 0o040, 0o020, 0o010, 0o004, 0o002, 0o001];
  for (let index = 1; index < token.length; index += 1) {
    if (token[index] !== "-") mode |= bitValues[index - 1] ?? 0;
  }
  return mode;
}

export function parseTarVerboseMetadata(output: string): ArchiveMetadataEntry[] {
  return output
    .split(/\r?\n/)
    .filter((line) => line.trim().length > 0)
    .map((line) => {
      const fields = line.trim().split(/\s+/);
      const permissions = fields[0];
      const path = fields.at(-1)?.replaceAll("\\", "/").replace(/\/$/, "");
      if (permissions === undefined || path === undefined)
        throw new Error(`Invalid tar listing: ${line}`);
      return {
        path,
        type: permissions.startsWith("d") ? "directory" : "file",
        mode: permissionBits(permissions),
      };
    });
}

export function validateLinuxArchiveModes(
  metadata: readonly ArchiveMetadataEntry[],
  payloadName: string,
): void {
  const entries = new Map(metadata.map((entry) => [entry.path, entry]));
  const root = entries.get(payloadName);
  if (root?.type !== "directory" || root.mode !== 0o755) {
    throw new Error(`Linux payload directory must be 0755: ${payloadName}`);
  }
  const binaryPath = `${payloadName}/devkitai`;
  const binary = entries.get(binaryPath);
  if (binary?.type !== "file" || binary.mode !== 0o755 || (binary.mode & 0o111) === 0) {
    throw new Error(`Linux executable must be 0755: ${binaryPath}`);
  }
  for (const entry of metadata) {
    if (entry.path === binaryPath) continue;
    if (entry.type === "directory" && entry.mode !== 0o755) {
      throw new Error(`Linux archive directory must be 0755: ${entry.path}`);
    }
    if (entry.type === "file" && entry.mode !== 0o644) {
      throw new Error(`Linux archive document must be non-executable 0644: ${entry.path}`);
    }
  }
}

export function packageFiles(payload: string): void {
  cpSync(join(PROJECT_ROOT, "packaging", "README.release.md"), join(payload, "README.md"));
  cpSync(join(PROJECT_ROOT, "THIRD_PARTY_NOTICES.md"), join(payload, "NOTICE.md"));
  cpSync(join(PROJECT_ROOT, "packaging", "LICENSE.txt"), join(payload, "LICENSE.txt"));
}

export function targetByArchive(path: string): ReleaseTarget {
  const file = basename(path);
  const target = RELEASE_TARGETS.find((candidate) => file === artifactFileName(candidate));
  if (!target) throw new Error(`Unexpected artifact: ${file}`);
  return target;
}
