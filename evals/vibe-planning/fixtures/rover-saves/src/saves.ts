// Save slots, stored as <data dir>/saves/<slot>.json.
export type Rover = { x: number; y: number };
export type SaveState = { profile: string; rover: Rover; hp: number };

export function encodeSave(state: SaveState): string {
  return JSON.stringify({ profile: state.profile, pos: [state.rover.x, state.rover.y], hp: state.hp });
}

export function decodeSave(text: string): SaveState {
  const file = JSON.parse(text);
  const [x, y] = file.pos;
  return { profile: file.profile, rover: { x, y }, hp: file.hp };
}
