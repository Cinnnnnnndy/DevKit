import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import {
  ARTIFACTS_DIR,
  artifactBaseName,
  artifactFileName,
  BUN_VERSION,
  collectThirdPartyLicenses,
  copyProjectForBuild,
  createManifest,
  gitMetadata,
  PROJECT_ROOT,
  packageFiles,
  RELEASE_TARGETS,
  RELEASE_DEVELOPMENT_OVERRIDE,
  RELEASE_VERSION,
  RELEASE_WORK_DIR,
  resetGeneratedDirectory,
  parseJsonValue,
  run,
  sha256File,
  validateReleaseGitState,
  verifyExecutable,
  writeLinuxTarGz,
  writeJson,
} from "./release-lib.js";

async function buildTarget(
  target: (typeof RELEASE_TARGETS)[number],
  git: { commit: string; dirty: boolean },
): Promise<string> {
  const targetWork = join(RELEASE_WORK_DIR, target.id);
  resetGeneratedDirectory(targetWork, RELEASE_WORK_DIR);

  const buildStage = join(targetWork, "build");
  const runtimeStage = join(targetWork, "runtime");
  mkdirSync(buildStage, { recursive: true });
  mkdirSync(runtimeStage, { recursive: true });
  copyProjectForBuild(buildStage);
  copyProjectForBuild(runtimeStage);

  console.log(`\n[${target.id}] Installing target production dependencies`);
  await run(
    [
      "bun",
      "install",
      "--production",
      "--frozen-lockfile",
      "--os",
      target.installOs,
      "--cpu",
      target.cpu,
    ],
    { cwd: buildStage },
  );

  console.log(`[${target.id}] Installing pinned Bun ${BUN_VERSION} runtime`);
  await run(
    [
      "bun",
      "install",
      "--frozen-lockfile",
      "--ignore-scripts",
      "--os",
      target.installOs,
      "--cpu",
      target.cpu,
    ],
    { cwd: runtimeStage },
  );

  const runtimePackagePath = join(
    runtimeStage,
    "node_modules",
    ...target.runtimePackage.split("/"),
  );
  const runtimePackageJson = parseJsonValue(
    await Bun.file(join(runtimePackagePath, "package.json")).text(),
    `${target.runtimePackage}/package.json`,
  );
  const runtimeVersion =
    typeof runtimePackageJson === "object" &&
    runtimePackageJson !== null &&
    !Array.isArray(runtimePackageJson) &&
    "version" in runtimePackageJson
      ? runtimePackageJson.version
      : undefined;
  if (runtimeVersion !== BUN_VERSION) {
    throw new Error(
      `${target.runtimePackage} is ${String(runtimeVersion)}, expected ${BUN_VERSION}`,
    );
  }
  const runtimeExecutable = join(runtimePackagePath, target.runtimeExecutable);
  if (!existsSync(runtimeExecutable))
    throw new Error(`Missing target Bun runtime: ${runtimeExecutable}`);

  const payloadName = artifactBaseName(target);
  const payload = join(targetWork, payloadName);
  mkdirSync(payload, { recursive: true });
  const binaryPath = join(payload, target.binaryName);
  const buildArguments = [
    "bun",
    "build",
    "--compile",
    `--target=${target.bunTarget}`,
    `--compile-executable-path=${runtimeExecutable}`,
    "--no-compile-autoload-dotenv",
    "--no-compile-autoload-bunfig",
    "--no-compile-autoload-package-json",
    "--minify",
    "--env=DEVKITAI_VERSION*",
    `--outfile=${binaryPath}`,
  ];
  if (target.os === "windows") {
    buildArguments.push(
      "--windows-title=Kunpeng DevKit AI",
      `--windows-version=${RELEASE_VERSION}.0`,
      "--windows-description=Kunpeng DevKit AI native terminal workspace",
    );
  }
  buildArguments.push("src/index.tsx");

  console.log(`[${target.id}] Compiling ${target.bunTarget}`);
  await run(buildArguments, {
    cwd: buildStage,
    env: { DEVKITAI_VERSION: RELEASE_VERSION },
  });
  verifyExecutable(binaryPath, target);

  writeJson(join(payload, "manifest.json"), createManifest(target, git));
  packageFiles(payload);
  collectThirdPartyLicenses(buildStage, payload, target);

  if (target.os === "windows") {
    const version = await run([binaryPath, "--version"], { capture: true });
    const help = await run([binaryPath, "--help"], { capture: true });
    const smoke = await run([binaryPath, "--smoke-render"], { capture: true });
    if (
      version !== `devkitai ${RELEASE_VERSION}` ||
      !help.includes("Usage: devkitai") ||
      !smoke.includes("devkitai smoke-render ok")
    ) {
      throw new Error(`Windows native CLI smoke failed: ${version}`);
    }
  }

  mkdirSync(ARTIFACTS_DIR, { recursive: true });
  const archivePath = join(ARTIFACTS_DIR, artifactFileName(target));
  console.log(`[${target.id}] Archiving ${artifactFileName(target)}`);
  if (target.archiveExtension === ".zip") {
    await run(["tar", "-a", "-cf", archivePath, "-C", targetWork, payloadName], {
      cwd: PROJECT_ROOT,
    });
  } else {
    await writeLinuxTarGz(archivePath, payload, payloadName);
  }
  return archivePath;
}

const releaseGit = await gitMetadata();
const allowDevelopment = process.env[RELEASE_DEVELOPMENT_OVERRIDE] === "1";
validateReleaseGitState(releaseGit, allowDevelopment);
if (allowDevelopment) {
  console.warn(
    `WARNING: ${RELEASE_DEVELOPMENT_OVERRIDE}=1 creates non-promotable development packages`,
  );
}
resetGeneratedDirectory(RELEASE_WORK_DIR, join(PROJECT_ROOT, ".codex_tmp"));
if (existsSync(ARTIFACTS_DIR)) {
  resetGeneratedDirectory(ARTIFACTS_DIR, join(PROJECT_ROOT, "artifacts"));
} else {
  mkdirSync(ARTIFACTS_DIR, { recursive: true });
}

const builtArtifacts: string[] = [];
for (const target of RELEASE_TARGETS) builtArtifacts.push(await buildTarget(target, releaseGit));

const checksumLines: string[] = [];
for (const artifact of builtArtifacts) {
  checksumLines.push(`${await sha256File(artifact)}  ${artifact.split(/[\\/]/).at(-1)}`);
}
writeFileSync(join(ARTIFACTS_DIR, "SHA256SUMS"), `${checksumLines.join("\n")}\n`, "utf8");
console.log(`\nCreated ${builtArtifacts.length} release artifacts in ${ARTIFACTS_DIR}`);
