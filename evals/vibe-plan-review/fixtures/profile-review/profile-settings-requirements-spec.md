# Profile Settings Requirements Spec

## Goal

Let signed-in users update their public profile display name and bio from the
existing account settings screen.

## Requirements

- Display name is required, trimmed before save, and limited to 1-60
  characters after trimming.
- Bio is optional and limited to 160 characters.
- Save through the current profile settings endpoint and show validation errors
  inline.
- Cancel restores the previously saved values without sending a network
  request.
- Existing email settings and avatar upload behavior stay unchanged.

## Acceptance Criteria

- A valid display name and bio can be saved and remain visible after reload.
- Empty display names and display names over 60 characters are rejected before
  submit.
- Bios over 160 characters are rejected before submit.
- Cancel restores the previously saved values.
- No avatar upload, username, email-setting, or account-deletion behavior
  changes in this slice.

## Out Of Scope

- Avatar upload.
- Username changes.
- Email preferences.
- Account deletion.
- Audit log surfaces.
