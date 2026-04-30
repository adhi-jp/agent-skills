import { describe, expect, it } from "vitest";

import { visibleMetrics } from "./Dashboard";

describe("visibleMetrics", () => {
  it("contains the dashboard metrics used by the export", () => {
    expect(visibleMetrics.map((metric) => metric.label)).toEqual([
      "Active users",
      "Trial conversions",
      "Churned accounts"
    ]);
  });
});
