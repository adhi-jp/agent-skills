# Export Retention Requirements

## Requirements

- Generated CSV exports are deleted 30 days after creation.
- Exports newer than 30 days are never deleted.

## Acceptance Criteria

- A daily run deletes every export file older than 30 days.
- An export created within the last 30 days survives the run.
