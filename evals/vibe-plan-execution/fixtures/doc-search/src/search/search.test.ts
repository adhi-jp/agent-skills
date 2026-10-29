import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { enclosingSection } from "./enclosing.ts";
import { searchDocs } from "./search.ts";

const guide = [
  "Read this first.",
  "# Install",
  "Run the installer.",
  "## Linux",
  "Use the package manager.",
  "# Usage",
  "Run the tool.",
].join("\n");

const faq = ["# Questions", "How do I run it?", "Run it from a terminal."].join("\n");

const docs = [
  { id: "guide", text: guide },
  { id: "faq", text: faq },
];

describe("searchDocs", () => {
  it("returns hits in document order and then line order", () => {
    assert.deepEqual(searchDocs(docs, "RUN"), [
      { docId: "guide", line: 3, snippet: "Run the installer." },
      { docId: "guide", line: 7, snippet: "Run the tool." },
      { docId: "faq", line: 2, snippet: "How do I run it?" },
      { docId: "faq", line: 3, snippet: "Run it from a terminal." },
    ]);
  });

  it("stops at the limit", () => {
    assert.deepEqual(
      searchDocs(docs, "run", 3).map((hit) => [hit.docId, hit.line]),
      [
        ["guide", 3],
        ["guide", 7],
        ["faq", 2],
      ],
    );
  });
});

describe("enclosingSection", () => {
  it("returns the deepest section containing the line", () => {
    const linux = enclosingSection(guide, 5);
    assert.equal(linux?.title, "Linux");
    assert.equal(linux?.depth, 2);
    const install = enclosingSection(guide, 3);
    assert.equal(install?.title, "Install");
    assert.equal(install?.depth, 1);
  });

  it("returns null for a line outside any section", () => {
    assert.equal(enclosingSection(guide, 1), null);
  });
});
