import { useState } from "react";

type Profile = {
  email: string;
  displayName: string | null;
};

type ProfileFormProps = {
  profile: Profile;
  onSave: (next: { displayName: string }) => Promise<void>;
};

export function ProfileForm({ profile, onSave }: ProfileFormProps) {
  const initialDisplayName = profile.displayName ?? "";
  const [displayName, setDisplayName] = useState(initialDisplayName);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    await onSave({ displayName });
    setSaving(false);
  }

  function handleCancel() {
    setDisplayName(initialDisplayName);
    setError(null);
  }

  return (
    <form onSubmit={handleSubmit}>
      <label htmlFor="display-name">Display name</label>
      <input
        id="display-name"
        value={displayName}
        onChange={(event) => setDisplayName(event.target.value)}
      />
      {error ? <p role="alert">{error}</p> : null}
      <button type="button" onClick={handleCancel}>
        Cancel
      </button>
      <button type="submit" disabled={saving}>
        {saving ? "Saving..." : "Save"}
      </button>
    </form>
  );
}
