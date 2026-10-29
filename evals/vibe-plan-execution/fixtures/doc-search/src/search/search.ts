export type Doc = {
  id: string;
  text: string;
};

export type SearchHit = {
  docId: string;
  line: number;
  snippet: string;
};

/**
 * Returns the lines of `docs` that contain `query`, ignoring case, in
 * document order and then line order, up to `limit` hits. Lines are
 * numbered from 1.
 */
export function searchDocs(docs: Doc[], query: string, limit = 100): SearchHit[] {
  const needle = query.toLowerCase();
  const hits: SearchHit[] = [];
  for (const doc of docs) {
    const lines = doc.text.split("\n");
    for (let index = 0; index < lines.length; index += 1) {
      if (hits.length >= limit) {
        return hits;
      }
      if (lines[index].toLowerCase().includes(needle)) {
        hits.push({ docId: doc.id, line: index + 1, snippet: lines[index].trim() });
      }
    }
  }
  return hits;
}
