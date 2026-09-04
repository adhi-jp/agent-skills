import assert from "node:assert/strict";
import test from "node:test";

import { summarize } from "../src/index.js";

test("summarize renders one widget per line", () => {
  const rendered = summarize([
    { id: 1, name: "alpha" },
    { id: 2, name: "beta" },
  ]);
  assert.equal(rendered, "1: alpha\n2: beta");
});
