// Release builds replace this environment value from the root package manifest.
export const BUILD_VERSION = process.env["DEVKITAI_VERSION"] ?? "0.1.0-dev";
