import { describe, expect, it } from "vitest";
import {
  createLandingField,
  createLandingFieldFrame,
  landingHash,
  renderLandingField,
  renderLandingWave,
} from "../../../src/components/ui/landing-field.js";

describe("ACTS[0] deterministic landing field", () => {
  it("reproduces the same base density field for a terminal size", () => {
    const first = createLandingField(58, 32);
    const second = createLandingField(58, 32);
    expect(Array.from(first)).toEqual(Array.from(second));
    expect(first).toHaveLength(58 * 32);
    expect(landingHash(17, 9)).toBeCloseTo(0.60038, 5);
    expect(renderLandingField(first, 58, 32)).toBe(renderLandingField(second, 58, 32));
  });

  it("uses a seeded, reproducible wave without changing the base field", () => {
    const field = createLandingField(80, 40);
    const before = Array.from(field);
    const first = renderLandingWave(field, 80, 40, 12);
    const second = renderLandingWave(field, 80, 40, 12);
    expect(first).toEqual(second);
    expect(first.core).not.toBe(renderLandingWave(field, 80, 40, 42).core);
    expect(Array.from(field)).toEqual(before);
  });

  it("returns stable base, halo and core layers", () => {
    const frame = createLandingFieldFrame(24, 12, 7);
    expect(frame).toEqual(createLandingFieldFrame(24, 12, 7));
    expect(frame.base.split("\n")).toHaveLength(12);
    expect(frame.halo.split("\n")).toHaveLength(12);
    expect(frame.core.split("\n")).toHaveLength(12);
  });
});
