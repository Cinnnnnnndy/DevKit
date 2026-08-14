import { describe, expect, it } from "vitest";
import * as ui from "../../../src/components/ui/index.js";
import {
  COMPONENT_CONTRACTS,
  COMPONENT_NAMES,
  COMPONENT_REFERENCE,
} from "../../../src/components/ui/index.js";
import { COMPONENT_GALLERY_ITEMS } from "../../../src/features/component-gallery/index.js";
import { PATTERN_REGISTRY } from "../../../src/features/pattern-gallery/index.js";

describe("component and pattern contracts", () => {
  it("exports exactly twenty-two real components with complete metadata", () => {
    expect(COMPONENT_NAMES).toHaveLength(22);
    expect(COMPONENT_GALLERY_ITEMS.map(({ name }) => name)).toEqual(COMPONENT_NAMES);
    for (const name of COMPONENT_NAMES) {
      // biome-ignore lint/performance/noDynamicNamespaceImportAccess: 此边界测试有意验证注册表中的每个键都是真实的公共导出。
      expect(ui[name]).toBeTypeOf("function");
      expect(COMPONENT_CONTRACTS[name].states).toEqual(
        expect.arrayContaining(["loading", "empty", "loaded", "error", "failed", "disabled"]),
      );
      expect(COMPONENT_CONTRACTS[name].keyboardEquivalents.length).toBeGreaterThan(0);
      expect(COMPONENT_CONTRACTS[name].tokens.length).toBeGreaterThan(0);
    }
    expect(COMPONENT_REFERENCE).toBe("web-feasibility-2026-08-13");
  });

  it("locks P01-P26 without extending the product flow", () => {
    expect(PATTERN_REGISTRY).toHaveLength(26);
    expect(PATTERN_REGISTRY.map(({ id }) => id)).toEqual(
      Array.from({ length: 26 }, (_, index) => `P${String(index + 1).padStart(2, "0")}`),
    );
    expect(new Set(PATTERN_REGISTRY.map(({ id }) => id))).toHaveLength(26);
    expect(PATTERN_REGISTRY.every(({ reference }) => reference === COMPONENT_REFERENCE)).toBe(true);
  });
});
