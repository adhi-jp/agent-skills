import { parseOutline } from "./outline.ts";
import type { OutlineNode } from "./outline.ts";

/** Returns the deepest outline node of `text` whose line range contains `line`, or null. */
export function enclosingSection(text: string, line: number): OutlineNode | null {
  let deepest: OutlineNode | null = null;
  for (const node of parseOutline(text)) {
    const contains = node.startLine <= line && line <= node.endLine;
    if (contains && (deepest === null || node.depth > deepest.depth)) {
      deepest = node;
    }
  }
  return deepest;
}
