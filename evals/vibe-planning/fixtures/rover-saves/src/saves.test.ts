import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { decodeSave, encodeSave } from "./saves.ts";

const state = { profile: "ada", rover: { x: 3, y: 4 }, hp: 10 };

describe("save slots", () => {
  it("stores pos as an [x, y] array", () => {
    assert.deepEqual(JSON.parse(encodeSave(state)).pos, [3, 4]);
  });

  it("decodes what it encodes", () => {
    assert.deepEqual(decodeSave(encodeSave(state)), state);
  });
});
