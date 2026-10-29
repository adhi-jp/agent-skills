import { finalizeRecording } from "./recording.ts";

const open: string[] = ["main"];
let exited = false;

/** Opens the window with the given label. */
export function openWindow(label: string): void {
  if (!open.includes(label)) {
    open.push(label);
  }
}

/** Closes the window with the given label. */
export function closeWindow(label: string): void {
  const index = open.indexOf(label);
  if (index === -1) {
    return;
  }
  if (label === "main" && open.length === 1) {
    finalizeRecording();
  }
  open.splice(index, 1);
  if (open.length === 0) {
    exited = true;
  }
}

/** Returns the labels of the open windows. */
export function openWindows(): string[] {
  return [...open];
}

/** Reports whether the process has exited. */
export function processExited(): boolean {
  return exited;
}
