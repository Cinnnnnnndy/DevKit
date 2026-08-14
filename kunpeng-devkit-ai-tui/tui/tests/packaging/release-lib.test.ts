import { execFileSync } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import {
  assertSafeGeneratedPath,
  createManifest,
  inspectExecutableHeader,
  parseTarVerboseMetadata,
  parseChecksumFile,
  recordValue,
  RELEASE_TARGETS,
  validateLinuxArchiveModes,
  validateArchiveEntries,
  validateManifest,
  validateReleaseGitState,
  writeLinuxTarGz,
} from "../../scripts/release-lib";

function setField(record: Record<string, unknown>, field: string, value: unknown): void {
  record[field] = value;
}

function nested(record: Record<string, unknown>, field: string): Record<string, unknown> {
  return recordValue(record[field], `test fixture ${field}`);
}

describe("release package invariants", () => {
  it("locks the three requested targets", () => {
    expect(RELEASE_TARGETS.map((target) => target.id)).toEqual([
      "windows-x64",
      "linux-x86_64",
      "linux-arm64",
    ]);
    expect(RELEASE_TARGETS.map((target) => target.bunTarget)).toEqual([
      "bun-windows-x64-baseline",
      "bun-linux-x64-baseline",
      "bun-linux-arm64",
    ]);
  });

  it("rejects traversal and absolute archive entries", () => {
    expect(() => validateArchiveEntries(["release/devkitai"], "release")).not.toThrow();
    expect(() => validateArchiveEntries(["release/../secret"], "release")).toThrow();
    expect(() => validateArchiveEntries(["C:/secret"], "release")).toThrow();
    expect(() => validateArchiveEntries(["other/devkitai"], "release")).toThrow();
  });

  it("refuses broad generated paths", () => {
    expect(() =>
      assertSafeGeneratedPath("D:/workspace/.codex_tmp/release", "D:/workspace/.codex_tmp"),
    ).not.toThrow();
    expect(() =>
      assertSafeGeneratedPath("D:/workspace/.codex_tmp", "D:/workspace/.codex_tmp"),
    ).toThrow();
    expect(() => assertSafeGeneratedPath("D:/workspace", "D:/workspace/.codex_tmp")).toThrow();
  });

  it("reads ELF and PE machine identifiers", () => {
    const elf = new Uint8Array(64);
    elf.set([0x7f, 0x45, 0x4c, 0x46, 2, 1]);
    elf[18] = 0xb7;
    expect(inspectExecutableHeader(elf)).toEqual({ format: "ELF", machine: 183 });

    const pe = new Uint8Array(128);
    pe.set([0x4d, 0x5a]);
    new DataView(pe.buffer).setUint32(0x3c, 64, true);
    pe.set([0x50, 0x45, 0, 0, 0x64, 0x86], 64);
    expect(inspectExecutableHeader(pe)).toEqual({ format: "PE", machine: 0x8664 });
  });

  it("parses strict SHA256SUMS records", () => {
    const digest = "a".repeat(64);
    expect(parseChecksumFile(`${digest}  artifact.zip\n`).get("artifact.zip")).toBe(digest);
    expect(() => parseChecksumFile(`${digest} artifact.zip\n`)).toThrow();
  });

  it("requires a clean real commit unless the development override is explicit", () => {
    const clean = { commit: "a".repeat(40), dirty: false };
    expect(() => validateReleaseGitState(clean)).not.toThrow();
    expect(() => validateReleaseGitState({ ...clean, dirty: true })).toThrow();
    expect(() => validateReleaseGitState({ commit: "uncommitted", dirty: false })).toThrow();
    expect(() =>
      validateReleaseGitState({ commit: "uncommitted", dirty: true }, true),
    ).not.toThrow();
  });

  it("validates every manifest identity, target, toolchain and verification field", () => {
    const target = RELEASE_TARGETS[0];
    if (target === undefined) throw new Error("Missing release target");
    const valid = createManifest(target, { commit: "a".repeat(40), dirty: false });
    expect(() => validateManifest(valid, target)).not.toThrow();

    const cases: Array<[string, (copy: Record<string, unknown>) => void]> = [
      ["schemaVersion", (copy) => setField(copy, "schemaVersion", 2)],
      ["product", (copy) => setField(copy, "product", "Other")],
      ["binary", (copy) => setField(copy, "binary", "other")],
      ["version", (copy) => setField(copy, "version", "9.9.9")],
      ["commit", (copy) => setField(copy, "commit", "not-a-sha")],
      ["dirty", (copy) => setField(copy, "dirty", true)],
      ["builtAt", (copy) => setField(copy, "builtAt", "yesterday")],
      ["target.id", (copy) => setField(nested(copy, "target"), "id", "linux-x86_64")],
      ["target.os", (copy) => setField(nested(copy, "target"), "os", "linux")],
      ["target.arch", (copy) => setField(nested(copy, "target"), "arch", "arm64")],
      ["target.baseline", (copy) => setField(nested(copy, "target"), "baseline", false)],
      [
        "target.bunTarget",
        (copy) => setField(nested(copy, "target"), "bunTarget", "bun-linux-arm64"),
      ],
      ["toolchain.bun", (copy) => setField(nested(copy, "toolchain"), "bun", "latest")],
      [
        "toolchain.typescript",
        (copy) => setField(nested(copy, "toolchain"), "typescript", "latest"),
      ],
      ["toolchain.react", (copy) => setField(nested(copy, "toolchain"), "react", "latest")],
      [
        "toolchain.opentuiCore",
        (copy) => setField(nested(copy, "toolchain"), "opentuiCore", "latest"),
      ],
      [
        "toolchain.opentuiReact",
        (copy) => setField(nested(copy, "toolchain"), "opentuiReact", "latest"),
      ],
      [
        "nativeVerification.status",
        (copy) =>
          setField(nested(copy, "nativeVerification"), "status", "native-runtime-unverified"),
      ],
      [
        "nativeVerification.checks",
        (copy) => setField(nested(copy, "nativeVerification"), "checks", ["incomplete"]),
      ],
      ["unexpected field", (copy) => setField(copy, "unexpected", true)],
    ];
    for (const [label, mutate] of cases) {
      // Convert the typed manifest into an untrusted JSON-shaped value before corrupting it.
      const invalid = recordValue(structuredClone(valid), "test manifest");
      mutate(invalid);
      expect(() => validateManifest(invalid, target), label).toThrow();
    }
  });

  it("reads and enforces Linux tar permission metadata", () => {
    const listing = [
      "drwxr-xr-x  0 root root 0 Aug 13 12:00 release/",
      "-rwxr-xr-x  0 root root 8 Aug 13 12:00 release/devkitai",
      "-rw-r--r--  0 root root 8 Aug 13 12:00 release/README.md",
      "drwxr-xr-x  0 root root 0 Aug 13 12:00 release/licenses/",
      "-rw-r--r--  0 root root 8 Aug 13 12:00 release/licenses/LICENSE",
    ].join("\n");
    const metadata = parseTarVerboseMetadata(listing);
    expect(metadata.map((entry) => entry.mode)).toEqual([0o755, 0o755, 0o644, 0o755, 0o644]);
    expect(() => validateLinuxArchiveModes(metadata, "release")).not.toThrow();

    const nonExecutable = listing.replace("-rwxr-xr-x", "-rw-r--r--");
    expect(() =>
      validateLinuxArchiveModes(parseTarVerboseMetadata(nonExecutable), "release"),
    ).toThrow();
    const executableDocument = listing.replace(
      "-rw-r--r--  0 root root 8 Aug 13 12:00 release/README.md",
      "-rwxr-xr-x  0 root root 8 Aug 13 12:00 release/README.md",
    );
    expect(() =>
      validateLinuxArchiveModes(parseTarVerboseMetadata(executableDocument), "release"),
    ).toThrow();
  });

  it("writes portable Linux tar metadata without relying on host chmod", async () => {
    const temporary = mkdtempSync(join(tmpdir(), "devkitai-tar-mode-"));
    try {
      const payload = join(temporary, "release");
      mkdirSync(join(payload, "licenses"), { recursive: true });
      writeFileSync(join(payload, "devkitai"), "ELF");
      writeFileSync(join(payload, "README.md"), "read me");
      writeFileSync(join(payload, "licenses", "LICENSE"), "license");
      const archive = join(temporary, "release.tar.gz");
      await writeLinuxTarGz(archive, payload, "release");

      const listing = execFileSync("tar", ["-tvf", archive], { encoding: "utf8" });
      validateLinuxArchiveModes(parseTarVerboseMetadata(listing), "release");
      expect(listing).toContain("-rwxr-xr-x");
      expect(listing).toContain("-rw-r--r--");
    } finally {
      rmSync(temporary, { recursive: true, force: true });
    }
  });
});
