// Player profiles, stored as <data dir>/profiles.json since version 0.1.0.
export type Profile = { name: string; color: string };

export function encodeProfiles(profiles: Profile[]): string {
  return JSON.stringify({ profiles }, null, 2);
}

export function decodeProfiles(text: string): Profile[] {
  const file = JSON.parse(text);
  return file.profiles.map((p: Profile) => ({ name: p.name, color: p.color }));
}
