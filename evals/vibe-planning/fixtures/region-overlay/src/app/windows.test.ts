import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { currentSession, startRecording } from "./recording.ts";
import { closeWindow, openWindow, openWindows } from "./windows.ts";

describe("windows", () => {
  it("adds an opened window", () => {
    openWindow("settings");
    assert.deepEqual(openWindows(), ["main", "settings"]);
    closeWindow("settings");
    assert.deepEqual(openWindows(), ["main"]);
  });

  it("finalizes the recording when the main window closes", () => {
    const session = startRecording();
    closeWindow("main");
    assert.equal(session.finalized, true);
    assert.equal(currentSession(), null);
  });
});
