import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { decodeProfiles, encodeProfiles } from "./profiles.ts";

describe("profiles", () => {
  it("decodes a profiles.json written by version 0.1.0", () => {
    const text = '{\n  "profiles": [\n    { "name": "ada", "color": "teal" }\n  ]\n}';
    assert.deepEqual(decodeProfiles(text), [{ name: "ada", color: "teal" }]);
  });

  it("decodes what it encodes", () => {
    const profiles = [{ name: "ada", color: "teal" }];
    assert.deepEqual(decodeProfiles(encodeProfiles(profiles)), profiles);
  });
});
