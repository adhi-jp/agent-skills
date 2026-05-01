type NotificationPreferences = {
  emailEnabled: boolean;
};

type PreferencesProps = {
  value: NotificationPreferences;
  onChange: (next: NotificationPreferences) => void;
};

export function Preferences({ value, onChange }: PreferencesProps) {
  return (
    <fieldset>
      <legend>Notifications</legend>
      <label>
        <input
          type="checkbox"
          checked={value.emailEnabled}
          onChange={(event) => onChange({ emailEnabled: event.target.checked })}
        />
        Email reminders
      </label>
    </fieldset>
  );
}
