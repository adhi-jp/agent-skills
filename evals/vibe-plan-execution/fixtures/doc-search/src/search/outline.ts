export type OutlineNode = {
  title: string;
  depth: number;
  startLine: number;
  endLine: number;
};

const HEADING = /^(#{1,6})\s+(.+)$/;

/**
 * Returns the Markdown headings of `text` in document order. Lines are
 * numbered from 1. A heading's section runs from its own line to the line
 * before the next heading of the same or lower depth, or to the last line.
 */
export function parseOutline(text: string): OutlineNode[] {
  const lines = text.split("\n");
  const nodes: OutlineNode[] = [];
  const unclosed: OutlineNode[] = [];
  lines.forEach((content, index) => {
    const match = HEADING.exec(content);
    if (match === null) {
      return;
    }
    const node: OutlineNode = {
      title: match[2].trim(),
      depth: match[1].length,
      startLine: index + 1,
      endLine: lines.length,
    };
    while (unclosed.length > 0 && unclosed[unclosed.length - 1].depth >= node.depth) {
      const closed = unclosed.pop() as OutlineNode;
      closed.endLine = index;
    }
    unclosed.push(node);
    nodes.push(node);
  });
  return nodes;
}
