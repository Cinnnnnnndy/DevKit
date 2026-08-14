import { describe, expect, it } from "vitest";
import { createAppError, err, mapResult, ok, unwrapOr } from "../../../src/shared";

describe("Result", () => {
  it("maps successful values without changing errors", () => {
    expect(mapResult(ok(2), (value) => value * 3)).toEqual(ok(6));

    const failure = createAppError("offline", "test.offline", "offline", true);
    expect(mapResult(err(failure), (value: number) => value * 3)).toEqual(err(failure));
  });

  it("unwraps a fallback only for failures", () => {
    expect(unwrapOr(ok("ready"), "fallback")).toBe("ready");
    expect(unwrapOr(err("failed"), "fallback")).toBe("fallback");
  });
});
