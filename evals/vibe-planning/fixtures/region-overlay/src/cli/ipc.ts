import { finalizeRecording, startRecording } from "../app/recording.ts";
import type { RecordingSession } from "../app/recording.ts";

/** Handles a `start` request from the CLI. */
export function handleStart(): RecordingSession {
  return startRecording();
}

/** Handles a `stop` request from the CLI. */
export function handleStop(): RecordingSession | null {
  return finalizeRecording();
}
