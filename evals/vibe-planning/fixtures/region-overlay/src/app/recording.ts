export type RecordingSession = {
  id: number;
  finalized: boolean;
};

let nextId = 1;
let session: RecordingSession | null = null;

/** Starts a recording session, or returns the current one when a session is already recording. */
export function startRecording(): RecordingSession {
  if (session === null) {
    session = { id: nextId, finalized: false };
    nextId += 1;
  }
  return session;
}

/** Marks the current session finalized and clears it. */
export function finalizeRecording(): RecordingSession | null {
  const finished = session;
  if (finished !== null) {
    finished.finalized = true;
    session = null;
  }
  return finished;
}

/** Returns the session that is recording, or null. */
export function currentSession(): RecordingSession | null {
  return session;
}
